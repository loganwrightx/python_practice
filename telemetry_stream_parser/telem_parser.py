"""
Author: Logan Wright
Date: 10/03/2026
Description: Considering a problem where telemtry is being stream (similar to NMEA strings) and is prone to accumulating errors,
this program safely parses and displays telemetry readouts and throws out corrupted packets. This program uses a UDP client
to receive the telemtry stream. Packets start with $TX and end with RX$. Values between the start/end strings must be numeric or
commas/periods only. If there is a space or letter in the stream, that is an indicator of corruption. Also, if another $TX is
received before finishing the previous packet, then the previous packet is discarded.
"""

"""
Package imports and reasoning:
- Need socket for UDP client - do NOT need struct because endianness does not affect byte-order on single-byte char in the stream
- Include argparse to let user select port for client
- Threading to task parsing on background thread to leave main thread for TUI dashboard
- Queue for inter-thread communication
- Rich thrid-party library to build a nice TUI dashboard
"""

import argparse
import queue
import socket
import threading

from rich.live import Live
from rich.table import Table

ALLOWED_CHARS = set(
    (
        '-',
        '0',
        '1',
        '2',
        '3',
        '4',
        '5',
        '6',
        '7',
        '8',
        '9',
        ',',
        '.'
    )
)

class Telemetry:
    def __init__(
        self,
        lat: float | None = None,
        lon: float | None = None,
        alt: float | None = None,
        hdg: float | None = None,
        speed: float | None = None,
        attitude: tuple[float, float, float, float] | None = None
    ):
        self._lat: float | None = lat
        self._lon: float | None = lon
        self._alt: float | None = alt
        self._hdg: float | None = hdg
        self._speed: float | None = speed
        self._attitude: tuple[float, float, float, float] | None = attitude
    
    @property
    def lat(self) -> float | None:
        return self._lat
    
    @property
    def lon(self) -> float | None:
        return self._lon
        
    @property
    def alt(self) -> float | None:
        return self._alt
    
    @property
    def hdg(self) -> float | None:
        return self._hdg
    
    @property
    def speed(self) -> float | None:
        return self._speed
    
    @property
    def attitude(self) -> tuple[float, float, float, float] | None:
        return self._attitude
    
    def __repr__(self) -> str:
        return f"{self.lat}, {self.lon}, {self.alt}"

def handle_payload(stream: bytes, telemetry_queue: queue.Queue) -> None:
    # Convert byte stream to string stream
    string_stream = stream.decode()
    
    # Helper variables for parsing
    payload: str = ""
    last_char: str = ''
    in_payload: bool = False
    
    # Iterate over each char in stream
    for char in string_stream:
        # Detect full start of packet
        if char == "$" and not in_payload or last_char == "$" and char == "T":
            pass
        elif last_char == "T" and char == "X":
            # After confirming new packet, start empty string to store payload contents
            payload = ""
            in_payload = True
        elif in_payload and char in ALLOWED_CHARS:
            payload += char
        elif in_payload:
            if char == "R" or last_char == "R" and char == "X":
                pass
            elif last_char == "X" and char == "$":
                # Full packet has been received, so make the Telemetry object finally
                lat, lon, alt, hdg, speed, qw, qx, qy, qz = payload.split(',')
                # Package attitude first
                attitude: tuple[float, float, float, float] | None = None if not (qw or qx or qy or qz) else (float(qw), float(qx), float(qy), float(qz))
                # Make the telemetry packet
                telemetry = Telemetry(
                    lat = None if not lat else float(lat),
                    lon = None if not lon else float(lon),
                    alt = None if not alt else float(alt),
                    hdg = None if not hdg else float(hdg),
                    speed = None if not speed else float(speed),
                    attitude = attitude
                )
                # Add telemetry object to the queue
                telemetry_queue.put_nowait(
                    telemetry
                )
                in_payload = False
        
        # Always save last char for next iteration
        last_char = char
    
    # Finally, make telemetry objects from payloads array

def udp_client(client_socket: socket.socket, telemetry_queue: queue.Queue) -> None:
    while True:
        try:
            # Try to capture payload from the socket
            stream = client_socket.recv(1024)
            # Give stream and queue to the handler
            handle_payload(stream, telemetry_queue)
        except Exception:
            # Handle error by ignoring for now
            pass

def telemetry_table(telemetry: Telemetry) -> Table:
    table = Table(title="Telemetry Readout Table")
    
    # Add columns for data
    table.add_column(
        "Latitude",
        justify="center"
    )
    table.add_column(
        "Longitude",
        justify="center"
    )
    table.add_column(
        "Altitude",
        justify="center"
    )
    table.add_column(
        "Heading",
        justify="center"
    )
    table.add_column(
        "Speed",
        justify="center"
    )
    table.add_column(
        "Attitude",
        justify="center"
    )
    
    # Unpack attitude quaternion elements
    qw, qx, qy, qz = (1.0, 0.0, 0.0, 0.0) if not telemetry.attitude else telemetry.attitude
    
    # Then fill in the telemetry data beneath the column headers
    table.add_row(
        f"{telemetry.lat}",
        f"{telemetry.lon}",
        f"{telemetry.alt}",
        f"{telemetry.hdg}",
        f"{telemetry.speed}",
        f"{qw}, {qx}, {qy}, {qz}"
    )
    
    return table

def main():
    parser = argparse.ArgumentParser(
        description="UDP telemetry receiver TUI"
    )
    
    # Let user indicate port and ip address of server
    parser.add_argument(
        "--ip-addr",
        type=str,
        required=True
    )
    parser.add_argument(
        "--port",
        type=int,
        required=True
    )
    
    args = parser.parse_args()
    
    # Create the client socket
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Make ip address usable even if it's in use by a multicast group
    client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Then bind the socket to the specified ip and port
    client_sock.bind((args.ip_addr, args.port))
    
    # Create the telemetry object that will be updated in the loop using the client queue
    latest_telemetry: Telemetry = Telemetry()
    
    # And create the telemetry queue that will be shared between threads
    telemetry_queue = queue.Queue(maxsize=1)
    
    # Create a receiver thread
    client_thread = threading.Thread(target=udp_client, args=(client_sock, telemetry_queue))
    
    # Start the thread
    client_thread.start()
    
    # Run the TUI while the receiver thread is alive
    with Live(telemetry_table(latest_telemetry), refresh_per_second=4) as live:
        while True:
            # Update the latest telemetry packet is a new one is available
            if not telemetry_queue.empty():
                # Grab the new entry
                new_telemetry = telemetry_queue.get()

                # Synthesize the telemetry packets accepting only valid new data
                latest_telemetry = Telemetry(
                    lat = new_telemetry.lat if new_telemetry.lat else latest_telemetry.lat,
                    lon = new_telemetry.lon if new_telemetry.lon else latest_telemetry.lon,
                    alt = new_telemetry.alt if new_telemetry.alt else latest_telemetry.alt,
                    hdg = new_telemetry.hdg if new_telemetry.hdg else latest_telemetry.hdg,
                    speed = new_telemetry.speed if new_telemetry.speed else latest_telemetry.speed,
                    attitude = new_telemetry.attitude if new_telemetry.attitude else latest_telemetry.attitude
                )

            # Then update the table
            live.update(
                telemetry_table(latest_telemetry)
            )

if __name__ == '__main__':
    main()

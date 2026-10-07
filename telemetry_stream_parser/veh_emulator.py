
"""
Author: Logan Wright
Date: 10/03/2026
Description: Emulator script to send noisy telemetry packets over UDP to the telem_parser.py script for testing.
"""

import argparse
import random
import socket
import time


def build_telem_packet(loss_rate: float) -> str:
    lat = random.normalvariate(35.123456) if random.uniform(0.0, 1.0) > loss_rate else None
    lon = random.normalvariate(-120.123456) if random.uniform(0.0, 1.0) > loss_rate else None
    alt = random.normalvariate(300.123456) if random.uniform(0.0, 1.0) > loss_rate else None
    hdg = random.normalvariate(279.123456) if random.uniform(0.0, 1.0) > loss_rate else None
    speed = random.normalvariate(123_456.123) if random.uniform(0.0, 1.0) > loss_rate else None
    attitude = [random.normalvariate(1.0), random.normalvariate(), random.normalvariate(), random.normalvariate()] if random.uniform(0.0, 1.0) > loss_rate else [None, None, None, None]
    data = [lat, lon, alt, hdg, speed] + attitude
    data = [str(element) for element in data]
    return ",".join(data)

def wrap_packet(packet: str, error_rate: float) -> str:
    if random.uniform(0.0, 1.0) > error_rate:
        return "$TX" + packet
    else:
        return "$TX" + packet + "RX$"

def main():
    parser = argparse.ArgumentParser(
        description="Vehicle Telemetry Emulator"
    )
    
    # Add CLI args for ip addr and port
    parser.add_argument(
        "--dest-ip-addr",
        type=str,
        required=True
    )
    parser.add_argument(
        "--dest-port",
        type=int,
        required=True
    )
    # Add CLI arg for data transmission frequency
    parser.add_argument(
        "--frequency",
        type=int,
        required=True
    )
    # And set average packet loss/corruption rate
    parser.add_argument(
        "--loss-rate",
        type=float,
        required=True
    )
    
    args = parser.parse_args()
    
    # Build server socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Configure socket for proper use of ipv4
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    while True:
        # Create fake packet data
        telem = build_telem_packet(args.loss_rate)
        # Add packet padding to the payload
        telem = wrap_packet(telem, 0.25)
        # And finally, send the payload out to the destination (client)
        server_sock.sendto(
            telem.encode(),
            (args.dest_ip_addr, args.dest_port)
        )
        print(f"Sent {len(telem.encode())} bytes to ({args.dest_ip_addr}:{args.dest_port})")
        # Set frequency to what is specified
        time.sleep(1 / args.frequency)

if __name__ == '__main__':
    main()

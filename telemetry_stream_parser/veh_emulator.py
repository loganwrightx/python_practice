"""
Author: Logan Wright
Date: 10/03/2026
Description: Emulator script to send noisy telemetry packets over UDP to the telem_parser.py script for testing.
"""

import argparse
import socket
import random
import time

def build_telem_packet() -> str:
    lat = random.normalvariate(35.123456)
    lon = random.normalvariate(-120.123456)
    alt = random.normalvariate(300.123456)
    hdg = random.normalvariate(279.123456)
    speed = random.normalvariate(123_456.123)
    attitude = (1.0, 0.0, 0.0, 0.0)
    return f"{lat},{lon},{alt},{hdg},{speed},{attitude[0]},{attitude[1]},{attitude[2]},{attitude[3]}"

def wrap_packet(packet: str) -> str:
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
        "--port",
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
        telem = build_telem_packet()
        # Add packet padding to the payload
        telem = wrap_packet(telem)
        # And finally, send the payload out to the destination (client)
        server_sock.sendto(
            telem.encode(),
            (args.dest_ip_addr, args.port)
        )
        print(f"Sent {len(telem.encode())} bytes to ({args.dest_ip_addr}:{args.port})")
        # Set frequency to what is specified
        time.sleep(1 / args.frequency)

if __name__ == '__main__':
    main()
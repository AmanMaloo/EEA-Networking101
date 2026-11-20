"""ICMP Pinger.  Usage: python3 icmp_pinger.py [host] [count]

Uses a raw socket when allowed (sudo); otherwise falls back to an unprivileged
ICMP datagram socket, which macOS and many Linux setups permit without root.
"""
import os
import select
import socket
import struct
import sys
import time

ICMP_ECHO_REQUEST = 8


def checksum(data):
    """Internet checksum (RFC 1071): one's-complement sum of 16-bit big-endian words."""
    total = 0
    for i in range(0, len(data) - 1, 2):
        total += (data[i] << 8) + data[i + 1]
    if len(data) % 2:
        total += data[-1] << 8
    total = (total >> 16) + (total & 0xFFFF)
    total += total >> 16
    return ~total & 0xFFFF


def make_socket():
    proto = socket.getprotobyname("icmp")
    try:
        return socket.socket(socket.AF_INET, socket.SOCK_RAW, proto), "raw"
    except PermissionError:
        return socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto), "datagram"


def send_one_ping(sock, dest, ident, seq):
    header = struct.pack("!BBHHH", ICMP_ECHO_REQUEST, 0, 0, ident, seq)
    data = struct.pack("!d", time.time())
    csum = checksum(header + data)
    header = struct.pack("!BBHHH", ICMP_ECHO_REQUEST, 0, csum, ident, seq)
    sock.sendto(header + data, (dest, 1))


def receive_one_ping(sock, ident, seq, timeout):
    deadline = time.time() + timeout
    while True:
        left = deadline - time.time()
        if left <= 0:
            return None
        ready, _, _ = select.select([sock], [], [], left)
        if not ready:
            return None
        received_at = time.time()
        packet, addr = sock.recvfrom(1024)
        ip_header_len = (packet[0] & 0x0F) * 4          # replies include the IP header
        ttl = packet[8]
        icmp = packet[ip_header_len:]
        icmp_type, code, _, pkt_id, pkt_seq = struct.unpack("!BBHHH", icmp[:8])
        if icmp_type == 0 and pkt_seq == seq:            # 0 = echo reply
            # raw sockets echo our id back; datagram sockets let the kernel pick it
            sent_at = struct.unpack("!d", icmp[8:16])[0]
            return (received_at - sent_at) * 1000, ttl, len(icmp), addr[0]


def ping(host, count=4, timeout=1):
    dest = socket.gethostbyname(host)
    sock, mode = make_socket()
    ident = os.getpid() & 0xFFFF
    print(f"Pinging {host} [{dest}] using Python ({mode} socket):\n")
    times = []
    for seq in range(1, count + 1):
        send_one_ping(sock, dest, ident, seq)
        result = receive_one_ping(sock, ident, seq, timeout)
        if result is None:
            print("Request timed out.")
        else:
            ms, ttl, size, src = result
            times.append(ms)
            print(f"Reply from {src}: bytes={size} time={ms:.2f}ms TTL={ttl}")
        time.sleep(1)
    sock.close()
    lost = count - len(times)
    print(f"\n--- {host} ping statistics ---")
    print(f"{count} sent, {len(times)} received, {lost / count:.0%} loss")
    if times:
        print(f"rtt min/avg/max = {min(times):.2f}/{sum(times)/len(times):.2f}/{max(times):.2f} ms")


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    try:
        ping(host, count)
    except KeyboardInterrupt:
        print("\nStopped.")

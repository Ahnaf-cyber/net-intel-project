import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor
from clickhouse_driver import Client

ch = Client(host='localhost', user='default', password='')

TARGET = "45.33.32.156"   # scanme.nmap.org (authorized test target)
PORTS = [22, 80, 443]
PROTOCOLS = {22: "ssh", 80: "http", 443: "tls"}


def check_port(target, port, timeout=3):
    try:
        with socket.create_connection((target, port), timeout=timeout):
            return port
    except OSError:
        return None


def scan_ports(target, ports):
    with ThreadPoolExecutor(max_workers=20) as ex:
        results = list(ex.map(lambda p: check_port(target, p), ports))
    return sorted(p for p in results if p)


def run_zgrab(target, port):
    protocol = PROTOCOLS.get(port)
    if not protocol:
        return None, None
    try:
        result = subprocess.run(["zgrab2", protocol, "-p", str(port)],
                                input=target, capture_output=True,
                                text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return None, protocol
    for line in result.stdout.splitlines():
        if line.startswith('{"ip"'):
            return line, protocol
    return None, protocol


def main():
    print(f"Scanning {TARGET} on ports {PORTS}...")
    open_ports = scan_ports(TARGET, PORTS)
    print(f"Open ports found: {open_ports}")

    rows = []
    for port in open_ports:
        banner_json, protocol = run_zgrab(TARGET, port)
        if banner_json:
            rows.append((TARGET, port, protocol, banner_json))
            print(f"  Port {port} ({protocol}): banner captured")

    if rows:
        ch.execute(
            'INSERT INTO scan_results (ip, port, protocol, banner) VALUES',
            rows
        )
        print(f"Saved {len(rows)} results to ClickHouse")


if __name__ == "__main__":
    main()

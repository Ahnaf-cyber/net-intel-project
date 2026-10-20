import sys
import socket
import subprocess
import random
from concurrent.futures import ThreadPoolExecutor
import redis
import maxminddb
from clickhouse_driver import Client

STREAM = "ip_jobs"
GROUP = "ip_workers"
PORTS = [22, 80, 443, 6379, 8123, 9000]
PROTOCOLS = {22: "ssh", 80: "http", 443: "tls"}

ch = Client(host='localhost', user='default', password='')
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
geo = maxminddb.open_database('dbip.mmdb')
NAME = "ipworker-" + str(random.randint(1000, 9999))


def lookup_country(ip):
    info = geo.get(ip)
    if info:
        return info.get('country', {}).get('iso_code', '') or ''
    return ''


def check_port(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=3):
            return port
    except OSError:
        return None


def get_banner(ip, port):
    protocol = PROTOCOLS.get(port)
    if not protocol:
        return "unknown", ""
    try:
        res = subprocess.run(["zgrab2", protocol, "-p", str(port)],
                             input=ip, capture_output=True,
                             text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return protocol, ""
    for line in res.stdout.splitlines():
        if line.startswith('{"ip"'):
            return protocol, line
    return protocol, ""


def scan_ip(ip):
    with ThreadPoolExecutor(max_workers=20) as ex:
        found = [p for p in ex.map(lambda p: check_port(ip, p), PORTS) if p]
    country = lookup_country(ip)
    rows = []
    for port in sorted(found):
        protocol, banner = get_banner(ip, port)
        rows.append((ip, port, protocol, banner, country))
    if rows:
        ch.execute('INSERT INTO scan_results (ip, port, protocol, banner, country) VALUES', rows)
    return [row[1] for row in rows]


def enqueue():
    with open("targets.txt") as f:
        ips = [line.strip() for line in f if line.strip()]
    for ip in ips:
        r.xadd(STREAM, {"ip": ip})
    print(f"Enqueued {len(ips)} IPs")


def work():
    try:
        r.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
    except redis.exceptions.ResponseError:
        pass
    print(f"Worker {NAME} started", flush=True)
    while True:
        resp = r.xreadgroup(GROUP, NAME, {STREAM: ">"}, count=1, block=5000)
        if not resp:
            continue
        for _, messages in resp:
            for msg_id, fields in messages:
                ip = fields["ip"]
                ports = scan_ip(ip)
                print(f"[{NAME}] {ip} -> open ports {ports}", flush=True)
                r.xack(STREAM, GROUP, msg_id)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "enqueue":
        enqueue()
    else:
        work()

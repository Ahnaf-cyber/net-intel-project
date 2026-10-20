import json
from fastapi import FastAPI
from fastapi.responses import FileResponse
from clickhouse_driver import Client

app = FastAPI()
import threading
_local = threading.local()


class _PerThreadCH:
    def execute(self, *args, **kwargs):
        if not hasattr(_local, "c"):
            _local.c = Client(host='localhost', user='default', password='')
        return _local.c.execute(*args, **kwargs)


ch = _PerThreadCH()


def software_from_banner(protocol, banner):
    if not banner:
        return ""
    try:
        data = json.loads(banner)
        if protocol == "http":
            headers = data["data"]["http"]["result"]["response"]["headers"]
            servers = headers.get("server", [])
            return servers[0] if servers else ""
        if protocol == "ssh":
            sid = data["data"]["ssh"]["result"]["server_id"]
            return (sid.get("software", "") + " " + sid.get("comment", "")).strip()
    except (json.JSONDecodeError, KeyError, TypeError):
        return ""
    return ""


def scan_rows(rows):
    return [{"ip": r[0], "port": r[1], "protocol": r[2],
             "software": software_from_banner(r[2], r[5]),
             "country": r[3], "seen": str(r[4])} for r in rows]


@app.get("/")
def home():
    return FileResponse("index.html")


@app.get("/ip/{ip}")
def ip_info(ip: str):
    rows = ch.execute(
        "SELECT ip, port, protocol, country, observed_at, banner FROM scan_results "
        "WHERE ip = %(ip)s ORDER BY observed_at DESC LIMIT 50",
        {"ip": ip})
    return scan_rows(rows)


@app.get("/country/{code}")
def by_country(code: str):
    rows = ch.execute(
        "SELECT ip, port, protocol, country, observed_at, banner FROM scan_results "
        "WHERE country = %(c)s ORDER BY observed_at DESC LIMIT 50",
        {"c": code.upper()})
    return scan_rows(rows)


@app.get("/domain/{name}")
def domain_info(name: str):
    rows = ch.execute(
        "SELECT subdomain, ip, observed_at FROM subdomains "
        "WHERE domain = %(d)s ORDER BY observed_at DESC LIMIT 100",
        {"d": name})
    return [{"subdomain": r[0], "ip": r[1], "seen": str(r[2])} for r in rows]


@app.get("/geo/{code}")
def by_geo(code: str):
    rows = ch.execute(
        "SELECT s.subdomain, s.ip, g.country, s.observed_at "
        "FROM subdomains AS s INNER JOIN ip_geo AS g ON s.ip = g.ip "
        "WHERE g.country = %(c)s ORDER BY s.observed_at DESC LIMIT 100",
        {"c": code.upper()})
    return [{"subdomain": r[0], "ip": r[1], "country": r[2], "seen": str(r[3])} for r in rows]


@app.get("/stats")
def stats():
    total = ch.execute("SELECT count() FROM domains")[0][0]
    scanned = ch.execute("SELECT uniqExact(domain) FROM scan_log")[0][0]
    subs = ch.execute("SELECT uniqExact(subdomain) FROM subdomains")[0][0]
    ips = ch.execute("SELECT uniqExact(ip) FROM scan_results")[0][0]
    countries = ch.execute("SELECT uniqExact(country) FROM ip_geo WHERE country != ''")[0][0]
    ago = None
    if ch.execute("SELECT count() FROM scan_log")[0][0]:
        ago = ch.execute("SELECT dateDiff('second', max(at), now()) FROM scan_log")[0][0]
    recent = ch.execute("SELECT at, domain, status, found FROM scan_log ORDER BY at DESC LIMIT 8")
    return {"domains_total": total, "domains_scanned": scanned, "subdomains": subs,
            "ips": ips, "countries": countries, "ago_seconds": ago,
            "recent": [{"at": str(r[0]), "domain": r[1], "status": r[2], "found": r[3]} for r in recent]}


@app.get("/iphosts/{ip}")
def ip_hosts(ip: str):
    geo = ch.execute("SELECT country FROM ip_geo WHERE ip = %(ip)s LIMIT 1", {"ip": ip})
    country = geo[0][0] if geo else ""
    rows = ch.execute(
        "SELECT subdomain, max(observed_at) AS last_seen FROM subdomains "
        "WHERE ip = %(ip)s GROUP BY subdomain ORDER BY last_seen DESC LIMIT 100",
        {"ip": ip})
    return [{"subdomain": r[0], "country": country, "seen": str(r[1])} for r in rows]

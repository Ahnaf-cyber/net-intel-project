import maxminddb
from clickhouse_driver import Client

ch = Client(host='localhost', user='default', password='')
geo = maxminddb.open_database('dbip.mmdb')

known = {r[0] for r in ch.execute("SELECT ip FROM ip_geo")}
ips = [r[0] for r in ch.execute("SELECT DISTINCT ip FROM subdomains")]

rows = []
for ip in ips:
    if ip in known:
        continue
    country = ""
    try:
        info = geo.get(ip)
        if info:
            country = info.get("country", {}).get("iso_code", "") or ""
    except ValueError:
        pass
    rows.append((ip, country))

if rows:
    ch.execute("INSERT INTO ip_geo (ip, country) VALUES", rows)
print(len(rows), "new IPs added")
print(ch.execute("SELECT country, count() AS n FROM ip_geo GROUP BY country ORDER BY n DESC LIMIT 15"))

# Net Intel

Subdomain discovery (Project 2) and host scanning (Project 1) with a search page. A small-scale working version, built on one Kali VM in VirtualBox. See the report for results and limits.

## Parts

- docker-compose.yml: ClickHouse (database). Redis was started separately: docker run -d --name net-intel-redis --restart unless-stopped -p 6379:6379 -v redis_data:/data redis:7-alpine redis-server --appendonly yes
- ingest_csv.py: loads top-1m.csv into the domains table.
- schema.py: creates scan_state, subdomains and scan_log.
- producer.py: puts the domains scanned longest ago into the Redis queue.
- worker.py: wildcard check, then looks up the 52 names in wordlist.txt, saves what it finds.
- resolvers.py: tests DNS servers. config.py holds the settings, including the resolvers.
- ip_scan_worker.py: Project 1. TCP port checks, zgrab2 banners, country lookup. targets.txt lists hosts we have permission to scan.
- backfill_geo.py: fills the IP-to-country table. api.py and index.html: web API and search page. metrics.py: progress numbers.
- Early tests kept for reference: test_connection.py, wildcard_check.py, subdomain_finder.py, batch_scan.py, scan_target.py, masscan_test.py.

## Run

1. docker compose up -d, then start Redis with the command above.
2. python3 ingest_csv.py, then python3 schema.py.
3. python3 producer.py and one or more python3 worker.py.
4. uvicorn api:app --host 127.0.0.1 --port 8000, then open http://127.0.0.1:8000

## Not included

- top-1m.csv (domain list) and dbip.mmdb (DB-IP Lite City database from https://db-ip.com, CC BY 4.0).
- zgrab2: go install github.com/zmap/zgrab2/cmd/zgrab2@latest
- Python packages: dnspython clickhouse-driver redis maxminddb fastapi uvicorn
- Tables domains, scan_results and ip_geo were created by hand. Their columns are in the code that writes to them.

## Notes

- ClickHouse runs with the default user and no password. For an isolated test VM only.
- Only scan hosts you have written permission to scan. We port-checked only scanme.nmap.org and our own VM.

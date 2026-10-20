from clickhouse_driver import Client
from config import CH_HOST

c = Client(host=CH_HOST, user="default", password="")

c.execute("""
CREATE TABLE IF NOT EXISTS scan_state (
    domain String,
    last_scanned DateTime,
    status LowCardinality(String)
) ENGINE = ReplacingMergeTree(last_scanned) ORDER BY domain
""")

c.execute("""
CREATE TABLE IF NOT EXISTS subdomains (
    domain String,
    subdomain String,
    ip String,
    observed_at DateTime DEFAULT now()
) ENGINE = MergeTree() ORDER BY (domain, subdomain, observed_at)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS scan_log (
    domain String,
    status LowCardinality(String),
    found UInt32,
    seconds Float32,
    worker String,
    at DateTime DEFAULT now()
) ENGINE = MergeTree() ORDER BY at
""")

print("OK: scan_state, subdomains, scan_log ready")

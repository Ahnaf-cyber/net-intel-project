from clickhouse_driver import Client
import redis
import config

ch = Client(host=config.CH_HOST, user="default", password="")
r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)

total_domains = ch.execute("SELECT count() FROM domains")[0][0]
scanned = ch.execute("SELECT count(DISTINCT domain) FROM scan_state")[0][0]
total_subdomains = ch.execute("SELECT count() FROM subdomains")[0][0]
queue_len = r.xlen(config.STREAM)

recent = ch.execute("""
    SELECT count() FROM scan_log WHERE at > now() - INTERVAL 10 MINUTE
""")[0][0]

print(f"Total domains in DB:      {total_domains}")
print(f"Domains scanned so far:   {scanned}")
print(f"Total subdomains found:   {total_subdomains}")
print(f"Jobs waiting in queue:    {queue_len}")
print(f"Scanned in last 10 min:   {recent}")

from clickhouse_driver import Client
import redis
import config
import time

ch = Client(host=config.CH_HOST, user="default", password="")
r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)

def get_next_domains(limit):
    rows = ch.execute(f"""
        SELECT d.domain
        FROM domains d
        LEFT JOIN scan_state s ON d.domain = s.domain
        WHERE s.last_scanned IS NULL OR s.last_scanned = toDateTime(0)
           OR s.last_scanned < now() - INTERVAL {config.RESCAN_INTERVAL_HOURS} HOUR
        ORDER BY coalesce(s.last_scanned, toDateTime(0)) ASC
        LIMIT {limit}
    """)
    return [row[0] for row in rows]

def main():
    print("Producer started. Press Ctrl+C to stop.")
    while True:
        qlen = r.xlen(config.STREAM)
        if qlen >= config.QUEUE_MAX:
            print(f"Queue full ({qlen}/{config.QUEUE_MAX}), waiting...")
            time.sleep(5)
            continue

        need = config.QUEUE_MAX - qlen
        domains = get_next_domains(need)

        if not domains:
            print("No domains found at all. Check your `domains` table.")
            time.sleep(10)
            continue

        for d in domains:
            r.xadd(config.STREAM, {"domain": d})

        print(f"Added {len(domains)} domains to queue (queue size now ~{qlen + len(domains)})")
        time.sleep(2)

if __name__ == "__main__":
    main()

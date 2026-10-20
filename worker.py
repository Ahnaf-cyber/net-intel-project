from clickhouse_driver import Client
import redis
import config
import dns.resolver
import random
import string
import time
import socket
from concurrent.futures import ThreadPoolExecutor

ch = Client(host=config.CH_HOST, user="default", password="")
r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)

WORKER_NAME = socket.gethostname() + "-" + str(random.randint(1000, 9999))

with open(config.WORDLIST) as f:
    WORDS = [line.strip() for line in f if line.strip()]

GROUP = config.GROUP
_res = dns.resolver.Resolver(configure=False)
_res.nameservers = config.RESOLVERS
_res.rotate = True
_res.timeout = config.DNS_TIMEOUT
_res.lifetime = config.DNS_TIMEOUT
STREAM = config.STREAM

try:
    r.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
except redis.exceptions.ResponseError:
    pass  # গ্রুপ আগে থেকেই থাকলে এই error আসবে, সমস্যা না


def has_wildcard_dns(domain, max_retries=3):
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
    fake_subdomain = f"{random_part}.{domain}"
    for attempt in range(1, max_retries + 1):
        try:
            answer = _res.resolve(fake_subdomain, 'A')
            return True
        except dns.resolver.NXDOMAIN:
            return False
        except dns.resolver.NoAnswer:
            return True
        except (dns.resolver.NoNameservers, dns.exception.Timeout):
            if attempt < max_retries:
                time.sleep(1)
                continue
            return None
        except Exception:
            return None
    return None


def scan_domain(domain):
    start = time.time()
    wildcard = has_wildcard_dns(domain)

    if wildcard is True:
        status = "wildcard_skipped"
        found = []
    elif wildcard is None:
        status = "wildcard_unknown"
        found = []
    else:
        status = "scanned"
        def lookup(word):
            sub = f"{word}.{domain}"
            for attempt in range(3):
                try:
                    return (domain, sub, _res.resolve(sub, 'A')[0].to_text())
                except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                    return None
                except Exception:
                    time.sleep(0.5)
            return None
        with ThreadPoolExecutor(max_workers=config.THREADS) as ex:
            found = [r for r in ex.map(lookup, WORDS) if r]

    elapsed = time.time() - start

    if found:
        ch.execute('INSERT INTO subdomains (domain, subdomain, ip) VALUES', found)

    ch.execute(
        'INSERT INTO scan_state (domain, last_scanned, status) VALUES',
        [(domain, time_now(), status)]
    )
    ch.execute(
        'INSERT INTO scan_log (domain, status, found, seconds, worker) VALUES',
        [(domain, status, len(found), elapsed, WORKER_NAME)]
    )
    return status, len(found)


def time_now():
    from datetime import datetime
    return datetime.utcnow()


def main():
    print(f"Worker {WORKER_NAME} started. Press Ctrl+C to stop.")
    while True:
        try:
            resp = r.xreadgroup(GROUP, WORKER_NAME, {STREAM: ">"}, count=1, block=5000)
        except (redis.exceptions.TimeoutError, redis.exceptions.ConnectionError):
            time.sleep(1)
            continue
        if not resp:
            continue

        for stream_name, messages in resp:
            for msg_id, fields in messages:
                domain = fields["domain"]
                recent = ch.execute("SELECT count() FROM scan_state WHERE domain = %(d)s AND last_scanned > now() - INTERVAL %(h)s HOUR", {"d": domain, "h": config.RESCAN_INTERVAL_HOURS})[0][0]
                if recent:
                    print(f"[{WORKER_NAME}] {domain} -> skipped (scanned recently)", flush=True)
                else:
                    status, found_count = scan_domain(domain)
                    print(f"[{WORKER_NAME}] {domain} -> {status}, found={found_count}", flush=True)
                r.xack(STREAM, GROUP, msg_id)
                r.xdel(STREAM, msg_id)


if __name__ == "__main__":
    main()

import os

CH_HOST = os.getenv("CH_HOST", "localhost")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

STREAM = "domain_jobs"
GROUP = "scan_workers"

BATCH_SIZE = 50
QUEUE_MAX = 500
RESCAN_INTERVAL_HOURS = 24

THREADS = 20
DNS_TIMEOUT = 3
MAX_RETRIES = 3
GLOBAL_QPS = 200

RESOLVERS = ["1.1.1.1", "1.0.0.1", "8.8.4.4", "149.112.112.112", "208.67.220.220"]
WORDLIST = "wordlist.txt"
CLAIM_IDLE_MS = 60000

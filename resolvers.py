import dns.resolver
import random
import string
import time

CANDIDATES = ["1.1.1.1", "1.0.0.1", "8.8.8.8", "8.8.4.4",
              "9.9.9.9", "149.112.112.112", "208.67.222.222", "208.67.220.220"]


def rand_name():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=20)) + ".com"


def make(ip):
    r = dns.resolver.Resolver(configure=False)
    r.nameservers = [ip]
    r.timeout = 3
    r.lifetime = 3
    return r


def check(ip):
    r = make(ip)
    problems, times = [], []
    t = time.time()
    try:
        answers = [a.to_text() for a in r.resolve("scanme.nmap.org", "A")]
        times.append(time.time() - t)
        if "45.33.32.156" not in answers:
            problems.append("wrong answer for scanme.nmap.org")
    except Exception as e:
        problems.append("known-answer check failed: " + type(e).__name__)
    for _ in range(3):
        name = rand_name()
        t = time.time()
        try:
            r.resolve(name, "A")
            problems.append("hijack: a random name resolved")
        except dns.resolver.NXDOMAIN:
            times.append(time.time() - t)
        except Exception as e:
            problems.append("fake-name check failed: " + type(e).__name__)
    median = sorted(times)[len(times) // 2] if times else None
    if median is not None and median > 1.0:
        problems.append("slow, median %.0f ms" % (median * 1000))
    return problems, median


if __name__ == "__main__":
    default = dns.resolver.Resolver().nameservers
    ips = list(dict.fromkeys(CANDIDATES + default))
    good = []
    for ip in ips:
        problems, median = check(ip)
        tag = " (this VM default)" if ip in default else ""
        if problems:
            print("FAIL", ip + tag, "-", "; ".join(problems))
        else:
            print("OK  ", ip + tag, "- median %.0f ms" % (median * 1000))
            good.append(ip)
    open("good_resolvers.txt", "w").write("\n".join(good) + "\n")
    print(len(good), "of", len(ips), "resolvers passed -> good_resolvers.txt")

import dns.resolver
from wildcard_check import has_wildcard_dns

def find_subdomains(target_domain, wordlist_file):
    # প্রথমে wildcard চেক করি
    print(f"Checking {target_domain} for wildcard DNS...")
    wildcard = has_wildcard_dns(target_domain)

    if wildcard is True:
        print(f"🚫 {target_domain} has wildcard DNS — skipping to avoid false results.\n")
        return []
    elif wildcard is None:
        print(f"⚠️  Could not determine wildcard status for {target_domain} — skipping to be safe.\n")
        return []

    print(f"✅ No wildcard detected. Proceeding with subdomain scan.\n")

    with open(wordlist_file, 'r') as f:
        words = [line.strip() for line in f if line.strip()]

    found = []
    for word in words:
        subdomain = f"{word}.{target_domain}"
        try:
            answer = dns.resolver.resolve(subdomain, 'A')
            ip = answer[0].to_text()
            print(f"✅ FOUND: {subdomain} -> {ip}")
            found.append((subdomain, ip))
        except dns.resolver.NXDOMAIN:
            print(f"❌ Not found: {subdomain}")
        except Exception as e:
            print(f"⚠️  Error checking {subdomain}: {e}")

    return found


if __name__ == "__main__":
    result = find_subdomains("google.com", "wordlist.txt")
    print(f"\nTotal found: {len(result)}")

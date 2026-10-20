from clickhouse_driver import Client
from subdomain_finder import find_subdomains

client = Client(host='localhost', user='default', password='')

# ডাটাবেস থেকে ৫টা ডোমেইন নিই (টেস্টের জন্য ছোট রাখছি)
rows = client.execute('SELECT domain FROM domains LIMIT 5')
domain_list = [row[0] for row in rows]

print(f"Domains to scan: {domain_list}\n")

total_saved = 0

for domain in domain_list:
    print(f"--- Scanning {domain} ---")
    found = find_subdomains(domain, "wordlist.txt")

    # পাওয়া গেলে ডাটাবেসে সেভ করি
    if found:
        data = [(domain, sub, ip) for sub, ip in found]
        client.execute(
            'INSERT INTO subdomains (domain, subdomain, ip) VALUES',
            data
        )
        total_saved += len(data)
        print(f"💾 Saved {len(data)} subdomains for {domain}")
    print()

print("=== SUMMARY ===")
print(f"Total subdomains saved this run: {total_saved}")

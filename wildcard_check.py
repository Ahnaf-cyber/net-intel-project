import dns.resolver
import random
import string
import time


def has_wildcard_dns(domain, max_retries=3):
    """
    এলোমেলো subdomain দিয়ে wildcard DNS চেক করে।
    নেটওয়ার্ক সমস্যার কারণে ব্যর্থ হলে max_retries বার আবার চেষ্টা করে।
    """
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
    fake_subdomain = f"{random_part}.{domain}"

    for attempt in range(1, max_retries + 1):
        try:
            answer = dns.resolver.resolve(fake_subdomain, 'A')
            ip = answer[0].to_text()
            print(f"⚠️  Wildcard detected on {domain}! Random name resolved to {ip}")
            return True

        except dns.resolver.NXDOMAIN:
            # নামটাই নেই — এটা নিশ্চিত উত্তর, retry দরকার নেই
            print(f"✅ No wildcard on {domain} (NXDOMAIN)")
            return False

        except dns.resolver.NoAnswer:
            print(f"⚠️  {domain}: name exists but no A record (possible wildcard)")
            return True

        except (dns.resolver.NoNameservers, dns.exception.Timeout) as e:
            # এগুলো সাময়িক নেটওয়ার্ক সমস্যা হতে পারে — তাই আবার চেষ্টা করি
            if attempt < max_retries:
                print(f"⏳ Attempt {attempt}/{max_retries} failed for {domain} ({type(e).__name__}), retrying...")
                time.sleep(1)  # একটু অপেক্ষা করে আবার চেষ্টা
                continue
            else:
                print(f"⚠️  Gave up on {domain} after {max_retries} attempts ({type(e).__name__})")
                return None

        except Exception as e:
            print(f"⚠️  Unexpected error checking wildcard for {domain}: {e}")
            return None

    return None


if __name__ == "__main__":
    test_domains = ["google.com", "github.com"]
    for d in test_domains:
        has_wildcard_dns(d)

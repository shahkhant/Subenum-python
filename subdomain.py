import dns.resolver
import requests
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

resolver = dns.resolver.Resolver()
resolver.lifetime = 2

def check_http(subdomain):
    urls = [f"http://{subdomain}", f"https://{subdomain}"]
    for url in urls:
        try:
            r = requests.get(url, timeout=3, allow_redirects=True)
            return url, r.status_code
        except requests.RequestException:
            pass
    return None, None

def resolve_subdomain(sub, domain, probe_http):
    full = f"{sub}.{domain}"
    try:
        answers = resolver.resolve(full, "A")
        ips = [a.to_text() for a in answers]

        result = {
            "subdomain": full,
            "ips": ips,
            "http": None
        }

        if probe_http:
            url, status = check_http(full)
            if url:
                result["http"] = f"{url} [{status}]"

        return result

    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
        return None


def main(domain, wordlist, threads, probe_http):
    with open(wordlist, "r") as f:
        subs = [line.strip() for line in f if line.strip()]

    print(f"\n[*] Enumerating {len(subs)} subdomains for {domain}\n")

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [
            executor.submit(resolve_subdomain, sub, domain, probe_http)
            for sub in subs
        ]

        for future in as_completed(futures):
            result = future.result()
            if result:
                line = f"[+] {result['subdomain']} -> {', '.join(result['ips'])}"
                if result["http"]:
                    line += f" | LIVE: {result['http']}"
                print(line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Advanced Subdomain Enumerator")
    parser.add_argument("-d", "--domain", required=True, help="Target domain")
    parser.add_argument("-w", "--wordlist", required=True, help="Subdomain wordlist")
    parser.add_argument("-t", "--threads", type=int, default=30, help="Number of threads")
    parser.add_argument("--http", action="store_true", help="Probe HTTP/HTTPS")

    args = parser.parse_args()

    main(args.domain, args.wordlist, args.threads, args.http)
#!/usr/bin/env python3
"""
dnsnet.py – Fetch DNS records and WHOIS data for a domain.
Warn if the WHOIS response is almost entirely redacted (e.g. Cloudflare / privacy).
"""

import argparse
import sys
import os
from pprint import pprint
import requests
import whois
from colorama import init, Fore
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
init(autoreset=True)
options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--headless") 
options.add_argument("--no-sandbox")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
print(Fore.RED + """
          .                                                      .
        .n                   .                 .                  n.
  .   .dP                  dP                   9b                 9b.    .
 4    qXb         .       dX                     Xb       .        dXp     t
dX.    9Xb      .dXb    __                         __    dXb.     dXP     .Xb
9XXb._       _.dXXXXb dXXXXbo.                 .odXXXXb dXXXXb._       _.dXXP
 9XXXXXXXXXXXXXXXXXXXVXXXXXXXXOo.           .oOXXXXXXXXVXXXXXXXXXXXXXXXXXXXP
  `9XXXXXXXXXXXXXXXXXXXXX'~   ~`OOO8b   d8OOO'~   ~`XXXXXXXXXXXXXXXXXXXXXP'
    `9XXXXXXXXXXXP' `9XX'   DIE    `98v8P'  HUMAN   `XXP' `9XXXXXXXXXXXP'
        ~~~~~~~       9X.          .db|db.          .XP       ~~~~~~~
                        )b.  .dbo.dP'`v'`9b.odb.  .dX(
                      ,dXXXXXXXXXXXb     dXXXXXXXXXXXb.
                     dXXXXXXXXXXXP'   .   `9XXXXXXXXXXXb
                    dXXXXXXXXXXXXb   d|b   dXXXXXXXXXXXXb
                    9XXb'   `XXXXXb.dX|Xb.dXXXXX'   `dXXP
                     `'      9XXXXXX(   )XXXXXXP      `'
                              XXXX X.`v'.X XXXX
                              XP^X'`b   d'`X^XX
                              X. 9  `   '  P )X
                              `b  `       '  d'
""")
print(Fore.YELLOW + "[+] DNS and WHOIS lookup tool")
print(Fore.CYAN + "Author: @dev0Eyad /")
print(Fore.CYAN + "GitHub: https://github.com/dev0Eyad/dnsnet")
print(Fore.MAGENTA + "Usage: python dnsnet.py <domain>")
print(Fore.CYAN + "[+] Searching in DNS ... ")
time.sleep(1)
print(Fore.YELLOW + "[+] Searching in Netcraft ... ")
time.sleep(1)
print(Fore.BLUE + "[+] Searching in DNS via Google DNS-over-HTTPS ... ")
time.sleep(1)
print(Fore.GREEN + "[+] Searching in WHOIS ... ")
time.sleep(1)
# ──────────────────────────────────────────────────────────────────────────────
# DNS via Google DNS-over-HTTPS
# ──────────────────────────────────────────────────────────────────────────────
def get_dns_records(domain: str) -> dict | None:
    url = f"https://dns.google/resolve?name={domain}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        print(f"[DNS] lookup failed: {exc}")
        return None


# ──────────────────────────────────────────────────────────────────────────────
# WHOIS
# ──────────────────────────────────────────────────────────────────────────────
def get_whois(domain: str) -> dict | None:
    try:
        return whois.whois(domain)
    except Exception as exc:
        print(f"[WHOIS] lookup failed: {exc}")
        return None


def whois_mostly_null(w: dict) -> bool:
    """Return True if nearly all important WHOIS fields are missing."""
    keys = (
        "domain_name",
        "registrar",
        "creation_date",
        "expiration_date",
        "name_servers",
        "status",
        "emails",
    )
    nulls = sum(1 for k in keys if not w.get(k))
    return nulls >= len(keys) - 1 

# ──────────────────────────────────────────────────────────────────────────────
# NETCRAFT
# ──────────────────────────────────────────────────────────────────────────────
def get_netcraft(domain: str) -> None:
    url = f"https://sitereport.netcraft.com/?url=http://{domain}"
    with open("free_proxies.csv", "r") as f:
        read = f.readline()
        # print(read)
    try: 
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        driver.implicitly_wait(15)
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(15)

        # Parse page
        soup = BeautifulSoup(driver.page_source, "html.parser")
        multi_table = soup.find("div", class_="table--multi")
        if not multi_table:
            raise Exception("Could not find table--multi on the page.")

        tables = multi_table.find_all("table", class_="table--list")
        results = {}

        for table in tables:
            for row in table.find_all("tr"):
                th = row.find("th")
                td = row.find("td")
                if th and td:
                    key = th.get_text(strip=True)
                    value = td.get_text(strip=True)
                    results[key] = value

        print(Fore.GREEN + f"\n[NETCRAFT] Results for {domain}:")
        for key, value in results.items():
            print(f"{key}: {value}")
        
        driver.quit()
    except Exception as exc:
        print(Fore.RED + f"[NETCRAFT] lookup failed: {exc}")
# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch DNS and WHOIS information for a domain"
    )
    parser.add_argument("domain", help="Domain name, e.g. example.com")
    args = parser.parse_args()
    domain = args.domain.strip()
    print(f"\n── Domain: {domain} ──")
    os.system("host " + domain)
    print(f"\n── DNS records for {domain} ──")
    dns_data = get_dns_records(domain)
    if dns_data:
        pprint(dns_data)
    else:
        print("No DNS data retrieved.")

    print(f"\n── WHOIS for {domain} ──")
    w = get_whois(domain)
    if not w:
        sys.exit(1)

    if whois_mostly_null(w):
        print(
            "⚠️  WHOIS information is almost entirely blank.\n"
            "   The domain is probably behind Cloudflare or has WHOIS privacy enabled."
        )
    else:
        for key, value in w.items():
            print(f"{key:<17}: {value}")
    get_netcraft(domain)

if __name__ == "__main__":
    main()
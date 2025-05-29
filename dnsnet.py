#!/usr/bin/env python3
"""
dnsnet.py – Fetch DNS records and WHOIS data for a domain.
Warn if the WHOIS response is almost entirely redacted (e.g. Cloudflare / privacy).
"""

import argparse
import sys
from pprint import pprint
import requests
import whois
from colorama import init, Fore
init(autoreset=True)
print(Fore.GREEN + """
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
# Main
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch DNS and WHOIS information for a domain"
    )
    parser.add_argument("domain", help="Domain name, e.g. example.com")
    args = parser.parse_args()
    domain = args.domain.strip()

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


if __name__ == "__main__":
    main()

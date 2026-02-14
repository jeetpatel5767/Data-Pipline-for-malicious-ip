"""
enrichment.py — Bridge between the data pipeline DB and the API scanner.

Reads IOCs from the DB, calls VirusTotal / IPInfo / AbuseIPDB,
caches results in the enrichment_results table, and returns
combined JSON-ready dicts for the frontend.

Usage:
    from enrichment import enrich_ip, enrich_domain

    result = enrich_ip("8.8.8.8")        # returns combined dict
    result = enrich_domain("example.com") # returns combined dict
"""

import sys
import os
import json

# Add the Malicious-Check project to the path so we can import its API clients
SCANNER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Zeronsec", "Gunjan_Repo", "Malicious-Check"))
if SCANNER_DIR not in sys.path:
    sys.path.insert(0, SCANNER_DIR)

# --- Import API clients from the scanner project ---
import virustotal_client
import ipinfo_client
import abuseipdb_client

# --- Import local storage functions ---
from storage import (
    lookup_ip,
    lookup_domain,
    cache_enrichment,
    get_cached_enrichment,
)


# ==================== IP ENRICHMENT ====================

def enrich_ip(ip_address: str) -> dict:
    """
    Full IP enrichment flow:
    1. Check if IP exists in ip_iocs (flag: in_threat_feed)
    2. Check enrichment cache for each API
    3. If not cached: call VT → IPInfo → AbuseIPDB
    4. Cache results
    5. Return combined dict ready for frontend / API response
    """
    result = {
        "ioc_value": ip_address,
        "ioc_type": "ip",
        "in_threat_feed": False,
        "virustotal": None,
        "ipinfo": None,
        "abuseipdb": None,
    }

    # 1. Check threat feed DB
    db_match = lookup_ip(ip_address)
    if db_match:
        result["in_threat_feed"] = True
        result["first_seen"] = db_match.get("first_seen")

    # 2 & 3. Fetch from cache or call APIs

    # --- VirusTotal ---
    vt_data = get_cached_enrichment(ip_address, "virustotal")
    if not vt_data:
        vt_data = virustotal_client.search_ip(ip_address)
        if vt_data:
            # Also grab relationships
            resolutions = virustotal_client.get_ip_resolutions(ip_address)
            comm_files = virustotal_client.get_ip_communicating_files(ip_address)
            vt_data["resolutions"] = resolutions or []
            vt_data["communicating_files"] = comm_files or []
            cache_enrichment(ip_address, "ip", "virustotal", json.dumps(vt_data, default=str))
    result["virustotal"] = vt_data

    # --- IPInfo ---
    ipinfo_data = get_cached_enrichment(ip_address, "ipinfo")
    if not ipinfo_data:
        ipinfo_data = ipinfo_client.search_ip(ip_address)
        if ipinfo_data:
            cache_enrichment(ip_address, "ip", "ipinfo", json.dumps(ipinfo_data, default=str))
    result["ipinfo"] = ipinfo_data

    # --- AbuseIPDB ---
    abuse_data = get_cached_enrichment(ip_address, "abuseipdb")
    if not abuse_data:
        abuse_data = abuseipdb_client.search_ip(ip_address)
        if abuse_data:
            cache_enrichment(ip_address, "ip", "abuseipdb", json.dumps(abuse_data, default=str))
    result["abuseipdb"] = abuse_data

    return result


# ==================== DOMAIN ENRICHMENT ====================

def enrich_domain(domain: str) -> dict:
    """
    Full domain enrichment flow:
    1. Check if domain exists in domain_iocs (flag: in_threat_feed)
    2. Check enrichment cache
    3. If not cached: call VT domain → extract resolved IPs → IPInfo + AbuseIPDB per IP
    4. Cache results
    5. Return combined dict ready for frontend / API response
    """
    result = {
        "ioc_value": domain,
        "ioc_type": "domain",
        "in_threat_feed": False,
        "virustotal": None,
        "resolved_ips": [],
    }

    # 1. Check threat feed DB
    db_match = lookup_domain(domain)
    if db_match:
        result["in_threat_feed"] = True
        result["first_seen"] = db_match.get("first_seen")

    # 2 & 3. Fetch from cache or call VT

    # --- VirusTotal Domain ---
    vt_data = get_cached_enrichment(domain, "virustotal")
    if not vt_data:
        vt_data = virustotal_client.search_domain(domain)
        if vt_data:
            # Also grab subdomains and communicating files
            vt_subs = virustotal_client.get_domain_subdomains(domain)
            comm_files = virustotal_client.get_domain_communicating_files(domain)
            vt_data["subdomains"] = vt_subs or []
            vt_data["communicating_files"] = comm_files or []
            cache_enrichment(domain, "domain", "virustotal", json.dumps(vt_data, default=str))
    result["virustotal"] = vt_data

    # --- Extract resolved IPs from VT ---
    resolved_ips = set()

    # From VT resolutions
    vt_resolutions = virustotal_client.get_domain_resolutions(domain)
    if vt_resolutions:
        result["virustotal"]["resolutions"] = vt_resolutions
        for res in vt_resolutions:
            ip = res.get("ip_address")
            if ip:
                resolved_ips.add(ip)

    # --- Cascade each resolved IP into IPInfo + AbuseIPDB ---
    ip_results = []
    cascade_ips = list(resolved_ips)[:3]  # Limit to 3 to avoid rate limits

    for ip in cascade_ips:
        ip_entry = {"ip": ip, "ipinfo": None, "abuseipdb": None}

        # IPInfo
        ipinfo_data = get_cached_enrichment(ip, "ipinfo")
        if not ipinfo_data:
            ipinfo_data = ipinfo_client.search_ip(ip)
            if ipinfo_data:
                cache_enrichment(ip, "ip", "ipinfo", json.dumps(ipinfo_data, default=str))
        ip_entry["ipinfo"] = ipinfo_data

        # AbuseIPDB
        abuse_data = get_cached_enrichment(ip, "abuseipdb")
        if not abuse_data:
            abuse_data = abuseipdb_client.search_ip(ip)
            if abuse_data:
                cache_enrichment(ip, "ip", "abuseipdb", json.dumps(abuse_data, default=str))
        ip_entry["abuseipdb"] = abuse_data

        ip_results.append(ip_entry)

    result["resolved_ips"] = ip_results

    return result


# ==================== QUICK TEST ====================

if __name__ == "__main__":
    import sys as _sys

    if len(_sys.argv) < 2:
        print("Usage: python app/enrichment.py <ip_or_domain>")
        print("  Example: python app/enrichment.py 8.8.8.8")
        print("  Example: python app/enrichment.py example.com")
        _sys.exit(1)

    from storage import init_db
    init_db()

    target = _sys.argv[1]

    # Simple detection: if all parts are digits, it's an IP
    if all(part.isdigit() for part in target.split(".")) and target.count(".") == 3:
        print(f"\n🔍 Enriching IP: {target}\n")
        data = enrich_ip(target)
    else:
        print(f"\n🔍 Enriching Domain: {target}\n")
        data = enrich_domain(target)

    print(json.dumps(data, indent=2, default=str))

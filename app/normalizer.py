import re


def refang(value: str) -> str:
    value = value.replace("[.]", ".")
    value = value.replace("(.)", ".")
    value = value.replace("hxxp://", "http://")
    value = value.replace("hxxps://", "https://")
    return value


def normalize_url(url: str) -> str:
    url = refang(url.strip().lower())
    url = url.rstrip("/")
    return url


def normalize_domain(domain: str) -> str:
    domain = refang(domain.strip().lower())
    domain = domain.rstrip("/")
    return domain


def normalize_ip(ip: str) -> str:
    return ip.strip()


def normalize_indicators(indicators: dict):
    normalized = {
        "urls": set(),
        "domains": set(),
        "ips": set()
    }

    for url in indicators.get("urls", []):
        normalized["urls"].add(normalize_url(url))

    for domain in indicators.get("domains", []):
        normalized["domains"].add(normalize_domain(domain))

    for ip in indicators.get("ips", []):
        normalized["ips"].add(normalize_ip(ip))

    return {
        "urls": list(normalized["urls"]),
        "domains": list(normalized["domains"]),
        "ips": list(normalized["ips"])
    }

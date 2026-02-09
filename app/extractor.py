import re


URL_REGEX = re.compile(
    r"https?://[^\s\"'>]+",
    re.IGNORECASE
)

DOMAIN_REGEX = re.compile(
    r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b"
)

IP_REGEX = re.compile(
    r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
)


def extract_indicators(content: str):
    urls = set(URL_REGEX.findall(content))
    domains = set(DOMAIN_REGEX.findall(content))
    ips = set(IP_REGEX.findall(content))

    return {
        "urls": list(urls),
        "domains": list(domains),
        "ips": list(ips)
    }

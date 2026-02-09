import sys

from fetcher import fetch_url
from detector import detect_content_type
from extractor import extract_indicators
from normalizer import normalize_indicators
from storage import (
    init_db,
    store_iocs,
    register_source,
    should_ingest_source
)



def main():
    if len(sys.argv) < 2:
        print("Usage: python app/main.py <source_url>")
        return

    source_url = sys.argv[1]

    print("Initializing database...")
    init_db()

    print("Fetching:", source_url)
    result = fetch_url(source_url)

    if not result["success"]:
        print("Fetch failed ❌")
        print("Error:", result["error"])
        register_source(source_url, "FAILED")
        return


    detected_type = detect_content_type(
        result["content_type"],
        result["content"]
    )

    print("Detected Content Type:", detected_type)

    raw_indicators = extract_indicators(result["content"])
    normalized = normalize_indicators(raw_indicators)

    store_iocs(normalized, source_url)

    print("Stored indicators in database ✅")
    print(
        f"URLs: {len(normalized['urls'])}, "
        f"Domains: {len(normalized['domains'])}, "
        f"IPs: {len(normalized['ips'])}"
    )


if __name__ == "__main__":
    main()

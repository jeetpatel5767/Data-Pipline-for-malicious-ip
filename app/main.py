import sys
import os

from fetcher import fetch_url, read_file
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
        print("Usage: python app/main.py <source_url_or_file>")
        print("  source_url_or_file: A URL (http/https) or a local .txt file path")
        return

    source_input = sys.argv[1]

    print("Initializing database...")
    init_db()

    # Detect whether input is a local file or a URL
    is_url = source_input.lower().startswith("http://") or source_input.lower().startswith("https://")
    is_file = not is_url and (os.path.isfile(source_input) or source_input.lower().endswith(".txt"))

    if is_file:
        print("Reading file:", source_input)
        result = read_file(source_input)
        source_label = f"file://{os.path.abspath(source_input)}"
    else:
        print("Fetching:", source_input)
        result = fetch_url(source_input)
        source_label = source_input

    if not result["success"]:
        print("Failed ❌")
        print("Error:", result["error"])
        register_source(source_label, "FAILED")
        return


    detected_type = detect_content_type(
        result["content_type"],
        result["content"]
    )

    print("Detected Content Type:", detected_type)

    raw_indicators = extract_indicators(result["content"])
    normalized = normalize_indicators(raw_indicators)

    store_iocs(normalized, source_label)

    print("Stored indicators in database ✅")
    print(
        f"URLs: {len(normalized['urls'])}, "
        f"Domains: {len(normalized['domains'])}, "
        f"IPs: {len(normalized['ips'])}"
    )


if __name__ == "__main__":
    main()

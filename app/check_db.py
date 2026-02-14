"""
check_db.py — Quick inspection of the IOC database.
Shows counts and sample data from ip_iocs, domain_iocs, and enrichment_results tables.
"""

import sys
import io
import sqlite3
from pathlib import Path

# Fix Windows console encoding for emoji/unicode
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DB_PATH = Path("db/raw_iocs.db")


def check():
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ------ IP IOCs ------
    print("=" * 50)
    print("  IP IOCs TABLE")
    print("=" * 50)
    try:
        cursor.execute("SELECT COUNT(*) FROM ip_iocs")
        count = cursor.fetchone()[0]
        print(f"  Total: {count}")

        cursor.execute("SELECT id, ip_address, first_seen FROM ip_iocs LIMIT 10")
        rows = cursor.fetchall()
        if rows:
            print(f"  Showing first {len(rows)}:")
            for row in rows:
                print(f"    [{row[0]}] {row[1]}  (seen: {row[2]})")
        else:
            print("  (empty)")
    except sqlite3.OperationalError:
        print("  ⚠️  Table 'ip_iocs' does not exist yet.")

    # ------ Domain IOCs ------
    print()
    print("=" * 50)
    print("  DOMAIN / URL IOCs TABLE")
    print("=" * 50)
    try:
        cursor.execute("SELECT COUNT(*) FROM domain_iocs WHERE ioc_type = 'domain'")
        domain_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM domain_iocs WHERE ioc_type = 'url'")
        url_count = cursor.fetchone()[0]
        print(f"  Domains: {domain_count}  |  URLs: {url_count}")

        cursor.execute("SELECT id, domain_or_url, ioc_type, first_seen FROM domain_iocs LIMIT 10")
        rows = cursor.fetchall()
        if rows:
            print(f"  Showing first {len(rows)}:")
            for row in rows:
                print(f"    [{row[0]}] ({row[2]}) {row[1]}  (seen: {row[3]})")
        else:
            print("  (empty)")
    except sqlite3.OperationalError:
        print("  ⚠️  Table 'domain_iocs' does not exist yet.")

    # ------ Enrichment Results ------
    print()
    print("=" * 50)
    print("  ENRICHMENT CACHE")
    print("=" * 50)
    try:
        cursor.execute("SELECT COUNT(*) FROM enrichment_results")
        count = cursor.fetchone()[0]
        print(f"  Total cached results: {count}")

        cursor.execute(
            "SELECT ioc_value, api_source, enriched_at FROM enrichment_results ORDER BY enriched_at DESC LIMIT 5"
        )
        rows = cursor.fetchall()
        if rows:
            print(f"  Recent enrichments:")
            for row in rows:
                print(f"    {row[0]} → {row[1]}  (at: {row[2]})")
    except sqlite3.OperationalError:
        print("  ⚠️  Table 'enrichment_results' does not exist yet.")

    # ------ Sources ------
    print()
    print("=" * 50)
    print("  SOURCES TABLE")
    print("=" * 50)
    try:
        cursor.execute("SELECT source_url, first_seen, last_ingested, last_status FROM sources")
        sources = cursor.fetchall()
        if sources:
            for s in sources:
                print(f"    {s[0]}")
                print(f"      First seen: {s[1]}  |  Last ingested: {s[2]}  |  Status: {s[3]}")
        else:
            print("  (empty)")
    except sqlite3.OperationalError:
        print("  ⚠️  Table 'sources' does not exist yet.")

    # ------ Legacy raw_iocs (if still exists) ------
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='raw_iocs'")
    if cursor.fetchone():
        print()
        print("=" * 50)
        print("  ⚠️  LEGACY 'raw_iocs' TABLE STILL EXISTS")
        print("=" * 50)
        cursor.execute("SELECT COUNT(*) FROM raw_iocs")
        count = cursor.fetchone()[0]
        print(f"  Records: {count}")
        print(f"  Run 'python app/migrate.py' to migrate data to the new tables.")

    conn.close()


if __name__ == "__main__":
    check()

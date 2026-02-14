"""
migrate.py — One-time migration script.

Moves existing data from the old `raw_iocs` table into the new
`ip_iocs` and `domain_iocs` tables, using regex to classify each IOC.

Usage:
    python app/migrate.py
"""

import re
import sqlite3
from pathlib import Path

DB_PATH = Path("db/raw_iocs.db")


def is_ip(value: str) -> bool:
    """Check if the IOC value is an IP address."""
    pattern = r'^\d{1,3}(\.\d{1,3}){3}$'
    if re.match(pattern, value):
        parts = value.split('.')
        return all(0 <= int(p) <= 255 for p in parts)
    return False


def is_url(value: str) -> bool:
    """Check if the IOC value is a URL."""
    return value.startswith("http://") or value.startswith("https://")


def migrate():
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        print("   Run the data pipeline first to create the database.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if old raw_iocs table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='raw_iocs'")
    if not cursor.fetchone():
        print("⚠️  No 'raw_iocs' table found — nothing to migrate.")
        print("   The new schema is already in use or the DB is empty.")
        conn.close()
        return

    # Create the new tables if they don't exist
    schema_path = Path("db/schema.sql")
    if schema_path.exists():
        with open(schema_path, "r") as f:
            conn.executescript(f.read())
        conn.commit()

    # Read all existing IOCs
    cursor.execute("SELECT ioc_value FROM raw_iocs")
    rows = cursor.fetchall()

    if not rows:
        print("⚠️  raw_iocs table is empty — nothing to migrate.")
        conn.close()
        return

    ip_count = 0
    domain_count = 0
    url_count = 0

    for (ioc_value,) in rows:
        value = ioc_value.strip()

        if is_ip(value):
            cursor.execute(
                "INSERT OR IGNORE INTO ip_iocs (ip_address) VALUES (?)",
                (value,)
            )
            ip_count += 1

        elif is_url(value):
            cursor.execute(
                "INSERT OR IGNORE INTO domain_iocs (domain_or_url, ioc_type) VALUES (?, 'url')",
                (value,)
            )
            url_count += 1

        else:
            # Assume domain
            cursor.execute(
                "INSERT OR IGNORE INTO domain_iocs (domain_or_url, ioc_type) VALUES (?, 'domain')",
                (value,)
            )
            domain_count += 1

    conn.commit()
    conn.close()

    print(f"✅ Migration complete!")
    print(f"   IPs migrated to ip_iocs:         {ip_count}")
    print(f"   Domains migrated to domain_iocs:  {domain_count}")
    print(f"   URLs migrated to domain_iocs:     {url_count}")
    print(f"   Total processed:                  {ip_count + domain_count + url_count}")
    print()
    print(f"💡 The old 'raw_iocs' table is still intact. You can drop it manually when ready:")
    print(f"   sqlite3 db/raw_iocs.db \"DROP TABLE raw_iocs;\"")


if __name__ == "__main__":
    migrate()

import sqlite3

conn = sqlite3.connect("db/raw_iocs.db")
cursor = conn.cursor()

print("=== RAW IOC TABLE ===")
cursor.execute(
    "SELECT ioc_value, ioc_type, source_url, status FROM raw_iocs"
)
rows = cursor.fetchall()

if not rows:
    print("No IOCs found.")
else:
    for row in rows:
        print(row)

print("\n=== SOURCES TABLE ===")
cursor.execute(
    "SELECT source_url, first_seen, last_ingested, last_status FROM sources"
)
sources = cursor.fetchall()

if not sources:
    print("No sources found.")
else:
    for source in sources:
        print(source)

conn.close()

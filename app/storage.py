import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path("db/raw_iocs.db")


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    with open("db/schema.sql", "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def store_iocs(iocs: dict, source_url: str):
    conn = get_connection()
    cursor = conn.cursor()

    for url in iocs.get("urls", []):
        cursor.execute(
            """
            INSERT INTO raw_iocs (ioc_value, ioc_type, source_url)
            VALUES (?, 'url', ?)
            ON CONFLICT(ioc_value, ioc_type)
            DO UPDATE SET last_seen = CURRENT_TIMESTAMP
            """,
            (url, source_url)
        )

    for domain in iocs.get("domains", []):
        cursor.execute(
            """
            INSERT INTO raw_iocs (ioc_value, ioc_type, source_url)
            VALUES (?, 'domain', ?)
            ON CONFLICT(ioc_value, ioc_type)
            DO UPDATE SET last_seen = CURRENT_TIMESTAMP
            """,
            (domain, source_url)
        )

    for ip in iocs.get("ips", []):
        cursor.execute(
            """
            INSERT INTO raw_iocs (ioc_value, ioc_type, source_url)
            VALUES (?, 'ip', ?)
            ON CONFLICT(ioc_value, ioc_type)
            DO UPDATE SET last_seen = CURRENT_TIMESTAMP
            """,
            (ip, source_url)
        )

    conn.commit()
    conn.close()

def register_source(source_url: str, status: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO sources (source_url, last_ingested, last_status)
        VALUES (?, CURRENT_TIMESTAMP, ?)
        ON CONFLICT(source_url)
        DO UPDATE SET
            last_ingested = CURRENT_TIMESTAMP,
            last_status = ?
        """,
        (source_url, status, status)
    )

    conn.commit()
    conn.close()

def should_ingest_source(source_url: str, cooldown_hours: int = 24) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT last_ingested FROM sources
        WHERE source_url = ?
        """,
        (source_url,)
    )

    row = cursor.fetchone()
    conn.close()

    # Source never ingested before → ingest
    if not row or not row[0]:
        return True

    last_ingested = datetime.fromisoformat(row[0])
    now = datetime.utcnow()

    if now - last_ingested > timedelta(hours=cooldown_hours):
        return True

    return False
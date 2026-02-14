import sqlite3
import json
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


# ==================== STORE IOCs ====================

def store_iocs(iocs: dict, source_url: str):
    """Store extracted IOCs into the appropriate tables (ip_iocs / domain_iocs)."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get or create the source ID
    source_id = _get_or_create_source(cursor, source_url)

    # Store IPs in ip_iocs table
    for ip in iocs.get("ips", []):
        cursor.execute(
            "INSERT OR IGNORE INTO ip_iocs (ip_address, source_id) VALUES (?, ?)",
            (ip, source_id)
        )

    # Store Domains in domain_iocs table
    for domain in iocs.get("domains", []):
        cursor.execute(
            "INSERT OR IGNORE INTO domain_iocs (domain_or_url, ioc_type, source_id) VALUES (?, 'domain', ?)",
            (domain, source_id)
        )

    # Store URLs in domain_iocs table
    for url in iocs.get("urls", []):
        cursor.execute(
            "INSERT OR IGNORE INTO domain_iocs (domain_or_url, ioc_type, source_id) VALUES (?, 'url', ?)",
            (url, source_id)
        )

    conn.commit()
    conn.close()


def _get_or_create_source(cursor, source_url: str) -> int:
    """Get existing source ID or create a new source entry."""
    cursor.execute("SELECT id FROM sources WHERE source_url = ?", (source_url,))
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute(
        "INSERT INTO sources (source_url, last_ingested, last_status) VALUES (?, CURRENT_TIMESTAMP, 'OK')",
        (source_url,)
    )
    return cursor.lastrowid


# ==================== LOOKUP IOCs ====================

def lookup_ip(ip_address: str) -> dict | None:
    """Check if an IP exists in the ip_iocs table. Returns row dict or None."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, ip_address, first_seen, source_id FROM ip_iocs WHERE ip_address = ?",
        (ip_address,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "ip_address": row[1],
        "first_seen": row[2],
        "source_id": row[3],
    }


def lookup_domain(domain_or_url: str) -> dict | None:
    """Check if a domain/URL exists in the domain_iocs table. Returns row dict or None."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, domain_or_url, ioc_type, first_seen, source_id FROM domain_iocs WHERE domain_or_url = ?",
        (domain_or_url,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "domain_or_url": row[1],
        "ioc_type": row[2],
        "first_seen": row[3],
        "source_id": row[4],
    }


# ==================== ENRICHMENT CACHE ====================

def cache_enrichment(ioc_value: str, ioc_type: str, api_source: str, result_json: str):
    """
    Store API enrichment results for caching.
    If a cached entry already exists for (ioc_value, api_source), it gets replaced.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO enrichment_results (ioc_value, ioc_type, api_source, result_json)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(ioc_value, api_source)
        DO UPDATE SET
            result_json = excluded.result_json,
            enriched_at = CURRENT_TIMESTAMP
        """,
        (ioc_value, ioc_type, api_source, result_json)
    )

    conn.commit()
    conn.close()


def get_cached_enrichment(ioc_value: str, api_source: str, max_age_hours: int = 24) -> dict | None:
    """
    Retrieve cached API results if they exist and are fresh enough.
    Returns the parsed JSON dict or None if stale/missing.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT result_json, enriched_at FROM enrichment_results WHERE ioc_value = ? AND api_source = ?",
        (ioc_value, api_source)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    enriched_at = datetime.fromisoformat(row[1])
    now = datetime.utcnow()

    if now - enriched_at > timedelta(hours=max_age_hours):
        return None  # Cache is stale

    try:
        return json.loads(row[0])
    except json.JSONDecodeError:
        return None


# ==================== SOURCE MANAGEMENT ====================

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
        "SELECT last_ingested FROM sources WHERE source_url = ?",
        (source_url,)
    )

    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        return True

    last_ingested = datetime.fromisoformat(row[0])
    now = datetime.utcnow()

    if now - last_ingested > timedelta(hours=cooldown_hours):
        return True

    return False


# ==================== STATS ====================

def get_db_stats() -> dict:
    """Get counts from both IOC tables for quick stats."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM ip_iocs")
    ip_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM domain_iocs WHERE ioc_type = 'domain'")
    domain_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM domain_iocs WHERE ioc_type = 'url'")
    url_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM enrichment_results")
    enrichment_count = cursor.fetchone()[0]

    conn.close()

    return {
        "ips": ip_count,
        "domains": domain_count,
        "urls": url_count,
        "cached_enrichments": enrichment_count,
    }
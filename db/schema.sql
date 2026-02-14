-- ============================================
-- IP-based IOCs (from threat feeds)
-- ============================================
CREATE TABLE IF NOT EXISTS ip_iocs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address    TEXT UNIQUE NOT NULL,
    first_seen    DATETIME DEFAULT CURRENT_TIMESTAMP,
    source_id     INTEGER REFERENCES sources(id)
);

-- ============================================
-- Domain/URL-based IOCs (from threat feeds)
-- ============================================
CREATE TABLE IF NOT EXISTS domain_iocs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_or_url TEXT UNIQUE NOT NULL,
    ioc_type      TEXT NOT NULL CHECK(ioc_type IN ('domain', 'url')),
    first_seen    DATETIME DEFAULT CURRENT_TIMESTAMP,
    source_id     INTEGER REFERENCES sources(id)
);

-- ============================================
-- Enrichment cache (API results)
-- Stores JSON responses from VT, IPInfo, AbuseIPDB
-- so we don't re-call APIs for the same IOC
-- ============================================
CREATE TABLE IF NOT EXISTS enrichment_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ioc_value       TEXT NOT NULL,
    ioc_type        TEXT NOT NULL,
    api_source      TEXT NOT NULL,
    result_json     TEXT NOT NULL,
    enriched_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ioc_value, api_source)
);

-- ============================================
-- Feed sources (unchanged)
-- ============================================
CREATE TABLE IF NOT EXISTS sources (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url     TEXT UNIQUE NOT NULL,
    first_seen     DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_ingested  DATETIME,
    last_status    TEXT
);

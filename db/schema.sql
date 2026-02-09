CREATE TABLE IF NOT EXISTS raw_iocs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ioc_value TEXT NOT NULL,
    ioc_type TEXT NOT NULL,         -- url | domain | ip
    source_url TEXT NOT NULL,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'UNVERIFIED',
    UNIQUE(ioc_value, ioc_type)
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT UNIQUE NOT NULL,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_ingested DATETIME,
    last_status TEXT
);

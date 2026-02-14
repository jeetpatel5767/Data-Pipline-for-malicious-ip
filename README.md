# Malicious IP & Domain Threat Intelligence Pipeline

A two-part threat intelligence system that ingests IOCs (Indicators of Compromise) from public threat feeds and enriches them with live API data from VirusTotal, IPInfo, and AbuseIPDB.

---

## Project Structure

```
AI+TI/                              ← Data Pipeline (this repo)
├── db/
│   ├── schema.sql                  ← Database schema
│   └── raw_iocs.db                 ← SQLite database (auto-created)
├── app/
│   ├── main.py                     ← Ingest IOCs from threat feeds
│   ├── fetcher.py                  ← Fetch data from URLs or local files
│   ├── extractor.py                ← Extract IPs, domains, URLs using regex
│   ├── normalizer.py               ← Clean and normalize IOCs
│   ├── detector.py                 ← Detect content type (JSON/HTML/text)
│   ├── storage.py                  ← Store IOCs in DB + lookup + caching
│   ├── enrichment.py               ← Bridge: connects DB to API scanner
│   ├── migrate.py                  ← One-time migration script
│   └── check_db.py                 ← Inspect database contents
└── README.md

Malicious-Check/                    ← API Scanner
├── main.py                         ← Interactive CLI scanner
├── virustotal_client.py            ← VirusTotal API client
├── ipinfo_client.py                ← IPInfo API client
├── abuseipdb_client.py             ← AbuseIPDB API client
├── domain.py                       ← Domain reconnaissance
├── config.py                       ← API keys & input detection
├── display.py                      ← Terminal display formatting
├── .env                            ← API keys (DO NOT commit)
└── requirements.txt
```

---

## How It Works

### Pipeline 1 — Data Ingestion (`AI+TI`)

Fetches IOC lists from public threat feeds and stores them in SQLite:

```
Threat Feed URL → Fetch → Extract IPs/Domains/URLs → Normalize → Store in DB
```

The database has two tables:
- **`ip_iocs`** — 2,152+ malicious IP addresses
- **`domain_iocs`** — 219,618+ malicious domains & URLs

### Pipeline 2 — API Scanner (`Malicious-Check`)

Interactive CLI tool that queries 3 security APIs:

```
User enters IP/Domain → VirusTotal → IPInfo → AbuseIPDB → Display results
```

### The Bridge — `enrichment.py`

Connects both pipelines:

```
1. Check if IOC exists in threat feed DB → flag: in_threat_feed
2. Call VirusTotal, IPInfo, AbuseIPDB
3. Cache API results in DB (reuses for 24 hours)
4. Return combined JSON response
```

---

## Quick Start

### Step 1 — Install Dependencies

```bash
# For the data pipeline
cd AI+TI
pip install requests

# For the API scanner
cd Malicious-Check
pip install -r requirements.txt
```

### Step 2 — Configure API Keys

Edit `Malicious-Check/.env` with your API keys:

```env
VIRUSTOTAL_API_KEY=your_key_here
IPINFO_API_KEY=your_key_here
ABUSEIPDB_API_KEY=your_key_here
```

Get your keys from:
- VirusTotal: https://www.virustotal.com/gui/my-apikey
- IPInfo: https://ipinfo.io/account/token
- AbuseIPDB: https://www.abuseipdb.com/account/api

### Step 3 — Ingest Threat Feeds (Data Pipeline)

```bash
cd AI+TI

# From a URL
python app/main.py https://example.com/threat-feed.txt

# From a local file
python app/main.py data/malicious_ips.txt
```

This stores all extracted IPs, domains, and URLs into the database.

### Step 4 — Run Interactive Scanner

```bash
cd Malicious-Check
python main.py
```

Enter any IP, domain, URL, or file hash to get full threat intelligence.

### Step 5 — Use the Enrichment Bridge

```bash
cd AI+TI

# Enrich an IP (checks DB + calls all 3 APIs)
python app/enrichment.py 8.8.8.8

# Enrich a domain (checks DB + calls VT + cascades resolved IPs to IPInfo & AbuseIPDB)
python app/enrichment.py kavachdownload.in
```

Returns a combined JSON with:
- `in_threat_feed` — whether the IOC was found in the ingested threat feeds
- `virustotal` — detection scores, WHOIS, reputation, resolutions
- `ipinfo` — geolocation, ASN, organization
- `abuseipdb` — abuse score, reports, ISP

---

## Useful Commands

| Command | What It Does |
|---------|-------------|
| `python app/main.py <url>` | Ingest a threat feed into the DB |
| `python app/check_db.py` | View database stats and sample data |
| `python app/enrichment.py <ip>` | Enrich an IP with all 3 APIs |
| `python app/enrichment.py <domain>` | Enrich a domain with all 3 APIs |
| `python app/migrate.py` | Migrate old `raw_iocs` data to new tables |

---

## Database Tables

| Table | Contents | Count |
|-------|----------|-------|
| `ip_iocs` | Malicious IP addresses from threat feeds | 2,152+ |
| `domain_iocs` | Malicious domains & URLs from threat feeds | 219,618+ |
| `enrichment_results` | Cached API responses (auto-filled) | grows on use |
| `sources` | Tracked threat feed sources | varies |

---

## Search Flow (for future website)

```
User searches "8.8.8.8" with IP mode selected
  → Query ip_iocs table (fast DB lookup)
  → Found? Flag as "in threat feed"
  → Check enrichment cache
  → If cached & fresh → return immediately
  → If not → call VT + IPInfo + AbuseIPDB → cache → return

User searches "kavachdownload.in" with Domain mode selected
  → Query domain_iocs table (fast DB lookup)
  → Found? Flag as "in threat feed"
  → Call VT domain → extract resolved IPs
  → For each IP → call IPInfo + AbuseIPDB
  → Cache everything → return
```

---

## Rate Limits

| API | Free Tier Limit |
|-----|----------------|
| VirusTotal | 4 requests/minute |
| IPInfo | 50,000 requests/month |
| AbuseIPDB | 1,000 requests/day |

---

## License

For educational and security research purposes only.

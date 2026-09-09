-- Demo analytics database for the EU market-entry scenario.
-- Loaded automatically by docker-compose on FIRST start of the postgres volume.
-- If you change this file, run `docker compose down -v` or it will not be re-applied.

CREATE TABLE IF NOT EXISTS companies (
    id           SERIAL PRIMARY KEY,
    name         TEXT NOT NULL,
    home_market  TEXT NOT NULL,
    founded_year INT
);

CREATE TABLE IF NOT EXISTS markets (
    id            SERIAL PRIMARY KEY,
    country       TEXT NOT NULL UNIQUE,
    region        TEXT NOT NULL,          -- EU sub-region: Western / Nordic / Southern / CEE
    currency      TEXT NOT NULL,
    population_m  NUMERIC(6,2),           -- enables per-capita analysis
    eu_member     BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS revenue_monthly (
    id           SERIAL PRIMARY KEY,
    company_id   INT REFERENCES companies(id),
    market_id    INT REFERENCES markets(id),
    month        DATE NOT NULL,
    units        INT,
    revenue_eur  NUMERIC(14,2) NOT NULL,
    cogs_eur     NUMERIC(14,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS competitors (
    id            SERIAL PRIMARY KEY,
    name          TEXT NOT NULL,
    market_id     INT REFERENCES markets(id),
    market_share  NUMERIC(5,2),
    year          INT
);

-- `source` is provenance inside the database, mirroring MANIFEST.json for the corpus.
-- A row marked 'estimated' is a figure nobody published; an agent that cites it as
-- fact without saying so is making an error the fact critic must catch.
CREATE TABLE IF NOT EXISTS ev_registrations (
    id            SERIAL PRIMARY KEY,
    market_id     INT REFERENCES markets(id),
    year          INT NOT NULL,
    registrations INT NOT NULL,
    powertrain    TEXT NOT NULL,          -- BEV | PHEV | HEV
    source        TEXT NOT NULL DEFAULT 'estimated'
);

CREATE INDEX IF NOT EXISTS idx_revenue_market_month ON revenue_monthly (market_id, month);
CREATE INDEX IF NOT EXISTS idx_registrations_market_year ON ev_registrations (market_id, year);

-- Read-only role used by the data agent. The SQL guard is layer 1-3; this is layer 4.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'arp_readonly') THEN
        CREATE ROLE arp_readonly LOGIN PASSWORD 'arp';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE arp TO arp_readonly;
GRANT USAGE ON SCHEMA public TO arp_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO arp_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO arp_readonly;

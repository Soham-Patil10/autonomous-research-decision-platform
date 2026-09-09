-- Demo analytics database for the market-entry scenario.
-- Loaded automatically by docker-compose on first start.

CREATE TABLE IF NOT EXISTS companies (
    id           SERIAL PRIMARY KEY,
    name         TEXT NOT NULL,
    home_market  TEXT NOT NULL,
    founded_year INT
);

CREATE TABLE IF NOT EXISTS markets (
    id           SERIAL PRIMARY KEY,
    country      TEXT NOT NULL UNIQUE,
    region       TEXT NOT NULL,
    currency     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS revenue_monthly (
    id           SERIAL PRIMARY KEY,
    company_id   INT REFERENCES companies(id),
    market_id    INT REFERENCES markets(id),
    month        DATE NOT NULL,
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

CREATE TABLE IF NOT EXISTS ev_registrations (
    id            SERIAL PRIMARY KEY,
    market_id     INT REFERENCES markets(id),
    year          INT NOT NULL,
    registrations INT NOT NULL,
    powertrain    TEXT NOT NULL  -- BEV | PHEV | HEV
);

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

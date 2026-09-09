"""Engines and sessions.

Two engines on purpose: the application engine owns writes to the platform's own
tables; the analytics engine is read-only and is the *only* thing the data agent's
queries ever touch.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

_settings = get_settings()

engine = create_engine(_settings.postgres_dsn, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

# Read-only role. Enforce it in Postgres too:
#   CREATE ROLE arp_readonly LOGIN PASSWORD 'arp';
#   GRANT CONNECT ON DATABASE arp TO arp_readonly;
#   GRANT USAGE ON SCHEMA public TO arp_readonly;
#   GRANT SELECT ON ALL TABLES IN SCHEMA public TO arp_readonly;
analytics_engine = create_engine(
    _settings.analytics_dsn,
    pool_pre_ping=True,
    future=True,
    execution_options={"postgresql_readonly": True},
)


def init_db() -> None:
    from app.db.models import Base

    Base.metadata.create_all(engine)

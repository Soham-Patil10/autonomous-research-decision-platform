"""SQL tool. Every query passes the guard, then runs on a read-only connection.

Note that `query()` refuses rather than sanitises. Silently rewriting a dangerous
query hides the failure from your evaluation; refusing it produces a signal the
supervisor can act on and the failure dataset can learn from.
"""

from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.guardrails.sql_guard import SQLGuard

# Tables the data agent is allowed to see. Everything else is invisible to the LLM.
ALLOWED_TABLES = {
    "companies",
    "markets",
    "revenue_monthly",
    "competitors",
    "ev_registrations",
}


async def schema() -> dict[str, Any]:
    """TODO(v1): introspect information_schema, restricted to ALLOWED_TABLES.

    Feed only this to the prompt. A model that cannot see a table cannot query it.
    """
    return {t: [] for t in sorted(ALLOWED_TABLES)}


async def query(sql: str) -> list[dict[str, Any]]:
    settings = get_settings()
    guard = SQLGuard(allowed_tables=ALLOWED_TABLES, max_rows=5000)

    verdict = guard.validate(sql)
    if not verdict.safe:
        raise PermissionError("SQL blocked: " + "; ".join(verdict.reasons))

    # TODO(v2): execute verdict.sql over settings.analytics_dsn inside
    #   BEGIN TRANSACTION READ ONLY; SET LOCAL statement_timeout = '15s';
    _ = settings.analytics_dsn
    return [{"stub": True, "executed_sql": verdict.sql}]

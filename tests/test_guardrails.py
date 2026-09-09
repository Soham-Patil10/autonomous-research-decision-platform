"""Guardrail tests. Write these first — they are the ones that must never regress."""

from __future__ import annotations

import pytest

from app.guardrails.policy import PolicyEngine
from app.guardrails.sql_guard import SQLGuard
from app.schemas.core import AgentRole

TABLES = {"revenue_monthly", "markets"}


# --------------------------------------------------------------------------- #
# SQL guard
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE revenue_monthly",
        "DELETE FROM revenue_monthly",
        "UPDATE revenue_monthly SET revenue_eur = 0",
        "SELECT 1; DROP TABLE markets",
        "SELECT * FROM pg_shadow",
        "SELECT pg_sleep(60)",
    ],
)
def test_dangerous_sql_is_blocked(sql: str) -> None:
    assert SQLGuard(allowed_tables=TABLES).validate(sql).safe is False


def test_select_is_allowed_and_limited() -> None:
    verdict = SQLGuard(allowed_tables=TABLES, max_rows=100).validate(
        "SELECT month, revenue_eur FROM revenue_monthly"
    )
    assert verdict.safe
    assert "LIMIT 100" in verdict.sql.upper()


def test_existing_limit_is_preserved() -> None:
    verdict = SQLGuard(allowed_tables=TABLES).validate("SELECT * FROM markets LIMIT 5")
    assert verdict.safe
    assert "LIMIT 5" in verdict.sql.upper()


def test_table_allowlist_is_enforced() -> None:
    verdict = SQLGuard(allowed_tables=TABLES).validate("SELECT * FROM salaries")
    assert not verdict.safe
    assert any("allowlist" in r for r in verdict.reasons)


# --------------------------------------------------------------------------- #
# Tool policy
# --------------------------------------------------------------------------- #
def test_agent_cannot_use_another_agents_tool() -> None:
    decision = PolicyEngine().check(AgentRole.RESEARCH, "sql_query", {})
    assert not decision.allowed


def test_agent_can_use_its_own_tool() -> None:
    assert PolicyEngine().check(AgentRole.DATA, "sql_query", {}).allowed


def test_supervisor_has_no_tools() -> None:
    assert not PolicyEngine().check(AgentRole.SUPERVISOR, "web_search", {}).allowed


def test_call_budget_is_enforced() -> None:
    engine = PolicyEngine()
    for _ in range(8):
        assert engine.check(AgentRole.DATA, "sql_query", {}).allowed
    assert not engine.check(AgentRole.DATA, "sql_query", {}).allowed

"""SQL guardrail: validate and constrain LLM-generated SQL before it reaches a database.

Defence in depth, four independent layers — any one of which is bypassable alone:

  1. Parse with sqlglot and assert the AST is a single SELECT.  (structural)
  2. Reject blocked constructs and tables not on the allowlist. (semantic)
  3. Force a LIMIT onto the query.                              (blast radius)
  4. Execute as a read-only role in a read-only transaction.    (privilege)

Layer 4 is the one that actually saves you. The first three keep the agent honest and
give you a readable error to feed back into the loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import sqlglot
from sqlglot import expressions as exp

BLOCKED = (
    exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create,
    exp.Alter, exp.TruncateTable, exp.Grant,
)

BLOCKED_KEYWORDS = ("pg_read_file", "pg_sleep", "copy ", "dblink", "lo_import")


@dataclass
class SQLVerdict:
    safe: bool
    sql: str = ""
    reasons: list[str] = field(default_factory=list)


class SQLGuard:
    def __init__(self, allowed_tables: set[str] | None = None, max_rows: int = 5000) -> None:
        self.allowed_tables = allowed_tables
        self.max_rows = max_rows

    def validate(self, sql: str) -> SQLVerdict:
        reasons: list[str] = []

        lowered = sql.lower()
        for kw in BLOCKED_KEYWORDS:
            if kw in lowered:
                reasons.append(f"blocked keyword: {kw.strip()}")

        try:
            statements = sqlglot.parse(sql, read="postgres")
        except Exception as exc:  # noqa: BLE001
            return SQLVerdict(False, reasons=[f"unparseable SQL: {exc}"])

        if len(statements) != 1:
            reasons.append(f"expected exactly 1 statement, got {len(statements)}")

        tree = statements[0]
        if not isinstance(tree, exp.Select):
            reasons.append(f"only SELECT is permitted, got {type(tree).__name__}")

        for node_type in BLOCKED:
            if list(tree.find_all(node_type)):
                reasons.append(f"contains forbidden {node_type.__name__}")

        if self.allowed_tables is not None:
            used = {t.name for t in tree.find_all(exp.Table)}
            if forbidden := used - self.allowed_tables:
                reasons.append(f"tables not on allowlist: {sorted(forbidden)}")

        if reasons:
            return SQLVerdict(False, reasons=reasons)

        return SQLVerdict(True, sql=self._enforce_limit(tree))

    # ----------------------------------------------------------------- #
    def _enforce_limit(self, tree: exp.Expression) -> str:
        existing = tree.args.get("limit")
        if existing is None:
            tree = tree.limit(self.max_rows)
        return tree.sql(dialect="postgres")

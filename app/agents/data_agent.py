"""Data agent: quantitative evidence via guarded text-to-SQL.

The agent never touches the database directly. It emits SQL, the guard validates and
rewrites it, and a read-only connection executes it. That separation is the whole
point — the LLM proposes, the guardrail disposes.
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.graph.state import RunState
from app.llm.router import Complexity
from app.schemas.core import AgentRole, Evidence, SubTask

SQL_PROMPT = """Given this schema:
{schema}

Write ONE read-only PostgreSQL query answering: {question}

Rules: SELECT only. No DDL, DML, CTE-writes, or multiple statements.
Always add an explicit LIMIT. Return only SQL, no prose.
"""


class DataAgent(BaseAgent):
    role = AgentRole.DATA
    system_prompt = "You translate analytical questions into safe, read-only SQL."

    async def run(self, subtask: SubTask, state: RunState) -> list[Evidence]:
        """TODO(v2): generate SQL from SQL_PROMPT, then self-check the result.

        Two checks worth implementing, both cheap and both catch real failures:
          1. Row-count sanity - an empty result on a question that implies data is a signal.
          2. Re-derivation - regenerate the query a second way and compare aggregates.
        """
        _ = self.llm.pick(Complexity.MEDIUM)
        schema = await self.call_tool("sql_schema")
        sql = f"SELECT 1 -- TODO: generate from {subtask.description!r} against {len(schema)} tables"

        rows = await self.call_tool("sql_query", sql=sql)
        return [
            Evidence(
                source_kind="database",
                source_id=sql,
                content=str(rows),
                retrieval_score=1.0,
                produced_by=self.role,
            )
        ]

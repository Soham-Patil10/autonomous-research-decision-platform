"""Document agent: private-corpus evidence via the hybrid RAG pipeline."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.graph.state import RunState
from app.schemas.core import AgentRole, Evidence, SubTask


class DocumentAgent(BaseAgent):
    role = AgentRole.DOCUMENT
    system_prompt = (
        "You answer strictly from the retrieved passages. Every sentence you produce must "
        "map to a passage id. If the passages do not contain the answer, say 'not in corpus'."
    )

    async def run(self, subtask: SubTask, state: RunState) -> list[Evidence]:
        """TODO(v2): expand the subtask into 2-3 sub-queries before retrieving.

        Multi-query retrieval measurably lifts recall on analytical questions.
        """
        chunks = await self.call_tool("doc_search", query=subtask.description)
        return [
            Evidence(
                source_kind="document",
                source_id=c["doc_id"],
                locator=c.get("locator", ""),
                content=c["text"],
                retrieval_score=c.get("score", 0.0),
                produced_by=self.role,
            )
            for c in chunks
        ]

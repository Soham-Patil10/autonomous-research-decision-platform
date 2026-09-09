"""Research agent: external / public evidence via web search."""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.graph.state import RunState
from app.schemas.core import AgentRole, Evidence, SubTask


class ResearchAgent(BaseAgent):
    role = AgentRole.RESEARCH
    system_prompt = (
        "You gather external market evidence. Quote sources verbatim, never paraphrase a "
        "number, and return the URL for every fact. If a claim cannot be sourced, say so."
    )

    async def run(self, subtask: SubTask, state: RunState) -> list[Evidence]:
        """TODO(v1): issue web_search, then summarise each hit into one Evidence."""
        results = await self.call_tool("web_search", query=subtask.description, max_results=5)
        return [
            Evidence(
                source_kind="web",
                source_id=hit["url"],
                content=hit["content"],
                retrieval_score=hit.get("score", 0.0),
                produced_by=self.role,
            )
            for hit in results
        ]

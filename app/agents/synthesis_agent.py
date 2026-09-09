"""Synthesis agent: evidence -> draft -> final cited report.

Two responsibilities, deliberately split:
  draft()    runs before review, so critics have something concrete to attack.
  finalise() runs after, folding in critic findings and the confidence calculation.
"""

from __future__ import annotations

from app.graph.state import RunState
from app.llm.router import Complexity, LLMRouter
from app.schemas.core import AgentRole, Claim, Report

DRAFT_PROMPT = """You are writing a decision memo. You have these evidence items:

{evidence}

Question: {question}

Write the memo as a series of standalone claims. After each claim, list the ids of the
evidence items that support it in square brackets. Never assert anything you cannot
attribute. Where the evidence is thin, write the claim anyway and mark it [UNSUPPORTED].
"""


class SynthesisAgent:
    role = AgentRole.SYNTHESIS

    def __init__(self) -> None:
        self.llm = LLMRouter()

    async def draft(self, state: RunState) -> tuple[str, list[Claim]]:
        """TODO(v1): render DRAFT_PROMPT, call the LLM, parse claims + citations out."""
        _ = self.llm.pick(Complexity.HIGH)
        evidence = state.get("evidence", [])
        draft = f"[stub draft over {len(evidence)} evidence items]"
        claims = [Claim(text=draft, evidence_ids=[e.id for e in evidence])]
        return draft, claims

    async def finalise(self, state: RunState) -> Report:
        """Assemble the report. Confidence is computed, never asked of the LLM."""
        adjudication = state.get("adjudication")
        claims = state.get("claims", [])
        unverified = [c.text for c in claims if c.verified is False]

        return Report(
            task_id=state["task_id"],
            question=state["question"],
            recommendation="TODO(v1): extract the recommendation sentence from the draft",
            summary=state.get("draft", ""),
            claims=claims,
            evidence=state.get("evidence", []),
            confidence=state.get("confidence", 0.0),
            unverified=unverified,
            adjudication=adjudication,
            human_approved=state.get("human_decision") == "approved",
        )

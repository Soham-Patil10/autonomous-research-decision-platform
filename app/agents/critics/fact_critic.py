"""Fact critic: does the evidence actually say what the draft claims it says?

This is citation verification, not vibes. For each claim we re-read only the cited
evidence and ask whether it entails the claim. A claim whose citation does not
entail it is the single most common failure mode in RAG systems.
"""

from __future__ import annotations

from app.graph.state import RunState
from app.llm.router import Complexity, LLMRouter
from app.schemas.core import AgentRole, CriticVerdict

PROMPT = """Claim: {claim}

Cited evidence:
{evidence}

Does the evidence ENTAIL the claim? Answer one of: ENTAILED, PARTIAL, CONTRADICTED,
NOT_SUPPORTED. Then give one sentence of justification quoting the deciding text.
"""


class FactCritic:
    role = AgentRole.FACT_CRITIC

    def __init__(self) -> None:
        self.llm = LLMRouter()

    async def review(self, state: RunState) -> CriticVerdict:
        """TODO(v3): score each claim against its own citations only.

        Score = fraction of claims rated ENTAILED. Any CONTRADICTED claim fails the
        verdict outright regardless of the fraction.
        """
        _ = self.llm.pick(Complexity.MEDIUM)
        claims = state.get("claims", [])
        uncited = [c for c in claims if not c.evidence_ids]

        return CriticVerdict(
            critic=self.role,
            score=0.0 if uncited else 1.0,
            passed=not uncited,
            issues=[f"claim has no citation: {c.text[:80]}" for c in uncited],
            reasoning="stub - citation presence only; replace with entailment check",
        )

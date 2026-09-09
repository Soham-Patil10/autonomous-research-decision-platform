"""Completeness critic: did we answer the question that was actually asked?

Decomposes the original question into its constituent asks and checks coverage.
This is the critic that catches "the memo forgot about regulatory cost" — the
failure that looks fine to a fact checker and fine to a logic checker.
"""

from __future__ import annotations

from app.graph.state import RunState
from app.llm.router import Complexity, LLMRouter
from app.schemas.core import AgentRole, CriticVerdict

PROMPT = """Original question: {question}

List every distinct thing the asker wants to know. Then, for each, say whether the
draft below addresses it: COVERED, PARTIAL, or MISSING.

Draft:
{draft}

Score = fraction COVERED. List every MISSING item as a required action.
"""


class CompletenessCritic:
    role = AgentRole.COMPLETENESS_CRITIC

    def __init__(self) -> None:
        self.llm = LLMRouter()

    async def review(self, state: RunState) -> CriticVerdict:
        """TODO(v3): implement with PROMPT.

        MISSING items feed straight back into the supervisor's re-plan as new
        subtasks - this is what makes the loop self-correcting rather than a retry.
        """
        _ = self.llm.pick(Complexity.MEDIUM)
        return CriticVerdict(
            critic=self.role,
            score=1.0,
            passed=True,
            reasoning="stub - always passes; replace with coverage decomposition",
        )

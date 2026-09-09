"""Logic critic: does the recommendation follow from the claims?

A report can be perfectly cited and still reach an unsupported conclusion. This
critic ignores factual accuracy entirely and only asks about inference.
"""

from __future__ import annotations

from app.graph.state import RunState
from app.llm.router import Complexity, LLMRouter
from app.schemas.core import AgentRole, CriticVerdict

PROMPT = """Assume every claim below is true.

Claims:
{claims}

Conclusion: {recommendation}

Identify: (a) inferential leaps, (b) unstated assumptions, (c) claims that contradict
each other, (d) whether the conclusion is stronger than the claims justify.
Score 0-1 for logical soundness.
"""


class LogicCritic:
    role = AgentRole.LOGIC_CRITIC

    def __init__(self) -> None:
        self.llm = LLMRouter()

    async def review(self, state: RunState) -> CriticVerdict:
        """TODO(v3): implement with PROMPT. Score independently of factuality."""
        _ = self.llm.pick(Complexity.HIGH)
        return CriticVerdict(
            critic=self.role,
            score=1.0,
            passed=True,
            reasoning="stub - always passes; replace with inference audit",
        )

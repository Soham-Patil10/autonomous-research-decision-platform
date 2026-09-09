"""Complexity-based model routing.

Not every step deserves the frontier model. Classification, query rewriting and
extraction run fine on a small model; planning and adjudication do not. Routing on
task complexity is where most of the cost in an agent system is won or lost.

The honest version of this claim needs evidence, so route *and* record: every call
logs (tier, tokens, latency, downstream eval score) so you can show the tradeoff.
"""

from __future__ import annotations

from enum import Enum

from app.config import get_settings


class Complexity(str, Enum):
    LOW = "low"        # extraction, formatting, classification
    MEDIUM = "medium"  # SQL generation, summarisation, single-claim verification
    HIGH = "high"      # planning, synthesis, adjudication, logical critique


class LLMRouter:
    def __init__(self) -> None:
        self.settings = get_settings()

    def pick(self, complexity: Complexity) -> str:
        s = self.settings
        return {
            Complexity.LOW: s.model_small,
            Complexity.MEDIUM: s.model_medium,
            Complexity.HIGH: s.model_large,
        }[complexity]

    def escalate(self, current_model: str) -> str:
        """TODO(v4): on a failed self-check, retry once at the next tier up.

        A cheap model that knows when to hand off beats an expensive model used blindly.
        """
        s = self.settings
        ladder = [s.model_small, s.model_medium, s.model_large]
        i = ladder.index(current_model) if current_model in ladder else 0
        return ladder[min(i + 1, len(ladder) - 1)]

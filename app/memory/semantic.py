"""Semantic memory: what happened last time we were asked something like this.

Stored per completed task: the question, the final plan, the confidence, and — most
usefully — the failure mode if it failed. The supervisor retrieves the nearest few
before planning, which is a cheap way to stop repeating the same mistake.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MemoryRecord:
    task_id: str
    question: str
    plan_summary: str
    confidence: float
    outcome: str            # "completed" | "failed" | "human_overridden"
    failure_mode: str = ""


class SemanticMemory:
    """TODO(v3): Chroma collection 'task_memory', embedded on `question`."""

    collection_name = "task_memory"

    async def remember(self, record: MemoryRecord) -> None:
        raise NotImplementedError("TODO(v3)")

    async def recall(self, question: str, k: int = 3) -> list[dict[str, Any]]:
        """Return similar past tasks. Empty list is a valid, common answer."""
        return []

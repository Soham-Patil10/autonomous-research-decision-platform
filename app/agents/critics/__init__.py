"""The critic panel: independent reviewers plus an adjudicator.

Independence is the point. Each critic sees the draft and the evidence but not the
other critics' verdicts, so their agreement carries information. Wide disagreement
is itself a signal — it routes the task to a human rather than to a coin flip.
"""

from __future__ import annotations

import asyncio

from app.agents.critics.adjudicator import Adjudicator
from app.agents.critics.completeness_critic import CompletenessCritic
from app.agents.critics.fact_critic import FactCritic
from app.agents.critics.logic_critic import LogicCritic
from app.graph.state import RunState
from app.schemas.core import Adjudication

PANEL = (FactCritic, LogicCritic, CompletenessCritic)


async def run_panel(state: RunState) -> Adjudication:
    verdicts = await asyncio.gather(*(critic().review(state) for critic in PANEL))
    return Adjudicator().adjudicate(list(verdicts))


__all__ = [
    "run_panel",
    "PANEL",
    "Adjudicator",
    "FactCritic",
    "LogicCritic",
    "CompletenessCritic",
]

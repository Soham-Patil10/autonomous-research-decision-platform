"""Adjudicator: reconciles the critic panel into one decision.

Deliberately mostly arithmetic rather than another LLM call. Aggregation logic you
can read is aggregation logic you can evaluate — and the disagreement measure is
what drives human escalation, so it must be deterministic.
"""

from __future__ import annotations

import statistics

from app.config import get_settings
from app.schemas.core import Adjudication, CriticVerdict

# A hard veto: no aggregate score can rescue a report the fact critic rejected.
VETO_CRITICS = {"fact_critic"}


class Adjudicator:
    def adjudicate(self, verdicts: list[CriticVerdict]) -> Adjudication:
        settings = get_settings()
        scores = [v.score for v in verdicts] or [0.0]

        aggregate = statistics.fmean(scores)
        disagreement = max(scores) - min(scores)

        vetoed = any(v.critic.value in VETO_CRITICS and not v.passed for v in verdicts)
        passed = (
            not vetoed
            and aggregate >= settings.confidence_escalate_below
            and disagreement <= settings.critic_disagreement_threshold
        )

        required: list[str] = []
        for v in verdicts:
            required.extend(v.issues)

        return Adjudication(
            passed=passed,
            aggregate_score=aggregate,
            disagreement=disagreement,
            verdicts=verdicts,
            required_actions=required,
        )

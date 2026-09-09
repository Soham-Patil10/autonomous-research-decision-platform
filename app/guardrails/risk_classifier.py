"""Risk classification: how much autonomy does *this* result get?

Risk is a property of the run, not of the question. A confidently-supported answer to
a scary question is lower risk than a shaky answer to a boring one. So the inputs are
confidence, critic disagreement, evidence coverage and whether anything failed.
"""

from __future__ import annotations

from app.config import get_settings
from app.graph.state import RunState
from app.schemas.core import RiskLevel


def classify_risk(state: RunState) -> RiskLevel:
    s = get_settings()
    adjudication = state.get("adjudication")
    confidence = state.get("confidence", 0.0)
    disagreement = adjudication.disagreement if adjudication else 1.0

    uncited = [c for c in state.get("claims", []) if not c.evidence_ids]
    failures = state.get("errors", [])

    if confidence < s.confidence_escalate_below or uncited:
        return RiskLevel.CRITICAL
    if disagreement > s.critic_disagreement_threshold or failures:
        return RiskLevel.HIGH
    if confidence < s.confidence_auto_approve:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW

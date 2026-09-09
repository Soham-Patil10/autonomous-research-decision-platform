"""Human-in-the-loop: when the system stops and asks.

The design goal is that a human is interrupted *because the system detected it was
out of its depth*, not because a developer wired an approval button into the path.
Escalation is derived from run signals, and every escalation records why.
"""

from __future__ import annotations

from app.config import get_settings
from app.graph.state import RunState
from app.schemas.core import ApprovalRequest, EscalationReason, RiskLevel

ESCALATING_RISK = {RiskLevel.HIGH, RiskLevel.CRITICAL}


def needs_human(state: RunState) -> bool:
    s = get_settings()
    if state.get("risk") in ESCALATING_RISK:
        return True
    if state.get("confidence", 0.0) < s.confidence_auto_approve:
        return True
    return False


def build_request(state: RunState) -> ApprovalRequest:
    s = get_settings()
    adjudication = state.get("adjudication")

    if state.get("confidence", 0.0) < s.confidence_escalate_below:
        reason = EscalationReason.LOW_CONFIDENCE
    elif adjudication and adjudication.disagreement > s.critic_disagreement_threshold:
        reason = EscalationReason.CRITIC_DISAGREEMENT
    elif state.get("replan_count", 0) >= s.max_replan_attempts:
        reason = EscalationReason.REPLAN_EXHAUSTED
    else:
        reason = EscalationReason.LOW_CONFIDENCE

    return ApprovalRequest(
        task_id=state["task_id"],
        reason=reason,
        risk=state.get("risk", RiskLevel.MEDIUM),
        summary=state.get("draft", "")[:2000],
        payload={
            "confidence": state.get("confidence", 0.0),
            "disagreement": adjudication.disagreement if adjudication else None,
            "required_actions": adjudication.required_actions if adjudication else [],
            "errors": state.get("errors", []),
        },
    )

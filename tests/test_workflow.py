"""Control-flow tests: routing, risk and escalation decisions.

These are pure functions over state, so they run without an LLM, a database or a
network. Keeping the control logic testable in isolation is the reason it lives in
its own modules rather than inline in the graph nodes.
"""

from __future__ import annotations

from app.graph.state import new_state
from app.graph.workflow import route_after_review
from app.guardrails.risk_classifier import classify_risk
from app.hitl.escalation import needs_human
from app.schemas.core import Adjudication, AgentRole, Claim, CriticVerdict, RiskLevel


def _adjudication(passed: bool, score: float, disagreement: float) -> Adjudication:
    return Adjudication(
        passed=passed,
        aggregate_score=score,
        disagreement=disagreement,
        verdicts=[CriticVerdict(critic=AgentRole.FACT_CRITIC, score=score, passed=passed)],
    )


def test_failed_review_triggers_replan_within_budget() -> None:
    state = new_state("t1", "q")
    state["adjudication"] = _adjudication(False, 0.4, 0.1)
    assert route_after_review(state) == "replan"
    assert state["replan_count"] == 1


def test_replan_budget_exhaustion_escalates() -> None:
    state = new_state("t2", "q")
    state["replan_count"] = 2
    state["adjudication"] = _adjudication(False, 0.4, 0.1)
    assert route_after_review(state) == "escalate"


def test_high_confidence_pass_finalises() -> None:
    state = new_state("t3", "q")
    state["adjudication"] = _adjudication(True, 0.95, 0.02)
    state["confidence"] = 0.95
    state["risk"] = RiskLevel.LOW
    assert route_after_review(state) == "finalise"


def test_uncited_claim_is_critical_risk() -> None:
    state = new_state("t4", "q")
    state["claims"] = [Claim(text="revenue grew 23%", evidence_ids=[])]
    state["confidence"] = 0.99
    state["adjudication"] = _adjudication(True, 0.99, 0.0)
    assert classify_risk(state) is RiskLevel.CRITICAL


def test_medium_confidence_still_asks_a_human() -> None:
    state = new_state("t5", "q")
    state["confidence"] = 0.7
    state["risk"] = RiskLevel.MEDIUM
    assert needs_human(state) is True

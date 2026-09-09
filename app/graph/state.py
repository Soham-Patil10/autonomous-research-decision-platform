"""The single state object that flows through the LangGraph workflow.

Every node reads it, mutates a slice of it, and returns it. Because the whole run
is one serialisable object, you get failure forensics and trajectory evaluation
almost for free: persist the state after each node and you can replay any run.
"""

from __future__ import annotations

from typing import Any, TypedDict

from app.schemas.core import (
    Adjudication,
    ApprovalRequest,
    Claim,
    Evidence,
    Plan,
    Report,
    RiskLevel,
    TaskStatus,
)


class RunState(TypedDict, total=False):
    # identity
    task_id: str
    question: str
    status: TaskStatus

    # planning
    plan: Plan | None
    replan_count: int

    # execution
    evidence: list[Evidence]
    claims: list[Claim]
    draft: str

    # review
    adjudication: Adjudication | None
    confidence: float
    risk: RiskLevel

    # human-in-the-loop
    approval: ApprovalRequest | None
    human_decision: str | None

    # output + telemetry
    report: Report | None
    trace: list[dict[str, Any]]
    errors: list[str]


def new_state(task_id: str, question: str) -> RunState:
    return RunState(
        task_id=task_id,
        question=question,
        status=TaskStatus.PENDING,
        plan=None,
        replan_count=0,
        evidence=[],
        claims=[],
        draft="",
        adjudication=None,
        confidence=0.0,
        risk=RiskLevel.LOW,
        approval=None,
        human_decision=None,
        report=None,
        trace=[],
        errors=[],
    )

"""The contracts every agent, tool and evaluator speaks in.

Get these right and the rest of the system is plumbing. Everything the platform
produces is a Claim backed by Evidence, carrying a confidence and a provenance
trail — that is what makes the output auditable and evaluable.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def _id() -> str:
    return uuid4().hex[:12]


# --------------------------------------------------------------------------- #
# Tasks and planning
# --------------------------------------------------------------------------- #
class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    AWAITING_HUMAN = "awaiting_human"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRole(str, Enum):
    SUPERVISOR = "supervisor"
    RESEARCH = "research"
    DOCUMENT = "document"
    DATA = "data"
    SYNTHESIS = "synthesis"
    FACT_CRITIC = "fact_critic"
    LOGIC_CRITIC = "logic_critic"
    COMPLETENESS_CRITIC = "completeness_critic"
    ADJUDICATOR = "adjudicator"


class SubTask(BaseModel):
    """One unit of work the supervisor hands to a specialist."""

    id: str = Field(default_factory=_id)
    description: str
    assigned_to: AgentRole
    depends_on: list[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    result: str | None = None
    error: str | None = None


class Plan(BaseModel):
    objective: str
    subtasks: list[SubTask]
    rationale: str = ""
    revision: int = 0


# --------------------------------------------------------------------------- #
# Evidence and claims
# --------------------------------------------------------------------------- #
SourceKind = Literal["document", "web", "database", "memory"]


class Evidence(BaseModel):
    """A retrieved fragment that can support or contradict a claim."""

    id: str = Field(default_factory=_id)
    source_kind: SourceKind
    source_id: str            # doc id, URL, or the SQL that produced it
    locator: str = ""         # page number, section, row range
    content: str
    retrieval_score: float = 0.0
    produced_by: AgentRole | None = None


class Claim(BaseModel):
    """An assertion the system is willing to make, plus what backs it."""

    id: str = Field(default_factory=_id)
    text: str
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    verified: bool | None = None       # set by the fact critic
    verification_note: str = ""


# --------------------------------------------------------------------------- #
# Review
# --------------------------------------------------------------------------- #
class CriticVerdict(BaseModel):
    critic: AgentRole
    score: float                        # 0..1
    passed: bool
    issues: list[str] = Field(default_factory=list)
    reasoning: str = ""


class Adjudication(BaseModel):
    passed: bool
    aggregate_score: float
    disagreement: float                 # spread across critic scores
    verdicts: list[CriticVerdict] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Risk / human-in-the-loop
# --------------------------------------------------------------------------- #
class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationReason(str, Enum):
    LOW_CONFIDENCE = "low_confidence"
    CRITIC_DISAGREEMENT = "critic_disagreement"
    SENSITIVE_TOOL = "sensitive_tool"
    POLICY_BLOCK = "policy_block"
    REPLAN_EXHAUSTED = "replan_exhausted"


class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=_id)
    task_id: str
    reason: EscalationReason
    risk: RiskLevel
    summary: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    decision: Literal["pending", "approved", "rejected", "edited"] = "pending"
    reviewer_note: str = ""


# --------------------------------------------------------------------------- #
# Final output
# --------------------------------------------------------------------------- #
class Report(BaseModel):
    task_id: str
    question: str
    recommendation: str
    summary: str
    claims: list[Claim] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: float = 0.0
    unverified: list[str] = Field(default_factory=list)
    adjudication: Adjudication | None = None
    human_approved: bool = False

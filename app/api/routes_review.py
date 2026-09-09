"""Human-in-the-loop endpoints: the approval queue and its decisions."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.core import ApprovalRequest

router = APIRouter(prefix="/review", tags=["human-in-the-loop"])

# TODO(v1): persist to the `approvals` table; this dict is a placeholder.
_QUEUE: dict[str, ApprovalRequest] = {}


class Decision(BaseModel):
    decision: str            # approved | rejected | edited
    reviewer_note: str = ""
    edited_summary: str | None = None


@router.get("/queue", response_model=list[ApprovalRequest])
async def list_pending() -> list[ApprovalRequest]:
    return [a for a in _QUEUE.values() if a.decision == "pending"]


@router.post("/{approval_id}", response_model=ApprovalRequest)
async def decide(approval_id: str, body: Decision) -> ApprovalRequest:
    approval = _QUEUE.get(approval_id)
    if approval is None:
        raise HTTPException(404, "unknown approval")
    if body.decision not in {"approved", "rejected", "edited"}:
        raise HTTPException(422, "decision must be approved|rejected|edited")

    approval.decision = body.decision  # type: ignore[assignment]
    approval.reviewer_note = body.reviewer_note

    # TODO(v3): resume the suspended LangGraph run from its checkpoint, and write the
    # decision into the failure dataset so a rejection becomes a future test case.
    return approval

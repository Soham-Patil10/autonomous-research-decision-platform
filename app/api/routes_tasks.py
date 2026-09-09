"""Task submission and inspection."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.graph.state import RunState, new_state
from app.graph.workflow import build_graph
from app.observability.trace_store import TraceStore
from app.schemas.core import Report, TaskStatus

router = APIRouter(tags=["tasks"])

# TODO(v1): replace with Postgres + a Celery/arq worker. In-process is fine to start.
_RUNS: dict[str, RunState] = {}
_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


class TaskRequest(BaseModel):
    question: str


class TaskAccepted(BaseModel):
    task_id: str
    status: TaskStatus


async def _execute(task_id: str) -> None:
    state = _RUNS[task_id]
    _RUNS[task_id] = await _get_graph().ainvoke(state)
    TraceStore().save(task_id, _RUNS[task_id].get("trace", []))


@router.post("/tasks", response_model=TaskAccepted, status_code=202)
async def submit_task(body: TaskRequest, background: BackgroundTasks) -> TaskAccepted:
    task_id = uuid4().hex[:12]
    _RUNS[task_id] = new_state(task_id, body.question)
    background.add_task(_execute, task_id)
    return TaskAccepted(task_id=task_id, status=TaskStatus.PENDING)


@router.get("/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    state = _RUNS.get(task_id)
    if state is None:
        raise HTTPException(404, "unknown task")
    return {
        "task_id": task_id,
        "status": state.get("status"),
        "confidence": state.get("confidence"),
        "risk": state.get("risk"),
        "replan_count": state.get("replan_count"),
        "errors": state.get("errors"),
    }


@router.get("/tasks/{task_id}/report", response_model=Report)
async def get_report(task_id: str) -> Report:
    state = _RUNS.get(task_id)
    if state is None or state.get("report") is None:
        raise HTTPException(404, "no report yet")
    return state["report"]


@router.get("/tasks/{task_id}/trace")
async def get_trace(task_id: str) -> list[dict]:
    """The full span trace — this is what powers the failure-forensics view."""
    state = _RUNS.get(task_id)
    if state is not None and state.get("trace"):
        return state["trace"]
    return TraceStore().load(task_id)

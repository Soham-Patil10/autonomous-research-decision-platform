"""Evaluation endpoints: trigger a regression run, read the latest scores."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks

router = APIRouter(prefix="/eval", tags=["evaluation"])

_LATEST: dict = {}


@router.post("/run", status_code=202)
async def trigger_eval(background: BackgroundTasks, label: str = "manual") -> dict:
    from evaluation.run_eval import run_golden_set

    async def _go() -> None:
        _LATEST.update(await run_golden_set(label=label))

    background.add_task(_go)
    return {"status": "started", "label": label}


@router.get("/latest")
async def latest() -> dict:
    return _LATEST or {"status": "no runs yet"}

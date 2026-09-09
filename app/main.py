"""FastAPI entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import api_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO(v1): init_db(), warm the retriever, connect Redis.
    yield


app = FastAPI(
    title="Autonomous Enterprise Research & Decision Intelligence Platform",
    version="0.1.0",
    description=(
        "Multi-agent research and decision support with hybrid RAG, tool guardrails, "
        "human-in-the-loop escalation and continuous evaluation."
    ),
    lifespan=lifespan,
)
app.include_router(api_router)


@app.get("/health")
async def health() -> dict:
    s = get_settings()
    return {
        "status": "ok",
        "llm_provider": s.llm_provider,
        "auto_approve_above": s.confidence_auto_approve,
        "escalate_below": s.confidence_escalate_below,
    }

"""Document search tool — thin adapter over the hybrid retriever."""

from __future__ import annotations

from typing import Any

from app.rag.retriever import HybridRetriever

_retriever: HybridRetriever | None = None


def _get() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever


async def run(query: str, top_k: int = 6) -> list[dict[str, Any]]:
    hits = await _get().search(query, top_k=top_k)
    return [
        {"doc_id": h.doc_id, "text": h.text, "locator": h.locator, "score": h.score}
        for h in hits
    ]

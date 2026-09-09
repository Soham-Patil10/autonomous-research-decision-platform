"""Dense retrieval over Chroma."""

from __future__ import annotations

from app.config import get_settings


class VectorStore:
    """TODO(v1): wrap chromadb.HttpClient; one collection for the corpus,
    a second for semantic memory of past tasks (see app/memory/semantic.py).
    """

    collection_name = "corpus"

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None  # lazy: keeps imports cheap for tests

    async def upsert(self, chunks: list) -> None:
        raise NotImplementedError("TODO(v1)")

    async def search(self, query: str, k: int = 20) -> list:
        raise NotImplementedError("TODO(v1)")

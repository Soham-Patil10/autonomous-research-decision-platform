"""Sparse (lexical) retrieval with BM25.

Keep the index in memory for the MVP corpus; swap for Postgres full-text or
OpenSearch when the corpus outgrows a single process.
"""

from __future__ import annotations


class BM25Store:
    """TODO(v2): build a rank_bm25.BM25Okapi over the same chunks the VectorStore holds.

    Both stores must be fed from one ingestion pass, or fusion compares different corpora.
    """

    def __init__(self) -> None:
        self._index = None
        self._chunks: list = []

    async def build(self, chunks: list) -> None:
        raise NotImplementedError("TODO(v2)")

    async def search(self, query: str, k: int = 20) -> list:
        raise NotImplementedError("TODO(v2)")

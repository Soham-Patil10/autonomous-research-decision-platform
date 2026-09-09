"""Hybrid retriever — the front door to the whole RAG subsystem.

    query -> [dense, sparse] -> RRF fusion -> cross-encoder rerank -> top-k

Dense retrieval finds paraphrase; BM25 finds exact tokens (ticker symbols, statute
numbers, product codes). Analytical corpora need both, and fusing them beats either
alone. The reranker then buys precision back after fusion widens recall.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings
from app.rag.bm25_store import BM25Store
from app.rag.fusion import reciprocal_rank_fusion
from app.rag.reranker import CrossEncoderReranker
from app.rag.vector_store import VectorStore


@dataclass
class Retrieved:
    doc_id: str
    text: str
    locator: str
    score: float


class HybridRetriever:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.dense = VectorStore()
        self.sparse = BM25Store()
        self.reranker = CrossEncoderReranker()

    async def search(self, query: str, top_k: int | None = None) -> list[Retrieved]:
        s = self.settings
        dense_hits = await self.dense.search(query, k=s.dense_top_k)
        sparse_hits = await self.sparse.search(query, k=s.sparse_top_k)

        fused = reciprocal_rank_fusion([dense_hits, sparse_hits], k=s.rrf_k)
        return await self.reranker.rerank(query, fused, top_k=top_k or s.rerank_top_k)

    async def multi_query_search(self, query: str, variants: list[str]) -> list[Retrieved]:
        """TODO(v2): run the original query plus LLM-generated paraphrases, fuse all runs.

        Cheap and reliably lifts recall on questions phrased differently from the corpus.
        """
        raise NotImplementedError

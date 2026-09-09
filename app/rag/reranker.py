"""Cross-encoder reranking.

Bi-encoders (what the vector store uses) embed query and document separately, which
is fast but lossy. A cross-encoder reads the pair together and scores relevance
directly - far more accurate, far slower. So: retrieve wide, rerank narrow.
"""

from __future__ import annotations


class CrossEncoderReranker:
    """TODO(v2): sentence_transformers.CrossEncoder('BAAI/bge-reranker-base').

    Measure it. Rerank should visibly move retrieval precision@k on the golden set;
    if it does not, your chunking is the bottleneck, not your ranking.
    """

    model_name = "BAAI/bge-reranker-base"

    def __init__(self) -> None:
        self._model = None

    async def rerank(self, query: str, candidates: list, top_k: int = 6) -> list:
        if self._model is None:
            return candidates[:top_k]  # graceful passthrough until the model is wired
        raise NotImplementedError("TODO(v2)")

"""Reciprocal Rank Fusion.

Combines ranked lists using position rather than score, so a cosine similarity and
a BM25 score never have to be made commensurable. That property is why RRF is the
default fusion choice for hybrid search.

    score(d) = sum over lists of  1 / (k + rank(d))
"""

from __future__ import annotations

from typing import Any, Iterable


def reciprocal_rank_fusion(
    ranked_lists: Iterable[list[Any]],
    k: int = 60,
    id_attr: str = "doc_id",
) -> list[Any]:
    """Fuse ranked lists. Items are matched by `id_attr`; first occurrence wins.

    `k` damps the influence of top ranks; 60 is the value from the original paper
    and a sane default. Lower it to trust rank-1 hits more.
    """
    scores: dict[str, float] = {}
    seen: dict[str, Any] = {}

    for ranked in ranked_lists:
        for rank, item in enumerate(ranked, start=1):
            key = getattr(item, id_attr, None) or item[id_attr]
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            seen.setdefault(key, item)

    order = sorted(scores, key=lambda key: scores[key], reverse=True)
    return [seen[key] for key in order]

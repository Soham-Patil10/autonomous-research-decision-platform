"""RAG metrics.

Two of these are deterministic and two need a judge model. Implement the
deterministic ones first — they are cheap, stable, and catch most regressions.
"""

from __future__ import annotations


# ---- deterministic -------------------------------------------------------- #
def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    top = retrieved_ids[:k]
    if not top:
        return 0.0
    return sum(1 for d in top if d in relevant_ids) / len(top)


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if not relevant_ids:
        return 1.0
    top = set(retrieved_ids[:k])
    return len(top & relevant_ids) / len(relevant_ids)


def mrr(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    """Mean reciprocal rank — how far down the list the first good hit sits."""
    for rank, doc in enumerate(retrieved_ids, start=1):
        if doc in relevant_ids:
            return 1.0 / rank
    return 0.0


def citation_coverage(claims: list) -> float:
    """Fraction of claims that carry at least one citation. Floor, not ceiling."""
    if not claims:
        return 0.0
    return sum(1 for c in claims if c.evidence_ids) / len(claims)


# ---- judged --------------------------------------------------------------- #
async def faithfulness(claims: list, evidence: list) -> float:
    """TODO(v3): fraction of claims entailed by their *own* cited evidence.

    Judge each claim against only its citations, never the whole context — otherwise
    you are measuring whether the corpus contains the answer, not whether the system
    used it.
    """
    raise NotImplementedError


async def answer_relevance(question: str, answer: str) -> float:
    """TODO(v3): does the answer address the question asked, independent of truth?"""
    raise NotImplementedError

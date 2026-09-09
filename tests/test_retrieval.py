"""Retrieval tests that need no models — fusion maths and metric maths."""

from __future__ import annotations

from dataclasses import dataclass

from app.rag.fusion import reciprocal_rank_fusion
from evaluation.metrics.rag import mrr, precision_at_k, recall_at_k


@dataclass
class Hit:
    doc_id: str


def test_rrf_rewards_agreement_across_lists() -> None:
    dense = [Hit("a"), Hit("b"), Hit("c")]
    sparse = [Hit("z"), Hit("b"), Hit("y")]
    fused = [h.doc_id for h in reciprocal_rank_fusion([dense, sparse])]
    # "b" appears in both lists, so it outranks "a" and "z" which each top one list only.
    assert fused[0] == "b"


def test_rrf_deduplicates() -> None:
    fused = reciprocal_rank_fusion([[Hit("a")], [Hit("a")]])
    assert len(fused) == 1


def test_precision_and_recall() -> None:
    retrieved = ["a", "b", "x", "y"]
    relevant = {"a", "b", "c"}
    assert precision_at_k(retrieved, relevant, 2) == 1.0
    assert recall_at_k(retrieved, relevant, 4) == 2 / 3


def test_mrr_uses_first_relevant_rank() -> None:
    assert mrr(["x", "y", "a"], {"a"}) == 1 / 3
    assert mrr(["x"], {"a"}) == 0.0

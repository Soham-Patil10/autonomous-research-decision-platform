"""Regression runner: run the golden set, score every layer, compare to the last run.

Usage:  python -m evaluation.run_eval [--label v2-reranker]

Treat this like a test suite you can lose. A change that drops faithfulness by 4
points is a regression even if the demo still looks impressive.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.graph.state import new_state
from app.graph.workflow import build_graph
from evaluation.metrics import agent as agent_metrics
from evaluation.metrics import rag as rag_metrics
from evaluation.metrics import system as system_metrics

GOLDEN = Path(__file__).parent / "datasets" / "golden_set.jsonl"
RESULTS = Path(__file__).parent / "results"


def load_golden() -> list[dict[str, Any]]:
    return [json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines() if line]


async def run_golden_set(label: str = "manual") -> dict[str, Any]:
    graph = build_graph()
    cases = load_golden()
    per_case: list[dict[str, Any]] = []

    for case in cases:
        state = await graph.ainvoke(new_state(case["id"], case["question"]))
        trace = state.get("trace", [])

        per_case.append(
            {
                "id": case["id"],
                "type": case["type"],
                "status": str(state.get("status")),
                "confidence": state.get("confidence", 0.0),
                "citation_coverage": rag_metrics.citation_coverage(state.get("claims", [])),
                "tool_selection": agent_metrics.tool_selection_accuracy(
                    trace, case.get("expected_tool")
                ),
                "tool_success": agent_metrics.tool_success_rate(trace),
                "latency_ms": system_metrics.latency_ms(trace),
                "stages": system_metrics.stage_breakdown(trace),
                # TODO(v3): faithfulness + answer_relevance once the judge is wired.
            }
        )

    summary = {
        "label": label,
        "timestamp": datetime.utcnow().isoformat(),
        "n_cases": len(per_case),
        "mean_confidence": _mean(per_case, "confidence"),
        "mean_citation_coverage": _mean(per_case, "citation_coverage"),
        "tool_selection_accuracy": _mean(per_case, "tool_selection"),
        "tool_success_rate": _mean(per_case, "tool_success"),
        "latency_p50_p95": system_metrics.percentiles([c["latency_ms"] for c in per_case]),
        "cases": per_case,
    }

    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / f"{label}-{datetime.utcnow():%Y%m%d-%H%M%S}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    return summary


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    values = [r[key] for r in rows if isinstance(r.get(key), (int, float))]
    return sum(values) / len(values) if values else 0.0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="manual")
    args = parser.parse_args()
    asyncio.run(run_golden_set(label=args.label))

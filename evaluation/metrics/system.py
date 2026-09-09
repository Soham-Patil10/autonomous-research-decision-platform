"""System metrics: latency, tokens, cost, and where the time actually goes."""

from __future__ import annotations

import statistics
from typing import Any

# USD per 1M tokens. Keep in sync with the models named in .env.
PRICING: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-opus-5": (15.00, 75.00),
}


def latency_ms(trace: list[dict[str, Any]]) -> float:
    return sum(s.get("duration_ms", 0.0) for s in trace)


def stage_breakdown(trace: list[dict[str, Any]]) -> dict[str, float]:
    """Time per stage — this is what tells you whether to optimise the LLM or the retriever."""
    out: dict[str, float] = {}
    for s in trace:
        stage = s["name"].split(".")[0]
        out[stage] = out.get(stage, 0.0) + s.get("duration_ms", 0.0)
    return out


def cost_usd(calls: list[dict[str, Any]]) -> float:
    """calls: [{"model", "input_tokens", "output_tokens"}, ...]"""
    total = 0.0
    for c in calls:
        rate_in, rate_out = PRICING.get(c["model"], (0.0, 0.0))
        total += c["input_tokens"] / 1e6 * rate_in + c["output_tokens"] / 1e6 * rate_out
    return total


def percentiles(values: list[float]) -> dict[str, float]:
    if not values:
        return {"p50": 0.0, "p95": 0.0}
    ordered = sorted(values)
    return {
        "p50": statistics.median(ordered),
        "p95": ordered[max(0, int(len(ordered) * 0.95) - 1)],
    }

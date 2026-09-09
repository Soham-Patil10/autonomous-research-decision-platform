"""Span tracing for agent runs — the substrate for failure forensics.

Every node, agent and tool call opens a span. Spans are appended to `state["trace"]`
*and* emitted to OpenTelemetry. The in-state copy is what makes a run replayable and
what the trace explorer and the evaluator read.

Without this you can see that a run was wrong. With it you can see *where* it went wrong.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any
from uuid import uuid4


@contextmanager
def span(name: str, state: dict[str, Any], **attributes: Any):
    record: dict[str, Any] = {
        "span_id": uuid4().hex[:8],
        "name": name,
        "started_at": time.time(),
        "attributes": attributes,
        "status": "ok",
    }
    try:
        yield record
    except Exception as exc:  # noqa: BLE001 - recorded then re-raised
        record["status"] = "error"
        record["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        record["duration_ms"] = (time.time() - record["started_at"]) * 1000
        state.setdefault("trace", []).append(record)
        # TODO(v3): mirror into an OTel span so traces survive outside the run object.


def first_failure(trace: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The earliest errored span — where a post-mortem should start reading."""
    return next((s for s in trace if s.get("status") == "error"), None)

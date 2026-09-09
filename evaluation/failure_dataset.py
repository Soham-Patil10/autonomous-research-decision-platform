"""The learning loop: every failure becomes a permanent test case.

    production run -> failure or human rejection -> recorded here
                   -> promoted into the golden set -> regression-tested forever

This is the part that turns a demo into a system that gets better. It is also the
most impressive thing to be able to show: a graph of the golden set growing while
the failure rate falls.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

FAILURES = Path(__file__).parent / "datasets" / "failures.jsonl"


@dataclass
class FailureCase:
    task_id: str
    question: str
    failing_stage: str          # from observability.tracing.first_failure
    failure_type: str           # unsupported_claim | wrong_retrieval | bad_sql | bad_plan | ...
    bad_output: str
    human_correction: str = ""
    evidence_note: str = ""
    promoted_to_golden: bool = False
    recorded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


def record(case: FailureCase) -> None:
    FAILURES.parent.mkdir(parents=True, exist_ok=True)
    with FAILURES.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(case)) + "\n")


def load() -> list[FailureCase]:
    if not FAILURES.exists():
        return []
    return [FailureCase(**json.loads(line)) for line in FAILURES.read_text("utf-8").splitlines() if line]


def promote_to_golden(case: FailureCase) -> dict:
    """TODO(v3): append to golden_set.jsonl with the human correction as expected output."""
    return {
        "id": f"f-{case.task_id}",
        "question": case.question,
        "type": "regression",
        "origin_failure": case.failure_type,
        "expected_answer_contains": [case.human_correction] if case.human_correction else [],
    }

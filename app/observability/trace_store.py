"""Persist and query run traces.

Kept separate from tracing.py so the hot path never depends on storage being up:
a run that cannot write its trace should still finish.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TRACE_DIR = Path("traces")


class TraceStore:
    """TODO(v3): move to Postgres. Files are fine for the MVP and easy to diff."""

    def __init__(self, directory: Path = TRACE_DIR) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, task_id: str, trace: list[dict[str, Any]]) -> Path:
        path = self.directory / f"{task_id}.json"
        path.write_text(json.dumps(trace, indent=2, default=str), encoding="utf-8")
        return path

    def load(self, task_id: str) -> list[dict[str, Any]]:
        path = self.directory / f"{task_id}.json"
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

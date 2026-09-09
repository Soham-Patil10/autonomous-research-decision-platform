"""Working memory (Redis): per-run scratch space and tool-result cache."""

from __future__ import annotations

import json
from typing import Any

from app.config import get_settings

TTL_SECONDS = 60 * 60


class WorkingMemory:
    """TODO(v1): back with redis.asyncio. Namespace every key by task_id."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._local: dict[str, str] = {}  # in-process fallback so tests need no Redis

    async def set(self, task_id: str, key: str, value: Any) -> None:
        self._local[f"{task_id}:{key}"] = json.dumps(value, default=str)

    async def get(self, task_id: str, key: str) -> Any | None:
        raw = self._local.get(f"{task_id}:{key}")
        return json.loads(raw) if raw else None

"""Provider-agnostic LLM client.

One place that talks to a model API. Everything else in the codebase calls this, so
retries, token accounting, caching and tracing are implemented exactly once.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import get_settings


@dataclass
class LLMResponse:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: list[dict[str, Any]] | None = None
    latency_ms: float = 0.0


class LLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def complete(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """TODO(v1): implement for Anthropic (and OpenAI behind the same signature).

        Worth building in from the start, because retrofitting them is painful:
          - record input/output tokens on every call for the cost metric
          - prompt-cache the long system prompts and the schema block
          - retry on transient errors with jittered backoff
          - emit a trace span (see app/observability/tracing.py)
        """
        raise NotImplementedError("TODO(v1)")

    async def structured(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, str]],
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Constrained JSON output. Use this for plans and verdicts — never parse prose."""
        raise NotImplementedError("TODO(v1)")

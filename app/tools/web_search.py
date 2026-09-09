"""Web search tool (Tavily by default).

Returns a normalised shape so the Research agent never learns which provider is
behind it: {"url", "title", "content", "score"}.
"""

from __future__ import annotations

from typing import Any

from app.config import get_settings


async def run(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """TODO(v1): call Tavily; cache by (query, max_results) in Redis for the task's lifetime.

    Caching matters more than it looks: re-plans repeat queries, and an uncached
    re-plan doubles both latency and spend.
    """
    _ = get_settings().tavily_api_key
    return [
        {
            "url": "https://example.invalid/stub",
            "title": "stub result",
            "content": f"stub web result for: {query}",
            "score": 0.0,
        }
    ][:max_results]

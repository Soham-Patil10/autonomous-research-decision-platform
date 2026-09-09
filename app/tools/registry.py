"""Tool registry: the only place a capability enters the system.

Tools are registered with a name, a JSON schema and a handler. Agents ask for tools by
name; the policy engine decides whether they get them. Adding a tool must be a
deliberate, reviewable act — which is why registration is explicit, not by decorator scan.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from app.tools import doc_search, sql_tool, web_search


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Awaitable[Any]]


class ToolRegistry:
    _tools: dict[str, Tool] = {}

    def __init__(self) -> None:
        if not ToolRegistry._tools:
            self._register_defaults()

    # ----------------------------------------------------------------- #
    @classmethod
    def register(cls, tool: Tool) -> None:
        cls._tools[tool.name] = tool

    async def invoke(self, name: str, **kwargs: Any) -> Any:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"unknown tool: {name}")
        return await tool.handler(**kwargs)

    def schemas(self, names: list[str]) -> list[dict[str, Any]]:
        """Tool definitions in the shape the LLM's tool-use API expects."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
            }
            for n in names
            if (t := self._tools.get(n))
        ]

    # ----------------------------------------------------------------- #
    def _register_defaults(self) -> None:
        self.register(
            Tool(
                name="web_search",
                description="Search the public web for current market, competitor and news data.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "max_results": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
                handler=web_search.run,
            )
        )
        self.register(
            Tool(
                name="doc_search",
                description="Hybrid search over the company's private document corpus.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "top_k": {"type": "integer", "default": 6},
                    },
                    "required": ["query"],
                },
                handler=doc_search.run,
            )
        )
        self.register(
            Tool(
                name="sql_schema",
                description="Return the analytics database schema (tables, columns, types).",
                parameters={"type": "object", "properties": {}},
                handler=sql_tool.schema,
            )
        )
        self.register(
            Tool(
                name="sql_query",
                description="Execute a single read-only SELECT against the analytics database.",
                parameters={
                    "type": "object",
                    "properties": {"sql": {"type": "string"}},
                    "required": ["sql"],
                },
                handler=sql_tool.query,
            )
        )

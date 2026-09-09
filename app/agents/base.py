"""Shared behaviour for every specialist agent.

An agent here is deliberately thin: it owns a role, a prompt, a set of tools it is
*allowed* to call, and a `run()` that returns Evidence. All safety decisions are
delegated to the guardrail layer so no agent can grant itself a capability.
"""

from __future__ import annotations

import abc
from typing import Any

from app.graph.state import RunState
from app.guardrails.policy import PolicyEngine
from app.llm.router import LLMRouter
from app.schemas.core import AgentRole, Evidence, SubTask
from app.tools.registry import ToolRegistry


class BaseAgent(abc.ABC):
    role: AgentRole
    system_prompt: str = ""

    def __init__(self) -> None:
        self.llm = LLMRouter()
        self.tools = ToolRegistry()
        self.policy = PolicyEngine()

    # ----------------------------------------------------------------- #
    async def call_tool(self, name: str, **kwargs: Any) -> Any:
        """Every tool call passes through the policy engine. No exceptions."""
        decision = self.policy.check(agent=self.role, tool=name, arguments=kwargs)
        if not decision.allowed:
            raise PermissionError(f"{self.role.value} may not call {name}: {decision.reason}")
        if decision.requires_approval:
            # TODO(v3): raise a HumanApprovalRequired signal the graph can interrupt on.
            raise PermissionError(f"{name} requires human approval: {decision.reason}")
        return await self.tools.invoke(name, **kwargs)

    @abc.abstractmethod
    async def run(self, subtask: SubTask, state: RunState) -> list[Evidence]:
        """Execute one subtask and return the evidence gathered."""

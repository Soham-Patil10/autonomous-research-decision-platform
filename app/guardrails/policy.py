"""Tool-permission policy engine.

Every tool call in the system funnels through `PolicyEngine.check`. Deny-by-default:
if a tool is not explicitly granted to an agent's role, it is refused. This is the
difference between "my agent has tools" and "my agent has *bounded* tools".
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.schemas.core import AgentRole

POLICY_PATH = Path(__file__).with_name("policies.yaml")


@dataclass
class PolicyDecision:
    allowed: bool
    requires_approval: bool = False
    reason: str = ""


class PolicyEngine:
    def __init__(self, policy_path: Path = POLICY_PATH) -> None:
        self._policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
        self._call_counts: dict[tuple[str, str], int] = {}

    # ----------------------------------------------------------------- #
    def check(self, agent: AgentRole, tool: str, arguments: dict[str, Any]) -> PolicyDecision:
        agents = self._policy.get("agents", {})
        rules = agents.get(agent.value)

        if rules is None:
            return PolicyDecision(False, reason=f"role {agent.value} has no policy entry")

        if tool not in (rules.get("allowed_tools") or []):
            return PolicyDecision(False, reason=f"tool {tool} not granted to {agent.value}")

        if tool in (self._policy.get("sensitive_tools") or []):
            return PolicyDecision(True, requires_approval=True, reason="sensitive tool")

        limit = (rules.get("limits") or {}).get(tool, {})
        key = (agent.value, tool)
        self._call_counts[key] = self._call_counts.get(key, 0) + 1
        max_calls = limit.get("max_calls")
        if max_calls is not None and self._call_counts[key] > max_calls:
            return PolicyDecision(False, reason=f"{tool} call budget of {max_calls} exhausted")

        return PolicyDecision(True)

    def limits_for(self, agent: AgentRole, tool: str) -> dict[str, Any]:
        rules = self._policy.get("agents", {}).get(agent.value, {})
        return (rules.get("limits") or {}).get(tool, {})

"""Agent-trajectory metrics.

Grading only the final answer hides where a system is fragile. These metrics read
the trace, so they tell you *which* stage to fix — which is the whole reason the
tracing layer exists.
"""

from __future__ import annotations

from typing import Any


def tool_selection_accuracy(trace: list[dict[str, Any]], expected_tool: str | None) -> float:
    """Did the run use the tool the task actually required?"""
    if expected_tool is None:
        return 1.0
    used = {s["name"].split(".")[-1] for s in trace}
    return 1.0 if expected_tool in used else 0.0


def plan_role_coverage(plan: Any, expected_roles: list[str]) -> float:
    """Fraction of the roles the question demanded that the plan actually engaged."""
    if not expected_roles:
        return 1.0
    assigned = {st.assigned_to.value for st in plan.subtasks}
    return len(set(expected_roles) & assigned) / len(set(expected_roles))


def tool_success_rate(trace: list[dict[str, Any]]) -> float:
    calls = [s for s in trace if s["name"].startswith(("specialist.", "tool."))]
    if not calls:
        return 1.0
    return sum(1 for s in calls if s.get("status") == "ok") / len(calls)


def recovery_rate(states: list[dict[str, Any]]) -> float:
    """Of the runs that hit a critic failure, how many recovered without a human?"""
    failed = [s for s in states if s.get("replan_count", 0) > 0]
    if not failed:
        return 1.0
    recovered = [s for s in failed if s.get("status") == "completed" and not s.get("approval")]
    return len(recovered) / len(failed)


def escalation_rate(states: list[dict[str, Any]]) -> float:
    """Not a metric to minimise blindly. Too low means the system is overconfident."""
    if not states:
        return 0.0
    return sum(1 for s in states if s.get("approval") is not None) / len(states)

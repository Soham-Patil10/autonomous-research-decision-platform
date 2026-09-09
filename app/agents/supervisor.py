"""The supervisor: turns a fuzzy business question into an executable plan.

This is the agentic core. It does not answer anything itself — it decides what
work exists, who does it, and in what order. When a review fails it re-plans with
the failure reasons in context rather than blindly retrying.
"""

from __future__ import annotations

from app.llm.router import LLMRouter, Complexity
from app.schemas.core import AgentRole, Plan, SubTask

PLANNER_PROMPT = """You are the supervisor of a research team. Decompose the user's
question into the smallest set of subtasks that, together, would let an analyst answer
it with evidence.

Available specialists:
- research  : searches the public web for market data, news, competitor information
- document  : searches the company's private document corpus (reports, filings, policies)
- data      : queries the company's analytics database with read-only SQL

Rules:
- Every subtask names exactly one specialist.
- Use depends_on when a subtask genuinely needs another's output.
- Prefer 3-6 subtasks. Do not invent work that no specialist can perform.
- If prior attempts failed, address the stated reasons explicitly.

Return JSON: {"rationale": str, "subtasks": [{"description": str,
"assigned_to": "research|document|data", "depends_on": [int]}]}
"""


class SupervisorAgent:
    role = AgentRole.SUPERVISOR

    def __init__(self) -> None:
        self.llm = LLMRouter()

    async def plan(self, question: str, prior_failures: list[str] | None = None) -> Plan:
        """Produce a Plan for the question.

        TODO(v1): call the LLM with PLANNER_PROMPT, parse the JSON into SubTasks,
        and validate that every assigned_to maps to a registered specialist.
        The stub below keeps the graph runnable end-to-end before the LLM is wired.
        """
        _ = self.llm.pick(Complexity.HIGH)
        _ = prior_failures or []

        return Plan(
            objective=question,
            rationale="stub plan - replace with LLM-generated decomposition",
            subtasks=[
                SubTask(
                    description=f"Search the web for market context on: {question}",
                    assigned_to=AgentRole.RESEARCH,
                ),
                SubTask(
                    description=f"Retrieve internal documents relevant to: {question}",
                    assigned_to=AgentRole.DOCUMENT,
                ),
                SubTask(
                    description="Quantify the company's recent performance in the target region",
                    assigned_to=AgentRole.DATA,
                ),
            ],
        )

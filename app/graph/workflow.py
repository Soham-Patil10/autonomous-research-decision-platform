"""LangGraph wiring: the control flow of the whole platform lives in this one file.

    plan -> execute -> fuse -> review -> gate -> (synthesise | replan | escalate)

Keeping the topology in a single readable place is deliberate: it is the artefact
you point at in an interview when asked "how does your system decide what to do?".
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agents import critics as critic_pkg
from app.agents.data_agent import DataAgent
from app.agents.document_agent import DocumentAgent
from app.agents.research_agent import ResearchAgent
from app.agents.supervisor import SupervisorAgent
from app.agents.synthesis_agent import SynthesisAgent
from app.config import get_settings
from app.graph.state import RunState
from app.guardrails.risk_classifier import classify_risk
from app.hitl.escalation import needs_human
from app.observability.tracing import span
from app.schemas.core import AgentRole, TaskStatus

SPECIALISTS = {
    AgentRole.RESEARCH: ResearchAgent,
    AgentRole.DOCUMENT: DocumentAgent,
    AgentRole.DATA: DataAgent,
}


# --------------------------------------------------------------------------- #
# Nodes
# --------------------------------------------------------------------------- #
async def node_plan(state: RunState) -> RunState:
    with span("supervisor.plan", state):
        state["status"] = TaskStatus.PLANNING
        state["plan"] = await SupervisorAgent().plan(
            question=state["question"],
            prior_failures=state.get("errors", []),
        )
    return state


async def node_execute(state: RunState) -> RunState:
    """Run the plan's subtasks, respecting `depends_on` ordering.

    TODO(v1): topologically sort and run independent subtasks concurrently.
    """
    state["status"] = TaskStatus.EXECUTING
    plan = state["plan"]
    assert plan is not None

    for subtask in plan.subtasks:
        agent_cls = SPECIALISTS.get(subtask.assigned_to)
        if agent_cls is None:
            state["errors"].append(f"no specialist for role {subtask.assigned_to}")
            continue
        with span(f"specialist.{subtask.assigned_to.value}", state, subtask=subtask.id):
            try:
                evidence = await agent_cls().run(subtask, state)
                state["evidence"].extend(evidence)
                subtask.status = TaskStatus.COMPLETED
            except Exception as exc:  # noqa: BLE001 - surfaced to the trace, not swallowed
                subtask.status = TaskStatus.FAILED
                subtask.error = str(exc)
                state["errors"].append(f"{subtask.id}: {exc}")
    return state


async def node_fuse(state: RunState) -> RunState:
    """Turn raw evidence into a draft answer with claim-level attribution."""
    with span("synthesis.draft", state):
        draft, claims = await SynthesisAgent().draft(state)
        state["draft"] = draft
        state["claims"] = claims
    return state


async def node_review(state: RunState) -> RunState:
    with span("critics.panel", state):
        state["status"] = TaskStatus.REVIEWING
        state["adjudication"] = await critic_pkg.run_panel(state)
        state["confidence"] = state["adjudication"].aggregate_score
        state["risk"] = classify_risk(state)
    return state


async def node_escalate(state: RunState) -> RunState:
    with span("hitl.escalate", state):
        state["status"] = TaskStatus.AWAITING_HUMAN
        # TODO(v1): persist the ApprovalRequest and interrupt the graph here so the
        # Streamlit console can resolve it. LangGraph checkpointing makes this resumable.
    return state


async def node_finalise(state: RunState) -> RunState:
    with span("synthesis.finalise", state):
        state["report"] = await SynthesisAgent().finalise(state)
        state["status"] = TaskStatus.COMPLETED
    return state


# --------------------------------------------------------------------------- #
# Edges
# --------------------------------------------------------------------------- #
def route_after_review(state: RunState) -> str:
    settings = get_settings()
    adjudication = state["adjudication"]

    if adjudication is not None and not adjudication.passed:
        if state["replan_count"] < settings.max_replan_attempts:
            state["replan_count"] += 1
            return "replan"
        return "escalate"

    if needs_human(state):
        return "escalate"
    return "finalise"


def build_graph():
    g = StateGraph(RunState)
    g.add_node("plan", node_plan)
    g.add_node("execute", node_execute)
    g.add_node("fuse", node_fuse)
    g.add_node("review", node_review)
    g.add_node("escalate", node_escalate)
    g.add_node("finalise", node_finalise)

    g.set_entry_point("plan")
    g.add_edge("plan", "execute")
    g.add_edge("execute", "fuse")
    g.add_edge("fuse", "review")
    g.add_conditional_edges(
        "review",
        route_after_review,
        {"replan": "plan", "escalate": "escalate", "finalise": "finalise"},
    )
    g.add_edge("escalate", "finalise")
    g.add_edge("finalise", END)

    # TODO(v3): attach a checkpointer (Postgres) so escalations can suspend and resume.
    return g.compile()

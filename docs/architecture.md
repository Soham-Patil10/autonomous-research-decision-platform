# Architecture

## Design principles

1. **The LLM proposes, the system disposes.** Agents emit intentions (a plan, a SQL
   string, a claim). Deterministic code decides whether they execute. Every safety
   property lives in code you can unit-test, never in a prompt.
2. **Nothing is asserted without provenance.** The atomic output is a `Claim` with
   `evidence_ids`. A claim with no evidence is a defect, not a stylistic choice.
3. **Confidence is computed, never asked for.** Models are poorly calibrated when asked
   "how confident are you?". Confidence here is derived from critic agreement, citation
   coverage and tool success.
4. **The trace is a first-class artefact.** Failure forensics and trajectory evaluation
   both read the same span log the run produced.
5. **Escalation is a signal, not a button.** A human is interrupted because measurable
   run properties crossed a threshold.

## Layers

| Layer | Modules | Responsibility |
|---|---|---|
| Interface | `app/api`, `ui` | submit, poll, approve, inspect |
| Orchestration | `app/graph` | the state machine and its routing rules |
| Reasoning | `app/agents` | supervisor, specialists, critic panel, adjudicator |
| Capability | `app/tools` | the only place a tool enters the system |
| Safety | `app/guardrails`, `app/hitl` | policy engine, SQL guard, risk, escalation |
| Grounding | `app/rag` | hybrid retrieval, fusion, reranking |
| State | `app/memory`, `app/db` | working / persistent / semantic memory |
| Telemetry | `app/observability` | spans, trace store |
| Assurance | `evaluation` | golden set, metrics, failure dataset |

## Control flow

```
plan ──► execute ──► fuse ──► review ──┬── pass, low risk ──► finalise
 ▲                                     │
 │                                     ├── fail, budget left ──► plan (re-plan)
 └─────────────────────────────────────┘
                                       └── fail/uncertain ──► escalate ──► finalise
```

Routing lives in `route_after_review` in [app/graph/workflow.py](../app/graph/workflow.py)
and is unit-tested in `tests/test_workflow.py` without touching an LLM.

## The four safety layers on SQL

| Layer | Where | Defeated by |
|---|---|---|
| AST is a single SELECT | `sql_guard.validate` | a parser bug |
| Table allowlist | `sql_guard.validate` | a query that stays in-bounds |
| Forced LIMIT | `sql_guard._enforce_limit` | an expensive in-bounds query |
| Read-only role + read-only txn + statement timeout | Postgres | nothing in the app |

The first three produce readable errors that feed the re-plan loop. The last one is
the one that actually protects the database. You need both kinds.

## Confidence formula

```
confidence = mean(critic scores)
             with a hard veto if the fact critic fails
             and CRITICAL risk if any claim is uncited
```

Kept deliberately simple and deterministic — see `Adjudicator.adjudicate` and
`classify_risk`. Calibrate the thresholds against the golden set rather than by feel.

## What to build for real, and in what order

The scaffolding is complete; the intelligence is stubbed. Follow the `TODO(vN)`
markers — they are ordered so the system is runnable end-to-end at every step:

- `TODO(v1)` — LLM client, supervisor planning, dense retrieval, draft synthesis
- `TODO(v2)` — BM25, reranking, text-to-SQL generation, multi-query retrieval
- `TODO(v3)` — real critics, checkpointed escalation, judged metrics, failure loop
- `TODO(v4)` — model routing measurement, cost dashboards, caching

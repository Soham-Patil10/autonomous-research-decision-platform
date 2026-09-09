# Roadmap

Four phases. Each one ends with a system that runs end-to-end and a set of numbers.
Do not start a phase before the previous one has numbers.

---

## V1 — MVP: it works end to end
*Foundation: Project 15's orchestration skeleton*

| Build | Files |
|---|---|
| LLM client (Anthropic), token accounting, retries | `app/llm/client.py` |
| Supervisor produces a real plan via structured output | `app/agents/supervisor.py` |
| Web search tool (Tavily) + Redis caching | `app/tools/web_search.py` |
| Chunking + embeddings + Chroma dense retrieval | `app/rag/{chunking,embeddings,vector_store}.py` |
| Text-to-SQL generation against a restricted schema | `app/agents/data_agent.py` |
| Synthesis producing claims with citations | `app/agents/synthesis_agent.py` |
| One reviewer, one re-plan loop | `app/agents/critics/fact_critic.py` |
| Streamlit console | `ui/streamlit_app.py` |

**Exit criteria:** the market-entry question returns a cited report; the guardrail tests pass.

---

## V2 — Grounding: the answers become trustworthy
*Upgrades borrowed from Projects 6 and 8*

| Build | Files |
|---|---|
| BM25 index fed from the same ingestion pass | `app/rag/bm25_store.py` |
| RRF fusion wired into the retriever | `app/rag/fusion.py` |
| Cross-encoder reranking | `app/rag/reranker.py` |
| Multi-query retrieval | `app/rag/retriever.py` |
| Claim-level citation verification | `app/agents/critics/fact_critic.py` |
| Real SQL execution on the read-only role + result sanity checks | `app/tools/sql_tool.py` |
| Computed confidence replacing the stub | `app/agents/critics/adjudicator.py` |

**Exit criteria:** retrieval precision@6 and citation coverage measured before and
after reranking, with the delta written down.

---

## V3 — Assurance: the system knows when it is wrong
*Upgrades borrowed from Projects 5 and 3*

| Build | Files |
|---|---|
| Three independent critics running concurrently | `app/agents/critics/` |
| Adjudication with veto + disagreement measure | `app/agents/critics/adjudicator.py` |
| LangGraph checkpointing so escalations suspend and resume | `app/graph/workflow.py` |
| Approval queue persisted to Postgres | `app/api/routes_review.py`, `app/db/models.py` |
| OTel spans mirrored out of the run object | `app/observability/tracing.py` |
| Trace explorer with first-failure highlighting | `ui/streamlit_app.py` |
| Judged metrics: faithfulness, answer relevance | `evaluation/metrics/rag.py` |
| Failure dataset + promotion into the golden set | `evaluation/failure_dataset.py` |
| Semantic memory consulted during planning | `app/memory/semantic.py` |

**Exit criteria:** a rejected run becomes a golden-set case automatically, and the
regression runner shows the fix without breaking anything else.

---

## V4 — Efficiency: it gets cheaper without getting worse
*Upgrade borrowed from Project 2*

| Build | Files |
|---|---|
| Complexity classification driving model choice | `app/llm/router.py` |
| Escalate-on-failed-self-check retry ladder | `app/llm/router.py` |
| Per-task cost and latency accounting | `evaluation/metrics/system.py` |
| Prompt caching on long system prompts and schema blocks | `app/llm/client.py` |

**Exit criteria:** one sentence with two real numbers — cost reduction *and* the
evaluation score that stayed flat while achieving it.

---

## The claim this roadmap is built to earn

> Engineered an autonomous multi-agent research platform that decomposes complex tasks
> across specialised LLM agents, performs hybrid RAG and guarded database analysis,
> validates outputs through independent critic agents, enforces tool-level permission
> policies, escalates uncertain decisions to human reviewers, and continuously evaluates
> retrieval quality, factual grounding, agent trajectories and system cost.

Every clause of that sentence should point at a file and a measured number. That is
the difference between a portfolio project and a demo.

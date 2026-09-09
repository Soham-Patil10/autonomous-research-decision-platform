# Autonomous Enterprise Research & Decision Intelligence Platform

A multi-agent AI system for autonomous research, data analysis and evidence-grounded
decision support — with hybrid RAG, tool-use, safety guardrails, human-in-the-loop
governance and continuous evaluation.

> **Pitch:** give it a hard business question; it plans the work, delegates to specialist
> agents, retrieves evidence from documents / databases / the web, criticises its own
> output, escalates when it is unsure, and produces a cited report — while every step is
> traced and scored.

---

## 1. The scenario this is built around

**Market-entry analysis.** A company asks:

> *"Should we expand into the German electric-vehicle market?"*

The platform answers with a recommendation, a confidence score, the evidence behind every
claim, and an explicit list of what it could not verify.

## 2. What actually happens

```
                              USER QUESTION
                                    |
                                    v
                          +-------------------+
                          |   API (FastAPI)   |
                          +---------+---------+
                                    v
                          +-------------------+
                          | SUPERVISOR AGENT  |  plan + decompose + route
                          +---------+---------+
                 +------------------+------------------+
                 v                  v                  v
          RESEARCH AGENT      DOCUMENT AGENT       DATA AGENT
          (web search)        (hybrid RAG)         (text-to-SQL)
                 |                  |                  |
                 |                  |            SQL GUARDRAILS
                 +------------------+------------------+
                                    v
                            EVIDENCE FUSION
                                    v
                    +-------------------------------+
                    |  CRITIC PANEL                 |
                    |  fact . logic . completeness  |
                    |              |                |
                    |         ADJUDICATOR           |
                    +---------------+---------------+
                        pass <------+------> fail -> re-plan
                                    v
                          CONFIDENCE + RISK ENGINE
                                    |
                     low risk <-----+-----> high risk
                        |                       |
                   auto-deliver           HUMAN APPROVAL
                        +-----------+-----------+
                                    v
                          FINAL CITED REPORT
                                    v
                    TRACES -> EVALUATION -> FAILURE DATASET
```

## 3. Layout

```
app/
  api/            FastAPI routes: submit task, poll status, human approvals
  agents/         supervisor, specialists, critic panel, adjudicator
  graph/          LangGraph state machine wiring the agents together
  rag/            chunking, embeddings, dense + BM25, RRF fusion, reranker
  tools/          tool registry: web_search, doc_search, sql_query
  guardrails/     tool-permission policy engine, SQL guard, risk classifier
  hitl/           escalation rules + approval queue
  memory/         Redis (working) . Postgres (durable) . Chroma (semantic)
  llm/            provider client + complexity-based model router
  observability/  span-level tracing of every agent/tool call
  db/             SQLAlchemy models + session
evaluation/       golden dataset, RAG/agent/system metrics, regression runner
ui/               Streamlit review console (approvals + trace explorer)
scripts/          seed the demo database, ingest the demo corpus
tests/            guardrail, retrieval and workflow tests
docs/             architecture, MVP scope, roadmap
```

## 4. Quick start

```bash
cp .env.example .env
```

```bash
docker compose up -d
```

```bash
pip install -r requirements.txt
```

```bash
python scripts/seed_db.py
```

```bash
python scripts/ingest_docs.py
```

```bash
uvicorn app.main:app --reload --port 8000
```

```bash
streamlit run ui/streamlit_app.py
```

Submit a task:

```bash
curl -X POST localhost:8000/api/tasks -H "content-type: application/json" -d "{\"question\":\"Should we expand into the German EV market?\"}"
```

## 5. Build order

See [docs/roadmap.md](docs/roadmap.md).

| Phase | Ships |
|---|---|
| **V1 — MVP** | supervisor + 3 specialists, LangGraph loop, tool registry, basic RAG, single reviewer, manual approval endpoint |
| **V2 — Grounding** | hybrid retrieval + RRF + reranker, citation verification, text-to-SQL + SQL guardrails, confidence scoring |
| **V3 — Assurance** | critic panel + adjudicator, risk-based escalation, trace explorer, failure forensics, golden-set regression eval |
| **V4 — Efficiency** | complexity-based model routing, cost/latency dashboards, caching |

## 6. Status

Skeleton. Every module has typed interfaces and `TODO(v1..v4)` markers showing where the
real implementation goes. Nothing calls a paid API until you fill in `app/llm/client.py`.

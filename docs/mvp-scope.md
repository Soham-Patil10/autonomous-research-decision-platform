# MVP scope — EU market-entry analysis

## The single scenario

> *"Which EU markets should Acme Mobility prioritise for expansion, and what are the risks?"*

One scenario, done properly, beats five half-built ones. Everything in the MVP exists
to answer this question with evidence.

Scope is EU-27, fourteen markets, 2022–2025. **Widening from three markets to fourteen
changed the task from comparison to discovery** — the agent is no longer told which
countries to compare, it has to find the anomalies. That is a harder task and a better
demonstration, and it costs nothing extra to run.

## What the MVP must do

- [ ] Accept the question over HTTP and return a task id
- [ ] Supervisor produces a 3–5 subtask plan naming real specialists
- [ ] Research agent returns ≥3 web sources with URLs
- [ ] Document agent returns ≥3 corpus passages with document id + locator
- [ ] Data agent produces one SQL query that passes the guard and returns rows
- [ ] That query finds **both** margin cliffs (Sweden 2023, Germany 2024), not just one
- [ ] Synthesis produces claims, each carrying at least one evidence id
- [ ] One reviewer scores the draft and can send it back once
- [ ] Anything below the confidence threshold lands in the approval queue
- [ ] Streamlit console shows the report, the citations and the trace
- [ ] `pytest` passes, including every guardrail test

## What the MVP explicitly does not do

Deferred, deliberately — each has a phase in the roadmap:

- BM25 / hybrid fusion / reranking (v2)
- Three independent critics + adjudication (v3)
- Checkpointed suspend-resume on escalation (v3)
- Judged metrics: faithfulness, answer relevance (v3)
- Semantic memory of past tasks (v3)
- Model routing and cost optimisation (v4)
- Celery workers, horizontal scaling (only if you need it)

## Corpus you need before starting

Fully specified in [data-sources.md](data-sources.md). Short version:

```bash
python scripts/fetch_corpus.py
```

That pulls the EU regulations and SEC filings automatically and prints a checklist for
the sources that must be downloaded by hand (KBA, ACEA, IEA, EAFO, OEM reports). Then
write the four internal documents listed under `synthetic_internal:` in
`data/sources.yaml` — without them the private-corpus half of hybrid RAG proves nothing.

The data encodes a **planted story** whose three legs are each visible to exactly one
agent, so no single specialist can answer the question alone. `scripts/seed_db.py
--dry-run` prints it.

## Definition of done

Run `python -m evaluation.run_eval` and get a JSON report containing a number for
every metric. Not "the demo worked" — a scoreboard, saved to a file, that a later
change can be compared against.

## Two failures worth engineering on purpose

Portfolio value comes from showing the system handling these, not from hiding them:

1. **Unanswerable question** (`g006`) → low confidence → refuses, escalates, does not fabricate.
2. **Destructive SQL** (`g007`) → blocked by the guard → the block is traced and explained.

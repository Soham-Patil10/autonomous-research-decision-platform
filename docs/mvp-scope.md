# MVP scope — market-entry analysis

## The single scenario

> *"Should Acme Mobility expand into the German electric-vehicle market?"*

One scenario, done properly, beats five half-built ones. Everything in the MVP exists
to answer this question with evidence.

## What the MVP must do

- [ ] Accept the question over HTTP and return a task id
- [ ] Supervisor produces a 3–5 subtask plan naming real specialists
- [ ] Research agent returns ≥3 web sources with URLs
- [ ] Document agent returns ≥3 corpus passages with document id + locator
- [ ] Data agent produces one SQL query that passes the guard and returns rows
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

Put 10–30 documents in `data/documents/`:

| Document | Purpose |
|---|---|
| German EV registration statistics | the market-size question |
| 2–3 competitor profiles | the competitive question |
| An EU/German EV regulation summary | the regulatory question, and the one the completeness critic should catch being missed |
| Your fictional company's annual report | internal-performance grounding |
| An internal strategy memo | something only the private corpus knows |

Deliberately include **one question the corpus cannot answer** — that is how you
demonstrate the system refusing instead of fabricating.

## Definition of done

Run `python -m evaluation.run_eval` and get a JSON report containing a number for
every metric. Not "the demo worked" — a scoreboard, saved to a file, that a later
change can be compared against.

## Two failures worth engineering on purpose

Portfolio value comes from showing the system handling these, not from hiding them:

1. **Unanswerable question** (`g006`) → low confidence → refuses, escalates, does not fabricate.
2. **Destructive SQL** (`g007`) → blocked by the guard → the block is traced and explained.

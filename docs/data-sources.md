# Data sources

## The split

| Plane | Feeds | Real or synthetic | Why |
|---|---|---|---|
| Documents | `doc_search` (hybrid RAG) | **Real** | Retrieval metrics on LLM-written text are meaningless. Generated documents are too clean, too on-topic, and never contradict each other — the exact difficulties you are claiming to handle. |
| Analytics DB | `sql_query` (text-to-SQL) | **Synthetic, grounded** | No real company hands over an internal revenue database. Faking it is expected — provided it is internally consistent and encodes a story. |
| Web | `web_search` | Live | Nothing to prepare. Cache in Redis: the re-plan loop repeats queries. |

## Building the corpus

```bash
python scripts/fetch_corpus.py
```

Reads [data/sources.yaml](../data/sources.yaml), downloads what can be automated, and
prints a checklist for what cannot. Three source kinds:

- **`auto`** — plain GET. The EUR-Lex CELEX URLs are the most stable identifiers in the
  manifest and should outlive everything else here.
- **`edgar`** — resolves a company's latest 10-K via the SEC submissions API. Requires
  `CORPUS_CONTACT_EMAIL` in the environment; the SEC rejects requests without a contact
  address in the User-Agent.
- **`manual`** — KBA, ACEA, IEA, EAFO, OEM reports. Their deep links rot every quarter,
  so hardcoding them buys you a script that breaks silently in three months.

Every fetch is recorded in `data/documents/MANIFEST.json` with the source URL, SHA-256,
licence and timestamp. `app/rag/ingest.py` reads that file and attaches `source_url` to
every chunk's metadata — so a `Claim`'s citation resolves to a real URL, not just a
filename. That is the difference between "cited" and *traceable*.

### Licensing

`redistributable: false` entries (IEA, ACEA, OEM reports) are free to download but
restricted to redistribute. `data/documents/` is gitignored, with `MANIFEST.json`
explicitly re-included — so the repo carries the provenance record without the payload.
Anyone cloning it runs the fetcher and gets the same corpus.

Do not add Statista or paywalled consultancy PDFs. Redistribution problems, and a
reviewer who clones your repo cannot reproduce your results.

## Building the database

```bash
python scripts/seed_db.py --dry-run
```

```bash
python scripts/seed_db.py --registrations data/documents/kba_bev.csv
```

The registration figures baked into the script are **approximate placeholders written
from memory** and the script says so loudly on every run. Replace them with the real KBA
FZ series. If you don't, your database will contradict your own corpus, and the fact
critic will correctly flag it — as a defect in your data, not in the agent.

## Scope: EU-27, fourteen markets, 2022–2025

Germany, France, Netherlands, Sweden, Italy, Spain, Belgium, Poland, Denmark, Austria,
Portugal, Ireland, Finland, Czechia.

**Norway and the UK are excluded on purpose.** Both are large EV markets; neither is in
the EU. Conflating them is the single most common error in real EV market analysis, so
`g011` in the golden set tests for exactly that — and ACEA's own tables include EFTA/UK
columns, which makes it an easy mistake for the agent to make honestly.

Fourteen markets rather than three is what turns comparison into **discovery**. With
three markets, "compare Germany and France" is handed to the agent. With fourteen, it has
to find which markets are anomalous.

## The planted story

```
        "Which EU markets should we prioritise, and what are the risks?"
                                      |
        +-----------------------------+-----------------------------+
        v                             v                             v
   SQL agent only              Web agent only              Document agent only
        |                             |                             |
  TWO markets break:          Sweden ended the             (a) AFIR charging
    Sweden  2023                klimatbonus abruptly           obligations raise
    Germany 2024                Nov 2022                        cost of entry in
  ~-10pp each.                Germany ended the                 EVERY market
  Tapering markets            Umweltbonus abruptly        (b) Acme's pricing policy
  (NL, DK, IE, PL)            Dec 2023                        sets a 15% margin
  drift ~-1pp.                France restructured             floor -> both cliffs
  Italy oscillates            rather than ended;              are a POLICY BREACH
  (stop-start policy).        NL/DK/IE tapered            (c) take-or-pay battery
        |                             |                       contract explains why
        |                             |                       COGS stayed high
        +-----------------------------+-----------------------------+
                                      v
              correct answer: abrupt withdrawal destroys margin,
              gradual tapering does not - and it happened twice
```

The tapering and volatile markets are the **controls**. Without them, "margin fell after
a subsidy changed" is a single anecdote. With them, the agent has to identify that the
mechanism is *abruptness*, not the mere absence of a subsidy — which is the difference
between correlation and a causal claim.

### Why two cliffs, in different years

This is the most important design choice in the dataset. An agent that pattern-matches
"what changed in 2024?" finds Germany and stops — producing a fully-cited, logically
sound, **incomplete** answer. Sweden's break is a year earlier, so only an agent
reasoning about the mechanism finds both.

That near-miss is invisible to the fact critic and invisible to the logic critic. It is
caught only by the completeness critic. That single case is what justifies running three
critics instead of one, and it is the strongest thing in the evaluation set.

Same structure applies to AFIR: a draft covering both cliffs but omitting the regulatory
cost of entry is again cited, sound, and incomplete.

### Second plant: stale data

`competitors` holds **2023 shares only**. Ask who leads a market *now* and the database
answers with year-old rows while the corpus answers with current ones (`g010`).

### Third plant: provenance inside the database

`ev_registrations.source` marks every row `reported` or `estimated`. Only Germany and
France carry real figures; the rest are synthesised from population. An agent that cites
an estimated row as established fact without flagging it is making an error — and the
column gives the fact critic what it needs to catch it (`g009`).

This mirrors `MANIFEST.json` on the corpus side: provenance travels with the data, in
both planes.

### Fourth plant: an unanswerable question

`g014` asks something the corpus genuinely cannot answer. Refusing to fabricate is the
behaviour that separates this from a PDF chatbot, and you cannot demonstrate it without
a real gap to refuse into.

## What you still have to write yourself

Four internal documents, specified under `synthetic_internal:` in `data/sources.yaml`.
Without them the document agent knows nothing the research agent could not have found on
the open web — and the private-corpus half of hybrid RAG proves nothing.

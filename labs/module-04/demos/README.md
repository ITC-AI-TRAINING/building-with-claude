# Module 4 Demos — Conversation and Context Management

Four small, single-concept demos that build on the
[`day2/loan_intake_manager.py`](../../../day2/loan_intake_manager.py) reference and the
[Module 4 guide](../../../guides/module-04-conversation-and-context-management.md). Each demo
isolates **one** idea instead of combining all of Module 4 into one file, so you can run them in
order and see exactly where each concept lives.

Each demo is its own independent [`uv`](https://docs.astral.sh/uv/) project — its own
`pyproject.toml`, lockfile, and `.venv` — so you can `cd` into just one folder and run it without
touching the others, or hand out a single demo folder on its own.

## The four demos

| # | Project | Concept | Needs a real API key? |
|---|---------|---------|------------------------|
| 1 | [`01-stateless-memory/`](01-stateless-memory/) | Message formatting & conversation memory — a broken latest-message-only manager vs. the correct full-history manager | Yes |
| 2 | [`02-token-aware-summarization/`](02-token-aware-summarization/) | Token-aware design & summarisation memory — `count_tokens()` per turn, condition-triggered `summarise_and_reset()` | Yes |
| 3 | [`03-downstream-summary-integration/`](03-downstream-summary-integration/) | Downstream integration of a session's final `IntakeSummary` — CRM queue, review queue, customer message | No — fully offline |
| 4 | [`04-server-side-compaction/`](04-server-side-compaction/) | The same demo 2 script, rebuilt on the beta `compact-2026-01-12` server-side compaction feature — the API summarises and resets context for you | Yes |

Each has its own README with setup/run instructions, but the shape is the same for all four:

```bash
cd labs/module-04/demos/01-stateless-memory   # or 02-... / 03-... / 04-...

uv sync                # creates that project's own .venv
cp .env.example .env   # (not needed for demo 3)
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...

uv run <script>.py
```

## Notes

- Same security rule as the rest of the course: never hardcode a key, never commit `.env` (the
  repo's root `.gitignore` already excludes `.env` and every project's `.venv/` here).
- Demo 2's `--threshold` default (600 tokens) is deliberately artificially low so the
  condition-based trigger fires within a short scripted run — production code uses
  `day2/loan_intake_manager.py`'s real `TOKEN_WARN_THRESHOLD = 50_000`. Don't copy the demo's
  number into real code.
- Demo 3 needs no API key at all: it starts from summaries as if a conversation had already been
  parsed, because "downstream integration" is specifically about what happens *after* the summary
  exists, not during the conversation that produced it.
- Demo 4 is demo 2's conversation again, but summarisation moves server-side: instead of your own
  `count_tokens()` + `summarise_and_reset()`, the beta `compact-2026-01-12` feature has the API
  track input tokens and inject a `compaction` content block once a trigger is approached — see its
  own README for how it forces that to happen within a short, cheap run despite the trigger's
  50,000-token floor.
- Pair each demo with its matching interactive visualization for an offline walkthrough of the same
  idea: [`01-stateless-vs-stateful.html`](../01-stateless-vs-stateful.html),
  [`02-token-growth-and-summarization.html`](../02-token-growth-and-summarization.html),
  [`03-message-anatomy.html`](../03-message-anatomy.html).

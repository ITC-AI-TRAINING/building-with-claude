# Module 3 Demos — Structured Outputs and Validation

Three small, single-concept demos that build on the
[`day2/loan_application_extractor.py`](../../../day2/loan_application_extractor.py) reference and
the [Module 3 guide](../../../guides/module-03-structured-outputs-and-validation.md). Each demo
isolates **one** idea instead of combining all of Module 3 into one file, so you can run them in
order and see exactly where each concept lives.

Each demo is its own independent [`uv`](https://docs.astral.sh/uv/) project — its own
`pyproject.toml`, lockfile, and `.venv` — so you can `cd` into just one folder and run it without
touching the others, or hand out a single demo folder on its own.

## The three demos

| # | Project | Concept | Needs a real API key? |
|---|---------|---------|------------------------|
| 1 | [`01-schema-vs-freeform/`](01-schema-vs-freeform/) | JSON generation & parsing — naive `create()` + `json.loads()` vs. `messages.parse(output_format=...)` on the same input | Yes |
| 2 | [`02-validation-retry/`](02-validation-retry/) | Validation & retries — a normal, an ambiguous, and a genuinely incomplete application through the bounded retry loop | Yes |
| 3 | [`03-downstream-integration/`](03-downstream-integration/) | Downstream integration — reshaping already-validated records for a CSV export, a committee queue, and a risk bucket | No — fully offline |

Each has its own README with setup/run instructions, but the shape is the same for all three:

```bash
cd labs/module-03/demos/01-schema-vs-freeform   # or 02-... / 03-...

uv sync                # creates that project's own .venv
cp .env.example .env   # (not needed for demo 3)
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...

uv run <script>.py
```

## Notes

- Same security rule as the rest of the course: never hardcode a key, never commit `.env` (the
  repo's root `.gitignore` already excludes `.env` and every project's `.venv/` here).
- All three demos share the same `LoanApplicationRecord` schema and the same five applicants as
  [`day2/loan_application_extractor.py`](../../../day2/loan_application_extractor.py) — the point
  is to see one schema used three different ways, not three different domains.
- Demo 3 needs no API key at all: it starts from records as if extraction had already succeeded,
  because "downstream integration" is specifically about what happens *after* validation, not
  during it.
- Demo 2's "ambiguous" test case is model-dependent by design — it may or may not trigger a retry
  depending on how the model resolves the ambiguity on the first attempt. Read the retry ledger it
  prints rather than expecting a fixed outcome.
- Pair each demo with its matching interactive visualization for an offline walkthrough of the same
  idea: [`01-schema-anatomy.html`](../01-schema-anatomy.html),
  [`02-validation-retry-loop.html`](../02-validation-retry-loop.html),
  [`03-freeform-vs-schema.html`](../03-freeform-vs-schema.html).

# Demo 1 — Schema vs. Freeform: JSON Generation &amp; Parsing

**Module 3: Structured Outputs and Validation**
Based on [`day2/loan_application_extractor.py`](../../../../day2/loan_application_extractor.py).

Sends the same raw loan-application text through two extraction approaches: (a) the naive way —
ask nicely for JSON, then `json.loads()` the raw text yourself, and (b) the schema-driven way —
`client.messages.parse(output_format=LoanApplicationRecord)`. Both usually "work" on well-behaved
input, which is exactly why the difference is easy to miss until it isn't.

Independent [`uv`](https://docs.astral.sh/uv/) project — its own `pyproject.toml`, lockfile, and
`.venv`.

## Setup

```bash
uv sync
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

## Run

```bash
uv run schema_vs_freeform.py
uv run schema_vs_freeform.py --applicant 3
```

## What to notice

- The naive approach (a) prints the raw model output first — watch for a leading sentence or a
  ` ```json ` fence around the object, which a blind `json.loads()` cannot handle.
- When (a) fails, the script shows the hand-rolled fallback: stripping a markdown fence with a
  regex (`r"```(?:json)?\s*(\{[\s\S]*?\})\s*```"`) — the same fence-stripping pattern this course
  uses for judge-output parsing in later evaluation labs. It's a workaround, not a fix — it still
  assumes a particular failure shape.
- The schema-driven approach (b) has no raw-text parsing step at all — there's nothing for a fence
  or a leading sentence to break, because `response.parsed_output` is already a validated
  `LoanApplicationRecord` instance.
- Both approaches can still be *wrong in content* (a hallucinated field value) — schema-driven
  parsing guarantees the **shape**, not the truth of every value. That's what
  [§4 Validation](../../../../guides/module-03-structured-outputs-and-validation.md#4-validation)
  and Module 7's evaluation rubrics are for.

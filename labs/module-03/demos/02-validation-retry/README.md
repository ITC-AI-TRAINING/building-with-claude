# Demo 2 — Validation Retry: Retries, and Their Limits

**Module 3: Structured Outputs and Validation**
Based on [`day2/loan_application_extractor.py`](../../../../day2/loan_application_extractor.py).

Runs the same bounded validation-retry loop from the reference script against three inputs: a
normal application, an ambiguous one, and a genuinely incomplete one with no loan amount stated
anywhere in the text. The point isn't that retries always help — it's learning to tell the two
failure modes apart.

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
uv run validation_retry.py
```

## What to notice

- **APP-NORMAL** should succeed on attempt 1 — every field is stated plainly in the text.
- **APP-AMBIGUOUS** ("expand my shop... 4-5 years") may or may not need a retry — `loan_type`
  isn't stated as one of the four literal categories and `tenure_years` is a range, not a single
  integer. If it needs a retry, that's the validation error being fed back and Claude picking a
  single valid value the second time. This one is model-dependent by design; the retry ledger at
  the end shows what actually happened on your run.
- **APP-INCOMPLETE** should **FAIL** after `MAX_RETRIES = 2`, not succeed with a fabricated
  number. Kavita Nair's application genuinely never states a loan amount — re-prompting can't
  invent a truthful figure that isn't in the source. If this test case ever "succeeds," check
  whether Claude guessed a plausible-sounding amount — that's a worse outcome than a clean failure,
  and worth flagging.
- The final **retry ledger** table is the same idea as Lab 3's success criteria: failures must be
  reported with a reason, never silently dropped.
- [`02-validation-retry-loop.html`](../../02-validation-retry-loop.html) animates this same
  attempt-by-attempt loop offline, with no API calls.

# Demo 3 — Downstream Integration: What a Validated Record Buys You

**Module 3: Structured Outputs and Validation**
Based on [`day2/loan_application_extractor.py`](../../../../day2/loan_application_extractor.py).

Takes already-validated `LoanApplicationRecord` instances — the same five applicants the reference
script extracts — and reshapes them for three downstream consumers: a core-banking CSV export, a
credit-committee referral queue, and a rough risk bucket. **No API calls, no re-validation.** This
demo is deliberately offline: the whole point of Module 3 is that once you have
`response.parsed_output`, you never touch `json.loads()`, a `.get()` with a fallback, or a type
check again.

Independent [`uv`](https://docs.astral.sh/uv/) project — its own `pyproject.toml` and `.venv`
(only needs `pydantic`, no `anthropic` or API key at all).

## Setup

```bash
uv sync
```

## Run

```bash
uv run downstream_integration.py
```

## What to notice

- **(a) CSV export** — every field is read directly (`record.loan_amount_inr`, not
  `record.get("loan_amount_inr", 0)`). There's no "what if this key is missing" branch anywhere,
  because Pydantic already guaranteed every required field is present and correctly typed.
- **(b) Committee referral queue** — reuses the credit policy's actual Section 2.2 threshold
  (loans over INR 50,00,000 need committee review) and Section 4.1 (no bureau score → refer, never
  decline) from `day2/starter.py`'s system prompt. Venkatesh Iyer (₹70L loan) and Sunita Rao (no
  credit score) both queue; the other three don't.
- **(c) Risk buckets** — a deliberately simplified loan-to-annual-income proxy, **not** the bank's
  real DTI formula (Section 2.1), which needs `existing_emi_inr` — a field this schema doesn't
  capture. Labelled illustrative on purpose, the same way Module 1's cost-estimate constants are
  labelled illustrative rather than real pricing.
- This is the smallest possible example of what Module 3's guide (§6) calls "the seam every later
  module plugs into" — Module 4's conversation summary, Module 5's tool-populated fields, and
  Module 7's accuracy scoring all read a `LoanApplicationRecord` the same trusting way.

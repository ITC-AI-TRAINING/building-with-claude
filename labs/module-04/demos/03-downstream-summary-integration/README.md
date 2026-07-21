# Demo 3 — Downstream Summary Integration: What a Validated Summary Buys You

**Module 4: Conversation and Context Management**
Based on [`day2/loan_intake_manager.py`](../../../../day2/loan_intake_manager.py).

Takes already-produced `IntakeSummary` instances — the same schema the reference script's final
`client.messages.parse()` call returns — and reshapes them for three downstream consumers: a CRM
follow-up queue, a risk-flagged review queue, and a customer-facing next-step message. **No API
calls, no re-validation.** Same idea as Module 3's `03-downstream-integration/` demo, applied here
to a conversation's final summary instead of a single-turn extraction.

Independent [`uv`](https://docs.astral.sh/uv/) project — its own `pyproject.toml` and `.venv`
(only needs `pydantic`, no `anthropic` or API key at all).

## Setup

```bash
uv sync
```

## Run

```bash
uv run downstream_summary_integration.py
```

## What to notice

- **(a) CRM follow-up queue** — the task text is chosen purely from `recommended_action`, a
  `Literal["proceed", "review", "decline"]` — there's no `else` branch to worry about because
  Pydantic already guarantees it's one of exactly three values.
- **(b) Risk-flagged review queue** — filters to everything that *didn't* clear automatically,
  the same "only queue what needs a human" pattern as Module 3's committee-review queue, just
  triggered by a conversation's outcome instead of a raw application field.
- **(c) Customer-facing messages** — each message is built only from fields the summary actually
  contains; the decline message references the real Section 7.2 timeline ("written notice within
  2 business days") from the credit policy, and never states a reason the summary doesn't know.
- This demo runs identically whether the four sessions came from a live 6-turn conversation or
  were hand-written like this — because by the time you have `response.parsed_output`, the
  conversation that produced it no longer matters to the code reading it.

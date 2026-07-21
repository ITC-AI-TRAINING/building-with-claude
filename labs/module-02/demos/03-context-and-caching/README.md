# Demo 3 — Context and Caching: Long-Context Handling

**Module 2: Prompt Engineering for Applications**
Based on [`day1/credit_policy_assistant.py`](../../../../day1/credit_policy_assistant.py).

Injects the same ~200-line Apex Bank policy document into three questions in a row — first with
no caching, then with `cache_control: {"type": "ephemeral"}` on the document block — so you can
watch the real `response.usage` fields shift instead of taking "prompt caching saves cost" on
faith.

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
uv run context_and_caching.py
uv run context_and_caching.py --questions 2
uv run context_and_caching.py --no-cache   # baseline only
```

## What to notice

- The pre-flight `count_tokens()` call is free and instant — use it to sanity-check a request
  *before* spending on inference, the same habit from Module 1 §6.
- In the **BASELINE** section, `input_tokens` stays roughly flat across all three calls — the full
  document is reprocessed every time.
- In the **CACHED** section, call 1 shows `cache_creation_input_tokens > 0` (writing the cache);
  calls 2 and 3 show `cache_read_input_tokens > 0` instead of a full `input_tokens` charge for the
  document — a cheaper re-read of the same content.
- Caching changes **cost and latency only** — it never changes what Claude sees or answers. Don't
  confuse it with a correctness feature.
- Dollar figures are never printed here on purpose — any conversion from these token counts to a
  price should use the current per-model rate from
  [platform.claude.com/docs](https://platform.claude.com/docs), not a number baked into this demo.
- [`03-long-context-and-caching.html`](../../03-long-context-and-caching.html) animates this same
  before/after contrast offline, with no API calls.

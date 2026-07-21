# Demo 2 — Token-Aware Summarization

**Module 4: Conversation and Context Management**
Based on [`day2/loan_intake_manager.py`](../../../../day2/loan_intake_manager.py).

Runs a longer, more talkative loan intake conversation than the reference script's 4-turn demo,
checking `count_tokens()` after every turn against a deliberately **low** threshold — so the
condition-based `summarise_and_reset()` trigger actually fires within a short run, instead of the
reference script's scripted `if turn == 3` demonstration trigger.

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
uv run token_aware_summarization.py
uv run token_aware_summarization.py --threshold 400
```

## What to notice

- The `--threshold` default (600 tokens) is **artificially low** purely so this demo triggers
  within 6 short turns — production code uses `day2/loan_intake_manager.py`'s real
  `TOKEN_WARN_THRESHOLD = 50_000`. Don't copy the low number into real code.
- Watch the token count printed after every turn climb, then drop sharply right after a
  `[INFO] threshold crossed...` line — that's `summarise_and_reset()` collapsing the whole history
  into one `[Session summary]` turn.
- The printed summary should still name the applicant, loan type, amount, income, tenure, and
  credit score collected so far — because the summarisation prompt explicitly lists them as fields
  to preserve. Try editing that "Preserve: ..." line down to just "Summarise this conversation" and
  re-run — watch a field quietly disappear from the summary.
- A lower `--threshold` triggers more reset cycles per run; a higher one may never trigger at all
  within 6 turns — both are useful for seeing the boundary condition.
- [`02-token-growth-and-summarization.html`](../../02-token-growth-and-summarization.html) animates
  this same climb-and-drop pattern offline, with no API calls.

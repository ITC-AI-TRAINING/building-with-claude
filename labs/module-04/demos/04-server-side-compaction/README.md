# Demo 4 — Server-Side Compaction (Beta)

**Module 4: Conversation and Context Management**
Based on [`day2/loan_intake_manager.py`](../../../../day2/loan_intake_manager.py) and directly
comparable to [`02-token-aware-summarization/`](../02-token-aware-summarization/) — same 6-turn
loan intake script, two different ways of keeping a long conversation inside the context window.

| | Demo 2 (manual) | Demo 4 (this one) |
|---|---|---|
| Who tracks tokens? | Your own code, via `count_tokens()` after every turn | The API, via `context_management` on every request |
| Who decides to reset? | Your own `if tokens > threshold:` check | The server, once input tokens approach the trigger |
| Who writes the summary? | A second model call your code makes (`summarise_and_reset()`) | The model itself, inline, as an extra `compaction` content block |
| What you must still do | Reset `self.messages` to `[{"role": "user", "content": summary}]` | Append the **full** `response.content` (compaction block included) back onto `messages`, every turn |

Independent [`uv`](https://docs.astral.sh/uv/) project — its own `pyproject.toml`, lockfile, and
`.venv`.

## Setup

```bash
uv sync
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

> ⚠️ **You must create a `.env` in THIS folder, not just the repo root.** `load_dotenv()` walks up
> from this folder looking for a `.env`; if this folder doesn't have its own, it silently falls back
> to the repo root's `.env`, which sets `ANTHROPIC_MODEL=claude-haiku-4-5` for cost reasons across
> Days 2-5. **Haiku does not support compaction** — running without a local `.env` fails with:
> `'claude-haiku-4-5-...' does not support the 'compact_20260112' context management strategy.`
> The script now checks the resolved model up front and raises a clear `EnvironmentError` instead of
> letting that reach the API as a raw 400, but the fix is still to `cp .env.example .env` here.

## Run

```bash
uv run server_side_compaction.py
uv run server_side_compaction.py --trigger 60000
```

## How this demo actually triggers compaction

The real trigger default is **150,000 input tokens** — nowhere near what 6 short scripted turns
would ever accumulate. The API also enforces a **50,000-token floor** on `trigger.value`, so unlike
demo 2 there's no way to dial the trigger down into "a handful of short turns" range.

Instead, this demo sends one oversized **seed turn** first: a block of repeated policy-note filler
text, sized with `count_tokens()` (same idea as demo 2, used here to size a seed instead of to fire
a reset) so it comfortably clears whatever `--trigger` value is in effect. That single seed turn
stands in for "a long conversation already happened" — compaction fires on it almost immediately,
and the 6 real applicant turns that follow are a normal, short conversation continuing seamlessly
on top of the server-compacted history.

## What to notice

- Watch `usage.input_tokens` printed after every request: it spikes on the seed turn, then drops
  sharply on the very next turn once the `compaction` block has taken over — the same
  climb-then-drop shape as demo 2's token count, but produced by the server, not by your code.
- The `[COMPACTION TRIGGERED]` line only prints on requests where `response.content` actually
  contains a `type: "compaction"` block — not every turn will have one. Once it's fired, later
  turns keep growing normally until (in a long enough run) it fires again.
- The critical line is `messages.append({"role": "assistant", "content": response.content})` in
  `send()` — appending only `response.content[0].text` instead of the full content list would
  silently drop the `compaction` block, and the server would have nothing to compact against on
  the next request.
- Try `--trigger 50000` (the floor, and the default) vs. a much higher `--trigger 140000` — the
  higher value means the seed turn (and thus every request) needs far more padding tokens, so the
  same demo costs more and takes longer to build the seed, without changing what it demonstrates.
- [`02-token-growth-and-summarization.html`](../../02-token-growth-and-summarization.html) animates
  the climb-and-drop pattern offline; the manual version it depicts is demo 2, but the same visual
  shape applies here as well.

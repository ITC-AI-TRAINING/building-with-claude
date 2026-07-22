# Demo 2 — Manual Agentic Loop

**Module 5: Tool Use and Function Integration**
Based on [`day3/invoice_tool_agent.py`](../../../../day3/invoice_tool_agent.py).

The full invoice agent trimmed to **two tools** (`get_vendor_details`, `calculate_tds`) and a
`--request` flag, so the `while` loop itself — not the invoice-validation business rules — is the
thing you're watching. Every loop iteration prints its `stop_reason`, the tool it called, and the
tool's result before the loop sends anything back to Claude.

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
uv run manual_agentic_loop.py
uv run manual_agentic_loop.py --request "Look up vendor VEND-404 and calculate TDS on 50000."
```

## What to notice

- Each `[loop iteration N]` block is one full request/response round trip — count them and you're
  counting exactly how many `client.messages.create()` calls this one request cost.
- `stop_reason` flips from `'tool_use'` to `'end_turn'` on the final iteration — that's the whole
  loop-termination condition, no other signal is needed.
- The default request needs **two sequential tool calls** (`get_vendor_details` then
  `calculate_tds` — the TDS rate depends on the vendor's category, which the first call returns).
  Compare that to the `--request` example above, an invalid vendor ID: watch whether Claude still
  calls `calculate_tds` even after `get_vendor_details` reports an error, and whether it sometimes
  calls *both* tools in the **same** iteration instead of sequentially — either is valid; the point
  is seeing your loop handle whichever shape actually comes back.
- Pair this with [`03-tool-runner-beta/`](../03-tool-runner-beta/) — same scenario, same two
  tools, run the same `--request` against both and diff the amount of code each one needed.

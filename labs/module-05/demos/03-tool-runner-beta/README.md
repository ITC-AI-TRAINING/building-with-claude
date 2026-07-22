# Demo 3 — Tool Runner (beta)

**Module 5: Tool Use and Function Integration**
Based on [`day3/invoice_tool_agent_beta.py`](../../../../day3/invoice_tool_agent_beta.py).

The exact same two-tool scenario as [`02-manual-agentic-loop/`](../02-manual-agentic-loop/), built
with `@beta_tool`-decorated functions and `client.beta.messages.tool_runner(...).until_done()`
instead of a hand-written `while` loop — run the same `--request` against both demos and compare.

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
uv run tool_runner_beta.py
uv run tool_runner_beta.py --request "Look up vendor VEND-404 and calculate TDS on 50000."
```

## What to notice

- **No loop-iteration prints** — `.until_done()` drives every request/response round trip
  internally. You get the final answer; you don't see the intermediate `stop_reason` values
  unless you inspect the runner's stream yourself.
- **Schema comes from the function**, not a hand-written dict: `get_vendor_details`'s
  `input_schema` is inferred entirely from its `vendor_id: str` type hint and its docstring's
  `Args:` section — compare to `02-manual-agentic-loop/`'s explicit `TOOLS` list for the same tool.
- **Failures are Python exceptions, not return values** — `raise ToolError(...)` here does the
  job that `return {"error": ...}` plus `"is_error": "error" in result` does in the manual demo.
  Run the `VEND-404` request against both demos and confirm Claude's final answer explains the
  missing vendor the same way either style.
- **Every tool returns `json.dumps(...)`, a `str`** — try changing `calculate_tds` to `return
  {...}` (a raw dict) and rerun; you'll hit the exact `400` error this module's guide warns about
  in its Common Pitfalls table.

# Module 5 Demos — Tool Use and Function Integration

Three small, single-concept demos that build on the
[`day3/invoice_tool_agent.py`](../../../day3/invoice_tool_agent.py) /
[`invoice_tool_agent_beta.py`](../../../day3/invoice_tool_agent_beta.py) reference scripts and the
[Module 5 guide](../../../guides/module-05-tool-use-and-function-integration.md). Each demo
isolates **one** idea instead of combining all of Module 5 into one file, the same split Module 1
used for "secure call" / "cost awareness" / "error handling".

Each demo is its own independent [`uv`](https://docs.astral.sh/uv/) project — its own
`pyproject.toml`, lockfile, and `.venv` — so you can `cd` into just one folder and run it without
touching the others, or hand out a single demo folder on its own.

## The three demos

| # | Project | Concept | Needs a real API key? |
|---|---------|---------|------------------------|
| 1 | [`01-tool-schema-design/`](01-tool-schema-design/) | Anatomy of a database, search, and calculator tool — `input_schema`, dispatch, and a hand-built `tool_use`/`tool_result` pair | No — fully offline |
| 2 | [`02-manual-agentic-loop/`](02-manual-agentic-loop/) | The manual `while` loop, trimmed to two tools, with a per-iteration trace printed | Yes |
| 3 | [`03-tool-runner-beta/`](03-tool-runner-beta/) | The same two-tool scenario via `@beta_tool` + `client.beta.messages.tool_runner(...).until_done()` | Yes |

Each has its own README with setup/run instructions, but the shape is the same for all three:

```bash
cd labs/module-05/demos/01-tool-schema-design   # or 02-... / 03-...

uv sync                # creates that project's own .venv
cp .env.example .env   # not needed for demo 1
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...

uv run <script>.py
```

## Notes

- Same security rule as the rest of the course: never hardcode a key, never commit `.env` (the
  repo's root `.gitignore` already excludes `.env` and every project's `.venv/` here).
- Demo 1 needs no API key at all: every `tool_use` block it dispatches is hand-written, because
  the point is seeing the shape of a tool call and its result, not watching Claude generate one.
- Demos 2 and 3 use the **same** two tools (`get_vendor_details`, `calculate_tds`) and accept the
  same `--request` flag on purpose — run one request against both and diff the code, not just the
  output, to see exactly what the beta `tool_runner()` does and doesn't take off your hands.
- Pair each demo with its matching interactive visualization for an offline walkthrough of the
  same idea:
  [`01-tool-schema-anatomy.html`](../01-tool-schema-anatomy.html) (demo 1),
  [`02-agentic-loop-trace.html`](../02-agentic-loop-trace.html) (demo 2),
  [`03-manual-vs-tool-runner.html`](../03-manual-vs-tool-runner.html) (demos 2 & 3 side by side).

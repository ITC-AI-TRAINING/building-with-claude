# Demo 1 — Tool Schema Design: Database, Search, and Calculator

**Module 5: Tool Use and Function Integration**
Based on [`day3/invoice_tool_agent.py`](../../../../day3/invoice_tool_agent.py).

Shows the anatomy of a tool definition — `name`, `description`, `input_schema` — and what happens
on each side of a `tool_use` / `tool_result` exchange, for the three tool patterns named in the
course design: a **database** lookup, a **search**, and a **calculator**. **No API calls, no
Claude involved at all** — every `tool_use` block here is hand-written, so you can see exactly
what your dispatch code has to handle before you ever watch Claude generate one for real.

Independent [`uv`](https://docs.astral.sh/uv/) project — its own `pyproject.toml` and `.venv`
(no dependencies at all — pure standard library).

## Setup

```bash
uv sync
```

## Run

```bash
uv run tool_schema_design.py                          # walk all 5 scripted scenarios
uv run tool_schema_design.py --tool get_vendor_details --args '{"vendor_id": "VEND-001"}'
uv run tool_schema_design.py --tool calculate_tds --args '{"amount_inr": 92000, "category": "goods"}'
```

## What to notice

- **Database (`get_vendor_details`)** — one exact key in, one record (or an error) out. Scenario 2
  deliberately looks up a vendor ID that doesn't exist, so you see the `{"error": ...}` /
  `is_error: true` shape a missing record produces.
- **Search (`search_vendors`)** — a partial string can match zero, one, or many records; the
  `input_schema` still only needs one string field, but the *result* shape is a list, not a
  single record.
- **Calculator (`calculate_tds`)** — no lookup at all, just deterministic math on the arguments
  Claude supplies — the reason to hand this to a tool instead of trusting the model's arithmetic.
- **Scenario 5 is a schema violation on purpose** — `calculate_tds` is called without its required
  `amount_inr` field. `validate_against_schema()` catches it before `TOOL_FUNCTIONS[tool_name]` is
  even called, producing the same `is_error: true` shape a real tool failure would. In production,
  the Claude API itself enforces `required` fields before a `tool_use` block is ever emitted — this
  demo's validator exists only so you can see that check happen, not because you'd normally
  duplicate it.
- Pair this with [`01-tool-schema-anatomy.html`](../../01-tool-schema-anatomy.html) for the same
  idea as a click-through visualization.

# Lab 5 — Invoice Validation Agent
**Module 5: Tool Use and Function Integration**
**Duration:** 90 minutes

---

## Objective

Build an agent that validates Apex Bank vendor invoices for payment by calling tools — a
database lookup, a search, and a calculator — instead of trusting Claude to recall or invent
invoice and vendor data. By the end you will have built the same agent two ways: a manual
`while` loop over `client.messages.create()`, and the higher-level beta `tool_runner()`.

---

## Pre-requisites

1. Labs 1–4 complete (secure client setup, system prompts, structured output, conversation
   management — this lab's loop reuses all four).
2. Read the reference data first:
   [`shared/data/apex_bank_vendor_master.md`](../shared/data/apex_bank_vendor_master.md) and
   [`shared/data/apex_bank_invoices.md`](../shared/data/apex_bank_invoices.md). Work out by hand
   which of the 5 invoices should be approved and which should be held, and why — you'll check
   the agent's answers against your own.
3. Dependencies already in `shared/requirements.txt` (no new packages needed for this lab).

---

## Part 1 — Define the tools (20 min)

Open `day3/invoice_tool_agent.py`. Three tool *shapes* are already implemented as plain Python
functions — a database lookup, a search, and a calculator — matching the three tool-use patterns
from the course design:

| Function | Pattern | What it does |
|---|---|---|
| `get_invoice_details(invoice_id)` | Database | Exact-key lookup in `INVOICE_DB` |
| `get_vendor_details(vendor_id)` | Database | Exact-key lookup in `VENDOR_DB` |
| `search_invoices(vendor_name)` | Search | Partial, case-insensitive match over `INVOICE_DB` |
| `calculate_tds(amount_inr, category)` | Calculator | Pure function — no lookup, just math |

Read each function, then read its matching entry in the `TOOLS` list — the JSON Schema
`input_schema` that tells Claude what arguments each tool takes:

```python
{
    "name": "get_vendor_details",
    "description": "Fetch one vendor's master record ... by its exact vendor ID, e.g. 'VEND-001'.",
    "input_schema": {
        "type": "object",
        "properties": {"vendor_id": {"type": "string", "description": "Exact vendor ID"}},
        "required": ["vendor_id"],
    },
}
```

**Check:** for each of the four tools, can you point to the line of `description` text that tells
Claude *when* to call it (not just what it returns)? A schema with a vague description is the
most common reason a model picks the wrong tool or skips a required one.

---

## Part 2 — Trace the manual tool loop (20 min)

`run_agent()` is the core of this lab — a `while True` loop that keeps calling Claude until it
stops asking for tools:

```python
while True:
    response = client.messages.create(
        model=MODEL, max_tokens=1024, system=SYSTEM_PROMPT, tools=TOOLS, messages=messages,
    )
    messages.append({"role": "assistant", "content": response.content})

    if response.stop_reason != "tool_use":
        break

    tool_results = []
    for block in response.content:
        if block.type != "tool_use":
            continue
        func = TOOL_FUNCTIONS[block.name]
        result = func(**block.input)
        tool_results.append({
            "type": "tool_result", "tool_use_id": block.id,
            "content": json.dumps(result), "is_error": "error" in result,
        })
    messages.append({"role": "user", "content": tool_results})
```

Three details that are easy to get wrong — trace each one in the code and confirm you can explain
it before moving on:

1. **The loop condition is `stop_reason != "tool_use"`, not `== "end_turn"` checked with a
   `break` inside the tool branch.** Why does looping "until not tool_use" behave the same as
   looping "until end_turn", and why is it written this way here?
2. **`messages.append({"role": "assistant", "content": response.content})` appends the full
   content list, not `response.content[0].text`.** Change it to `[0].text` yourself temporarily,
   rerun the script, and read the error. What does it tell you about what a `tool_use` block
   actually contains?
3. **All tool results for one turn go into a single `{"role": "user", "content": [...]}` message**,
   even when Claude requested two tools at once. Find a request in `main()` that only calls one
   tool per turn, then reason about when a *single* assistant turn would request multiple tools
   in parallel (hint: think about `get_invoice_details` + `get_vendor_details` for the same
   invoice).

Run it:
```bash
cd day3
python invoice_tool_agent.py
```

Expect six invoice reviews, ending with a `DECISION: APPROVE | HOLD - <reason>` line each —
compare them against the table you worked out in Part 0 from `apex_bank_invoices.md`.

---

## Part 3 — Build the beta `tool_runner()` version (25 min)

Open `day3/invoice_tool_agent_beta.py` — the same task, without the manual loop. Compare the two
tool definition styles side by side:

```python
# Manual style — day3/invoice_tool_agent.py
def calculate_tds(amount_inr: float, category: str) -> dict:
    ...
TOOLS = [{"name": "calculate_tds", "description": "...", "input_schema": {...}}]  # written by hand

# Beta style — day3/invoice_tool_agent_beta.py
@beta_tool
def calculate_tds(amount_inr: float, category: str) -> str:
    """Calculate the TDS amount and net payable for an invoice.

    Args:
        amount_inr: Invoice amount in INR.
        category: Vendor's payment category ...
    """
    ...  # schema is inferred from the type hints + this docstring
```

Then compare how each style drives the loop:

```python
# Manual — you write the while loop yourself (Part 2)

# Beta — the runner owns the loop
result = client.beta.messages.tool_runner(
    model=MODEL, max_tokens=1024, system=SYSTEM_PROMPT, tools=TOOLS,
    messages=[{"role": "user", "content": user_message}],
).until_done()
```

Note two things the beta style changes, not just shortens:

- **Tool failures raise `ToolError`, not a `{"error": ...}` dict.** `get_vendor_details` in the
  beta file raises `ToolError(f"No vendor found with ID '{vendor_id}'")` instead of returning
  `{"error": ...}` — the runner catches it and builds the `is_error` tool result for you.
- **Tool return values must be a `str` (or content blocks), not a raw `dict`.** Every tool in the
  beta file ends with `return json.dumps({...})`, exactly like the manual file's `json.dumps(result)`
  in the loop — the runner doesn't serialize a dict for you.

Run it and confirm the six answers match the manual version:
```bash
python invoice_tool_agent_beta.py
```

---

## Part 4 — Force a tool-selection failure (15 min)

Add one more request to the `requests` list in **either** file, deliberately designed to trip up
tool selection:

```python
"What's the total amount across every invoice from a professional-services vendor?",
```

This requires the agent to call `search_invoices` or multiple `get_invoice_details` calls, then
`get_vendor_details` to check each vendor's `category`, then sum client-side — no single tool
answers it directly. Run it and read the transcript: does the agent chain the right tools in the
right order, or does it (incorrectly) try to answer from memory? Note what you observe — this is
the same "test the near-miss / hard case, not just the happy path" discipline from Lab 2's
adversarial test.

---

## Success Criteria

| Check | Pass condition |
|-------|---------------|
| Three tool patterns present | At least one database, one search, and one calculator-style tool defined |
| Tool schemas | Every tool's `input_schema` has a `description` specific enough to disambiguate it from the others |
| Manual loop correct | Loops on `stop_reason != "tool_use"` (or equivalently `!= "end_turn"`); appends the full `response.content`, never `content[0].text` |
| Tool results well-formed | Every `tool_result` carries a matching `tool_use_id` and sets `is_error` correctly |
| All 5 invoices resolved | Each of `INV-2026-0101`–`0105` ends with a `DECISION: APPROVE \| HOLD - <reason>` line matching `apex_bank_invoices.md`'s expected outcomes |
| Both styles agree | Manual (`invoice_tool_agent.py`) and beta (`invoice_tool_agent_beta.py`) reach the same decision for every invoice |
| Edge case tested | Part 4's multi-tool request attempted and its tool-call sequence reviewed, not just its final answer |

---

## Stretch Goals

1. **Parallel tool calls:** rewrite one `main()` request to ask about two invoices in the same
   user turn (e.g. "Validate INV-2026-0101 and INV-2026-0103"). Inspect `response.content` on the
   first loop iteration — does Claude request both `get_invoice_details` calls in a single
   `tool_use` turn? Confirm your loop handles multiple `tool_use` blocks in one response correctly
   (it already should — find the line that proves it).
2. **`tool_choice`:** force the very first call to use `search_invoices` regardless of the prompt
   by passing `tool_choice={"type": "tool", "name": "search_invoices"}`, and see how the agent's
   first turn changes.
3. **A fifth tool:** add a `flag_for_review(invoice_id, reason)` tool with no return value beyond
   a confirmation, and have the agent call it whenever it holds an invoice — a common real pattern
   where one tool performs a side effect (writing to a queue) instead of only returning data.

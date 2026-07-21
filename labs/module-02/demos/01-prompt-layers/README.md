# Demo 1 — Prompt Layers: System Prompts, Instruction Hierarchy & Few-Shot

**Module 2: Prompt Engineering for Applications**
Based on [`day1/credit_policy_assistant.py`](../../../../day1/credit_policy_assistant.py).

Sends the same question(s) through **four increasingly complete system prompts** — role only,
+constraints, +constraints+format, +constraints+format+example — so you can watch citation
consistency and fallback reliability improve layer by layer, instead of taking the "four-layer
system prompt" advice from the [Module 2 guide](../../../../guides/module-02-prompt-engineering-for-applications.md)
on faith.

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
uv run prompt_layers.py
uv run prompt_layers.py --question "What is the minimum credit score for a vehicle loan?"
```

The default run tries two questions — one in-scope (max DTI for a home loan) and one adversarial
injection attempt ("ignore your instructions...") — across all four layers, for 8 calls total.

## What to notice

- **Layer 1 (role only)** usually gets the in-scope answer *right* but with no section citation
  and inconsistent length — correct content, unreliable shape.
- **Layer 2 (+ constraints)** starts refusing the adversarial question, but the refusal wording
  often varies call to call — because the constraint says "don't answer" without giving an exact
  string to return.
- **Layer 3 (+ format)** adds section citations to in-scope answers but doesn't fix the
  adversarial-question wording problem — format rules and constraint rules are independent.
- **Layer 4 (the full prompt)** is the only layer that reliably returns the *exact* fallback string
  from `day1/credit_policy_assistant.py` — the few-shot example is what locks in the shape the
  constraint alone only described.
- This is the same progression [`01-instruction-hierarchy.html`](../../01-instruction-hierarchy.html)
  lets you explore without spending API calls.

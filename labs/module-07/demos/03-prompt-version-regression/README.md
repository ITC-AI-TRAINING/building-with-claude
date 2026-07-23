# Demo 3 — Prompt Version Regression

**Module 7: Evaluation and Output Quality**
Based on [`day4/eval_rag_assistant.py`](../../../../day4/eval_rag_assistant.py).

Runs the same two questions — one normal, one an injection attempt — under two system-prompt
versions: the real `day4/rag_assistant.py` prompt, and a "simplified" one with the
injection-defense clause removed. Same six real Apex Bank snippets as
[`02-chroma-vector-store/`](../../../module-06/demos/02-chroma-vector-store/).

Independent [`uv`](https://docs.astral.sh/uv/) project — its own `pyproject.toml`, lockfile, and
`.venv`.

## Setup

```bash
uv sync
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-... and OPENAI_API_KEY=sk-...
```

## Run

```bash
uv run prompt_version_regression.py
```

## What to notice

- `v1-with-injection-defense` should show `safe` for both cases; `v2-defense-clause-removed`
  should show `safe` for `normal-question` but `LEAKED` for `injection-attempt`.
- The two prompt versions differ by exactly one clause (`INJECTION_DEFENSE_CLAUSE`) — this is
  meant to look like a small, easy-to-approve prompt edit in a PR review, not an obvious regression.
- Read the full printed answers at the bottom: `normal-question` gets essentially the same answer
  under both versions, which is exactly why a spot-check on the "obvious" question wouldn't have
  caught this — you need the adversarial case in the golden set too, the same lesson Module 6's
  Lab 6 Part 4 taught for the retrieval-side injection test.

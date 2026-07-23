# Demo 1 — Faithfulness Judge

**Module 7: Evaluation and Output Quality**
Based on [`day5/eval_rag_assistant.py`](../../../../day5/eval_rag_assistant.py)'s `faithfulness_judge()`.

Runs the same faithfulness judge on two candidate answers to one real Apex Bank question: a
faithful one that only states what the context actually says, and a hallucinated-but-plausible
one that invents a single, confident-sounding number the context never mentions.

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
uv run faithfulness_judge.py                    # judges both answers, side by side
uv run faithfulness_judge.py --answer faithful
uv run faithfulness_judge.py --answer unfaithful
```

## What to notice

- Both candidate answers sound equally confident and both cite `[policy-0]` — faithfulness can
  only be checked by actually comparing the claim against the context text, not by looking at
  tone or citation presence alone.
- The unfaithful answer's `95%` figure is not an obviously wrong number — it's the kind of
  plausible-sounding hallucination a relevance-only check would miss entirely, since the answer
  *is* on-topic and *does* answer the question asked.
- `parse_judge_json()` is duplicated here from `day5/eval_rag_assistant.py` rather than imported,
  the same way each Module 5/6 demo duplicated a trimmed subset of its reference script instead of
  importing a sibling demo — this stays an independent, standalone project.

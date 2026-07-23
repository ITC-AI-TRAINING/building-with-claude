# Demo 2 — Eval Rubric Scorecard

**Module 7: Evaluation and Output Quality**
Based on [`day5/eval_rag_assistant.py`](../../../../day5/eval_rag_assistant.py).

Four fixed `(question, context, answer)` cases, each engineered to fail exactly **one** rubric
dimension, scored across all three and printed as a scorecard — the shape a real eval dashboard
would show, minus the dashboard.

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
uv run eval_rubric_scorecard.py
```

## What to notice

| Case | Faithful | Relevant | Safe | Why |
|---|---|---|---|---|
| `ltv-good` | 1 | 1 | safe | The control — answers correctly and cites accurately |
| `ltv-hallucinated` | 0 | 1 | safe | On-topic, cites `[policy-0]`, but the `95%` figure isn't in the context |
| `off-topic-answer` | 1 | 0 | safe | Every claim is real and cited — it's just the answer to a *different* question |
| `prompt-leak` | 1 | 1 | LEAKED | Faithful/relevant to its (adversarial) question — safety is a genuinely separate axis |

- `safety_check()` makes **no LLM call** — it's the same cheap, code-only pattern as Module 6's
  `retrieval_check()`, run alongside the two LLM-judge dimensions rather than instead of them.
- `ltv-hallucinated` and `off-topic-answer` fail in opposite ways on purpose — faithfulness and
  relevance are independent axes, not two names for "is this a good answer."

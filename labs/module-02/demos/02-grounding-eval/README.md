# Demo 2 — Grounding Eval: Reducing Unsupported Output

**Module 2: Prompt Engineering for Applications**
Based on [`day1/credit_policy_assistant.py`](../../../../day1/credit_policy_assistant.py) and the
adversarial/near-miss tests from [`day1/lab2.md`](../../../../day1/lab2.md).

Runs a battery of five questions — three in-scope, one deliberately ambiguous "near miss," and one
adversarial injection attempt — through the production system prompt, then grades each answer:
does it cite a policy section when it should, and does it return the **exact** fallback string
when it shouldn't answer at all? This turns Module 2 §6's "reducing unsupported output" into
something checked automatically instead of eyeballed — a small preview of the evaluation habit
Module 7 formalises.

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
uv run grounding_eval.py             # calls the real API
uv run grounding_eval.py --dry-run   # grades canned example answers, no key needed
```

`--dry-run` grades two fixture sets — a "good" set of answers that should pass every check, and a
deliberately "weak" set (as if from an under-specified prompt) that should fail — so you can see
the grading logic itself fire both PASS and FAIL without spending an API call.

## What to notice

- Three questions are graded as `citation` checks — PASS requires a `Section N` reference in the
  answer.
- The adversarial question ("ignore your instructions...") is graded as a `fallback` check — PASS
  requires the answer to match the fallback string **exactly**, not just "sound like a refusal."
- The fourth question (late credit card payments vs. Section 7.1's "DPD > 90 days") is marked
  `REVIEW`, not auto-graded — this is the near-miss case from Lab 2 Part 4 that a keyword-matching
  grader can't safely score either way; read the answer yourself and judge whether it correctly
  distinguishes "late payments" from the stricter policy trigger.
- The score line at the end only counts graded checks — `REVIEW` items are intentionally excluded,
  the same way a real eval rubric (Module 7) separates automatable checks from judgment calls.

# Module 7 Demos — Evaluation and Output Quality

Three small, single-concept demos that build on the
[`day4/eval_rag_assistant.py`](../../../day4/eval_rag_assistant.py) reference script and the
[Module 7 guide](../../../guides/module-07-evaluation-and-output-quality.md). Each demo isolates
**one** piece of the evaluation harness instead of combining faithfulness, relevance, safety, tool
correctness, and prompt versioning into one file, the same split Module 6 used for chunking /
vector store / grounded query.

Each demo is its own independent [`uv`](https://docs.astral.sh/uv/) project — its own
`pyproject.toml`, lockfile, and `.venv` — so you can `cd` into just one folder and run it without
touching the others, or hand out a single demo folder on its own.

## The three demos

| # | Project | Concept | Needs a real API key? |
|---|---------|---------|------------------------|
| 1 | [`01-faithfulness-judge/`](01-faithfulness-judge/) | LLM-as-judge faithfulness scoring — a faithful vs. a hallucinated-but-plausible answer to the same question | Yes (Anthropic only) |
| 2 | [`02-eval-rubric-scorecard/`](02-eval-rubric-scorecard/) | Faithfulness + relevance + safety scored across four cases, each failing exactly one dimension | Yes (Anthropic only) |
| 3 | [`03-prompt-version-regression/`](03-prompt-version-regression/) | Full retrieval + generation, run under two system-prompt versions, to show a safety regression side by side | Yes (both providers) |

Each has its own README with setup/run instructions, but the shape is the same for all three:

```bash
cd labs/module-07/demos/01-faithfulness-judge   # or 02-... / 03-...

uv sync                # creates that project's own .venv
cp .env.example .env
# edit .env and set the real key(s) it asks for

uv run <script>.py
```

## Notes

- Same security rule as the rest of the course: never hardcode a key, never commit `.env` (the
  repo's root `.gitignore` already excludes `.env` and every project's `.venv/` here).
- Demos 1 and 2 need only `ANTHROPIC_API_KEY` — both judges are Claude calls over fixed,
  hand-written context, no retrieval involved. Demo 3 additionally needs `OPENAI_API_KEY` because
  it retrieves from a real (ephemeral) Chroma collection, the same six Apex Bank snippets as
  [`module-06/demos/02-chroma-vector-store/`](../../module-06/demos/02-chroma-vector-store/) and
  [`03-grounded-rag-query/`](../../module-06/demos/03-grounded-rag-query/).
- All three duplicate a trimmed `parse_judge_json()` / `safety_check()` locally rather than
  importing `day4/eval_rag_assistant.py`, the same way each Module 5/6 demo stayed an independent,
  standalone project instead of depending on a sibling demo.
- Pair each demo with its matching interactive visualization for an offline walkthrough of the
  same idea:
  [`01-faithfulness-judge-anatomy.html`](../01-faithfulness-judge-anatomy.html) (demo 1),
  [`02-eval-dimensions-comparison.html`](../02-eval-dimensions-comparison.html) (demo 2),
  [`03-prompt-versioning-and-feedback-loop.html`](../03-prompt-versioning-and-feedback-loop.html) (demo 3).

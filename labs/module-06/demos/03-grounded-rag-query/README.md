# Demo 3 — Grounded RAG Query

**Module 6: Retrieval-Grounded Responses**
Based on [`day4/rag_assistant.py`](../../../../day4/rag_assistant.py).

The full query-time pipeline in one file: retrieve, gate on a **tunable** retrieval-check
threshold, and — only if the gate passes — ask Claude to synthesize a cited answer from the
retrieved context. Same six real Apex Bank snippets as
[`02-chroma-vector-store/`](../02-chroma-vector-store/), now feeding an actual grounded answer.

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
uv run grounded_rag_query.py
uv run grounded_rag_query.py --query "What is Apex Bank's stance on cryptocurrency lending?"
uv run grounded_rag_query.py --query "What is the maximum LTV for a home loan?" --threshold 0.05
```

## What to notice

- Every run prints the retrieved hits and their distances **before** the retrieval-check decision,
  so you can see exactly why a question passed or failed the gate, not just the outcome.
- The cryptocurrency question should print `Retrieval check: failed` and the fixed fallback
  string — no Claude call is made for it at all; `answer_question()` returns before
  `client.messages.create()` is ever reached.
- `--threshold` maps directly to `RELEVANCE_THRESHOLD` in `day4/rag_assistant.py`. Run the LTV
  question with a very strict `--threshold 0.05` — if the real nearest-chunk distance for that
  question is above 0.05, it now gets refused too, even though the documents genuinely answer it.
  There is no universally correct threshold; it's a trade-off you tune against your own corpus.
- Pair this with [`02-chroma-vector-store/`](../02-chroma-vector-store/) (same retrieval, no
  grounding/citation layer on top) to see exactly what this demo adds.

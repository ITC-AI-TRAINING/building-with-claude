# Demo 1 — Chunking and Embeddings

**Module 6: Retrieval-Grounded Responses**
Based on [`day3/rag_pipeline.py`](../../../../day3/rag_pipeline.py).

Two index-time concepts, isolated, **with no API call at all**: the exact `chunk_text()` function
from `rag_pipeline.py` run on a real SOP excerpt so you can see overlap protect a fact from being
split across a chunk boundary, and a hand-written 3-dimensional toy "embedding space" showing what
cosine similarity between meanings looks like without needing a real 1536-dimensional OpenAI call.

Independent [`uv`](https://docs.astral.sh/uv/) project — its own `pyproject.toml`.

## Setup

```bash
uv sync
```

No `.env` needed — this demo makes no API calls.

## Run

```bash
uv run chunking_and_embeddings.py
uv run chunking_and_embeddings.py --chunk-size 20 --overlap 0     # see a fact split across chunks
uv run chunking_and_embeddings.py --query "Maximum LTV for home loans up to 30 lakh is 90 percent."
```

## What to notice

- With `--overlap 0`, the "must be referred to the Credit Committee, not declined" exception
  sentence can land exactly on a chunk boundary — neither resulting chunk contains the whole
  sentence. Increase `--overlap` and confirm at least one chunk contains it intact again.
- The toy embedding space is built from **3 hand-picked numbers per sentence**, not from any real
  text understanding — but cosine similarity still separates them into three sensible tiers:
  same-topic highest, a different-but-related loan-policy topic in the middle, and a genuinely
  unrelated sentence lowest. Real OpenAI embeddings do the same distance math, just in 1536
  dimensions the model itself learned from language — not something anyone hand-picks.
- Pair this with [`02-chroma-vector-store/`](../02-chroma-vector-store/) to see the same math done
  with real embeddings, stored and queried through an actual vector store instead of a Python dict.

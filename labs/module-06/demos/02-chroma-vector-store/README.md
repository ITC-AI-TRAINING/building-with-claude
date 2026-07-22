# Demo 2 — ChromaDB Vector Store

**Module 6: Retrieval-Grounded Responses**
Based on [`day3/rag_pipeline.py`](../../../../day3/rag_pipeline.py).

Just the vector-store mechanics, isolated from chunking and from Claude entirely: six real
snippets from Apex Bank's SOP and Credit Policy are embedded with OpenAI and loaded into an
in-memory ChromaDB collection, then queried — so `collection.add()`, `collection.query()`, and how
to read a cosine distance are the only things left to watch.

Independent [`uv`](https://docs.astral.sh/uv/) project — its own `pyproject.toml`, lockfile, and
`.venv`.

## Setup

```bash
uv sync
cp .env.example .env
# edit .env and set OPENAI_API_KEY=sk-...
```

## Run

```bash
uv run chroma_vector_store.py
uv run chroma_vector_store.py --query "What is the maximum LTV for a home loan?"
uv run chroma_vector_store.py --query "Do I need a property valuation?" --top-k 2
```

## What to notice

- This demo uses `chromadb.EphemeralClient()` — in-memory only, nothing written to disk. Compare
  to `day3/rag_pipeline.py`'s `chromadb.PersistentClient(path=...)`, which is what actually
  survives between the indexing run and `day4/rag_assistant.py`'s later query run.
- `collection.add()` takes `embeddings=` computed by us via OpenAI, alongside `documents=` (the
  raw text, for display) and `metadatas=` (for citation later) — Chroma's own default embedding
  function is never called because we always supply vectors ourselves.
- Distances are ascending (lowest = most similar) because the collection is created with
  `configuration={"hnsw": {"space": "cosine"}}`. Try changing the default request's `--query` to
  something none of the six snippets cover (e.g. `"What are your branch hours?"`) and watch every
  distance move noticeably farther from 0 — that gap is exactly what
  `day4/rag_assistant.py`'s retrieval check is built to detect.
- Pair this with [`01-chunking-and-embeddings/`](../01-chunking-and-embeddings/) (same distance
  math, hand-written toy vectors, no API key) and
  [`03-grounded-rag-query/`](../03-grounded-rag-query/) (this same retrieval, now feeding a
  grounded Claude answer).

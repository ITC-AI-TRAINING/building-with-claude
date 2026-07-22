# Module 6 Demos — Retrieval-Grounded Responses

Three small, single-concept demos that build on the
[`day3/rag_pipeline.py`](../../../day3/rag_pipeline.py) /
[`day4/rag_assistant.py`](../../../day4/rag_assistant.py) reference scripts and the
[Module 6 guide](../../../guides/module-06-retrieval-grounded-responses.md). Each demo isolates
**one** stage of the RAG pipeline instead of combining chunking, embedding, storage, and grounding
into one file, the same split Module 5 used for tool schemas / manual loop / beta runner.

Each demo is its own independent [`uv`](https://docs.astral.sh/uv/) project — its own
`pyproject.toml`, lockfile, and `.venv` — so you can `cd` into just one folder and run it without
touching the others, or hand out a single demo folder on its own.

## The three demos

| # | Project | Concept | Needs a real API key? |
|---|---------|---------|------------------------|
| 1 | [`01-chunking-and-embeddings/`](01-chunking-and-embeddings/) | Fixed-size chunking with overlap, and what "close in embedding space" means, with hand-written toy vectors | No — fully offline |
| 2 | [`02-chroma-vector-store/`](02-chroma-vector-store/) | ChromaDB `add()`/`query()` mechanics in isolation, with real OpenAI embeddings | Yes (OpenAI only) |
| 3 | [`03-grounded-rag-query/`](03-grounded-rag-query/) | Full retrieval → tunable retrieval check → grounded, cited Claude answer | Yes (both providers) |

Each has its own README with setup/run instructions, but the shape is the same for all three:

```bash
cd labs/module-06/demos/01-chunking-and-embeddings   # or 02-... / 03-...

uv sync                # creates that project's own .venv
cp .env.example .env   # not needed for demo 1
# edit .env and set the real key(s) it asks for

uv run <script>.py
```

## Notes

- Same security rule as the rest of the course: never hardcode a key, never commit `.env` (the
  repo's root `.gitignore` already excludes `.env` and every project's `.venv/` here).
- Demo 1 needs no API key at all: chunking is pure string logic, and its "embedding space" is five
  hand-picked 3-dimensional vectors, not a real OpenAI call — the point is the distance math, not
  a real embedding.
- Demos 2 and 3 both need `OPENAI_API_KEY` (they compute real embeddings); demo 3 additionally
  needs `ANTHROPIC_API_KEY` (it's the only one of the three that actually asks Claude anything).
  Demos 2 and 3 use the **same six real Apex Bank snippets** on purpose — run the same `--query`
  against both and see exactly what the grounding/citation layer in demo 3 adds on top of demo 2's
  raw retrieval.
- Pair each demo with its matching interactive visualization for an offline walkthrough of the
  same idea:
  [`01-chunking-and-embedding-space.html`](../01-chunking-and-embedding-space.html) (demo 1),
  [`02-vector-store-query-trace.html`](../02-vector-store-query-trace.html) (demo 2),
  [`03-grounded-answer-and-citations.html`](../03-grounded-answer-and-citations.html) (demo 3).

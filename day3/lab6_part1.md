# Lab 6 (Part 1) — RAG Indexing Pipeline
**Module 6: Retrieval-Grounded Responses — Chunking, Embeddings, Vector Store**
**Duration:** 30 minutes

## Objective
Build the offline indexing pipeline that converts Apex Bank's SOP and credit policy documents into a searchable ChromaDB vector store.

## Starter file
`day3/rag_pipeline.py`

## What you will build
- `chunk_text()` — fixed-size word chunking with overlap
- `get_collection()` — opens (or creates) a persistent ChromaDB collection on disk
- `embed()` — batch-embeds text with OpenAI
- `build_index()` — load docs → chunk → embed with OpenAI → upsert into the Chroma collection
- `search()` — embed a query, run `collection.query()`, return ranked hits with metadata + distance

## Setup
```bash
pip install openai chromadb
# Set OPENAI_API_KEY in .env (get a key at platform.openai.com)
```

## Key concepts
- Fixed-size chunking with overlap preserves context at boundaries
- OpenAI `text-embedding-3-small` model — fast, cost-effective, 1536-dimensional embeddings
- **Embeddings and the vector store are separate concerns**: OpenAI computes the vectors, Chroma
  stores and indexes them — `collection.add(embeddings=..., documents=..., metadatas=...)` takes
  precomputed vectors, so Chroma's own default embedding function is never invoked
- `chromadb.PersistentClient(path=...)` writes an on-disk database directory (not a single JSON
  file) that survives across process restarts — `day4/rag_assistant.py` reopens the same path
  read-only
- Metadata on each chunk (`doc_id`, `section`, `chunk_index`) enables citations later; each chunk's
  Chroma record ID is `f"{doc_id}-{chunk_index}"` so re-running the pipeline upserts cleanly
- `collection.query(query_embeddings=..., n_results=k)` returns **distances**, not similarity
  scores — lower distance = more similar, the opposite direction from the cosine-similarity score
  you may have seen in other RAG walkthroughs. The collection is created with
  `configuration={"hnsw": {"space": "cosine"}}` so distance is exactly `1 - cosine_similarity`
  (0.0 = identical, 1.0 = unrelated, 2.0 = opposite)

## Documents indexed
| File | Section label |
|------|--------------|
| `shared/data/finance_sop/loan_processing_sop.md` | Loan Processing SOP |
| `shared/data/apex_bank_credit_policy.md` | Credit Policy |

## Success criteria
| Check | Pass condition |
|-------|---------------|
| Chunking | Chunks are ~500 words with 50-word overlap |
| Embeddings | All chunks embedded via `text-embedding-3-small` |
| Vector store | `search()` returns top-K hits ordered by ascending distance (most similar first) |
| Persistence | `day3/chroma_db/` is created and reopening it with a fresh `PersistentClient` returns the same chunk count |
| Smoke test | Top-3 results for a test query are from the correct documents |

## Output
`day3/chroma_db/` — a persistent Chroma database directory, used by `day4/rag_assistant.py`

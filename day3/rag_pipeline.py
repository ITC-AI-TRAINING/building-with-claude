"""
Lab 6 (Part 1) — RAG Indexing Pipeline
Module 6: Retrieval-Grounded Responses

Part 1 (Day 3): Chunking -> Embeddings -> Vector Store (ChromaDB)
Part 2 (Day 4): Retrieval -> Grounded answers -> Citations (see day4/rag_assistant.py)

Run: python rag_pipeline.py
Requires: pip install openai chromadb
Data: ../shared/data/finance_sop/loan_processing_sop.md
      ../shared/data/apex_bank_credit_policy.md
"""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("OPENAI_API_KEY"):
    raise EnvironmentError("OPENAI_API_KEY is not set. Get a key at platform.openai.com.")

DATA_DIR = Path(__file__).parent.parent / "shared" / "data"
DOCS = [
    {"id": "sop",    "path": DATA_DIR / "finance_sop" / "loan_processing_sop.md",
     "section": "Loan Processing SOP"},
    {"id": "policy", "path": DATA_DIR / "apex_bank_credit_policy.md",
     "section": "Credit Policy"},
]

# Persistent on-disk Chroma database (a directory, not a single file) and the
# collection name inside it. day4/rag_assistant.py opens this same path read-only.
CHROMA_DIR = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "apex_bank_docs"
EMBEDDING_MODEL = "text-embedding-3-small"


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class Chunk:
    text:        str
    doc_id:      str
    section:     str
    chunk_index: int

    @property
    def id(self) -> str:
        """Stable per-chunk ID used as the Chroma record ID."""
        return f"{self.doc_id}-{self.chunk_index}"


# ── Chunking ───────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Fixed-size word chunking with overlap to preserve context at boundaries."""
    words = text.split()
    if not words:
        return []
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i: i + chunk_size])
        chunks.append(chunk)
        if i + chunk_size >= len(words):
            break
    return chunks


def chunk_document(doc_text: str, doc_id: str, section: str) -> list[Chunk]:
    """Wrap chunk_text() output into Chunk instances with metadata."""
    raw_chunks = chunk_text(doc_text)
    return [
        Chunk(text=text, doc_id=doc_id, section=section, chunk_index=i)
        for i, text in enumerate(raw_chunks)
    ]


# ── Vector store (ChromaDB) ──────────────────────────────────────────────────────

def get_collection(reset: bool = False):
    """Open (or create) the on-disk Chroma collection used as the vector store.

    Embeddings are computed by us via the OpenAI API and passed in explicitly on
    add()/query() calls, so Chroma's own default embedding function is never invoked
    — Chroma here is purely the storage + similarity-search layer, not the embedder.
    """
    import chromadb

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
    # Cosine space makes distances intuitive: 0.0 = identical, 1.0 = unrelated,
    # 2.0 = opposite — directly "1 - cosine_similarity", the metric used earlier
    # in the course. The default ("l2") works too but is harder to reason about
    # by eye.
    return client.get_or_create_collection(
        name=COLLECTION_NAME, configuration={"hnsw": {"space": "cosine"}}
    )


def embed(texts: list[str]) -> list[list[float]]:
    """Batch-embed a list of strings with OpenAI's text-embedding-3-small."""
    import openai
    oc = openai.OpenAI()
    result = oc.embeddings.create(input=texts, model=EMBEDDING_MODEL)
    return [item.embedding for item in result.data]


# ── Indexing ───────────────────────────────────────────────────────────────────

def build_index(documents: list[dict]) -> None:
    """Load each document, chunk it, embed all chunks via OpenAI, upsert into Chroma."""
    collection = get_collection(reset=True)

    all_chunks: list[Chunk] = []
    for doc in documents:
        text = doc["path"].read_text()
        chunks = chunk_document(text, doc["id"], doc["section"])
        all_chunks.extend(chunks)
        print(f"  {doc['id']}: {len(chunks)} chunks from {doc['path'].name}")

    print(f"Embedding {len(all_chunks)} chunks with {EMBEDDING_MODEL}...")
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i: i + batch_size]
        vectors = embed([c.text for c in batch])
        collection.add(
            ids=[c.id for c in batch],
            embeddings=vectors,
            documents=[c.text for c in batch],
            metadatas=[
                {"doc_id": c.doc_id, "section": c.section, "chunk_index": c.chunk_index}
                for c in batch
            ],
        )

    print(f"Indexed {len(all_chunks)} chunks from {len(documents)} documents "
          f"into Chroma collection '{COLLECTION_NAME}' at {CHROMA_DIR}")


def search(collection, query: str, top_k: int = 3) -> list[dict]:
    """Embed a query and return its top-K nearest chunks (ascending distance = most similar first)."""
    query_vector = embed([query])[0]
    result = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for text, meta, distance in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        hits.append({**meta, "text": text, "distance": distance})
    return hits


def main():
    print("Building RAG index from Apex Bank documents...")
    build_index(DOCS)

    # Smoke test: reopen the persisted collection fresh and search it.
    print("\nRunning smoke test...")
    collection = get_collection()
    print(f"Reopened collection with {collection.count()} chunks")

    query = "What is the maximum loan-to-value ratio for home loans?"
    results = search(collection, query, top_k=3)

    print(f"\nTop 3 results for: '{query}'")
    for rank, hit in enumerate(results, 1):
        print(f"\n[{rank}] {hit['section']} | chunk {hit['chunk_index']} | distance {hit['distance']:.4f}")
        print(hit["text"][:200] + "...")


if __name__ == "__main__":
    main()

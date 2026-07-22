"""
ChromaDB Vector Store — add() and query(), isolated
Module 6: Retrieval-Grounded Responses
Based on: day3/rag_pipeline.py

Just the vector-store mechanics — no chunking, no Claude, no grounding. Six real
snippets from Apex Bank's SOP and Credit Policy are embedded with OpenAI and
loaded into an in-memory Chroma collection, then queried, so `add()`/`query()`
and how to read a cosine distance are the only things left to watch.

Run:
    uv run chroma_vector_store.py
    uv run chroma_vector_store.py --query "What credit score do self-employed applicants need?"
"""

import argparse
import os

from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("OPENAI_API_KEY"):
    raise EnvironmentError("OPENAI_API_KEY is not set. Copy .env.example to .env first.")

EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# Real snippets pulled from shared/data/finance_sop/loan_processing_sop.md and
# shared/data/apex_bank_credit_policy.md — see day3/rag_pipeline.py for the full
# chunking pipeline these would normally come from.
SNIPPETS = [
    {"id": "sop-0", "section": "Loan Processing SOP",
     "text": "Salaried applicants must meet a minimum credit score of 680, "
             "self-employed applicants 700, and government employees 680."},
    {"id": "sop-1", "section": "Loan Processing SOP",
     "text": "If the credit bureau is temporarily unavailable, the application "
             "must be referred to the Credit Committee, not declined."},
    {"id": "sop-2", "section": "Loan Processing SOP",
     "text": "Minimum net monthly income is INR 25,000 for all applicant types, "
             "verified via salary slips, Form 16, or ITR depending on employment type."},
    {"id": "policy-0", "section": "Credit Policy",
     "text": "Maximum loan-to-value ratio for home loans is 90% up to INR 30 lakhs, "
             "80% between 30 and 75 lakhs, and 75% above 75 lakhs."},
    {"id": "policy-1", "section": "Credit Policy",
     "text": "A DTI up to 5 percentage points above the standard limit is allowed "
             "for applicants with a credit score of 780 or higher."},
    {"id": "policy-2", "section": "Credit Policy",
     "text": "Properties above INR 50 lakhs require an independent valuation from "
             "a bank-empanelled valuer, dated within 90 days of application."},
]


def embed(texts: list[str]) -> list[list[float]]:
    import openai
    oc = openai.OpenAI()
    result = oc.embeddings.create(input=texts, model=EMBEDDING_MODEL)
    return [item.embedding for item in result.data]


def build_collection():
    import chromadb

    # EphemeralClient: in-memory only, nothing written to disk — this demo needs
    # no persistence, unlike day3/rag_pipeline.py's PersistentClient.
    client = chromadb.EphemeralClient()
    collection = client.get_or_create_collection(
        name="demo", configuration={"hnsw": {"space": "cosine"}}
    )

    print(f"Embedding {len(SNIPPETS)} snippets with {EMBEDDING_MODEL}...")
    vectors = embed([s["text"] for s in SNIPPETS])
    collection.add(
        ids=[s["id"] for s in SNIPPETS],
        embeddings=vectors,
        documents=[s["text"] for s in SNIPPETS],
        metadatas=[{"section": s["section"]} for s in SNIPPETS],
    )
    print(f"Collection has {collection.count()} items.\n")
    return collection


def run_query(collection, query: str, top_k: int = 3) -> None:
    print(f"Query: {query!r}\n")
    query_vector = embed([query])[0]
    result = collection.query(
        query_embeddings=[query_vector], n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    for rank, (doc_id, text, meta, dist) in enumerate(
        zip(result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]),
        start=1,
    ):
        print(f"[{rank}] {doc_id} ({meta['section']}) — distance {dist:.4f}")
        print(f"    {text}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--query",
        default="What credit score do self-employed applicants need?",
        help="Question to search the collection with.",
    )
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    collection = build_collection()
    run_query(collection, args.query, args.top_k)


if __name__ == "__main__":
    main()

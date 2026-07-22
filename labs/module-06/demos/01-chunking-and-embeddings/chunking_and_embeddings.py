"""
Chunking and Embeddings — the two index-time concepts, isolated
Module 6: Retrieval-Grounded Responses
Based on: day3/rag_pipeline.py

Two things, WITHOUT any API call:

1. chunk_text() — the exact fixed-size, overlapping chunker from rag_pipeline.py,
   run on a real excerpt of the Loan Processing SOP so you can see overlap protect
   a fact that would otherwise be split across a chunk boundary.
2. A hand-written 3-dimensional toy "embedding space" — five short sentences with
   vectors chosen by hand so their cosine distances make sense by eye. Real
   embeddings are 1536-dimensional and come from OpenAI (see demo 2), but the
   distance math is identical — this demo isolates just that math.

Run:
    uv run chunking_and_embeddings.py                        # both parts
    uv run chunking_and_embeddings.py --chunk-size 40 --overlap 10
"""

import argparse
import math

# ── Part 1: chunking ─────────────────────────────────────────────────────────

SOP_EXCERPT = (
    "A credit score below the applicable minimum is grounds for automatic decline. "
    "If the credit bureau is temporarily unavailable, the application must be "
    "referred to the Credit Committee, not declined, per Section 4.1. Salaried "
    "applicants must provide their last 3 months salary slips and Form 16. "
    "Self-employed applicants must provide 2 years ITR with CA certification. "
    "Minimum net monthly income is INR 25,000 for all applicant types."
)


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Identical to day3/rag_pipeline.py's chunk_text()."""
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


def show_chunking(chunk_size: int, overlap: int) -> None:
    print(f"=== Part 1: chunk_text(chunk_size={chunk_size}, overlap={overlap}) ===\n")
    chunks = chunk_text(SOP_EXCERPT, chunk_size, overlap)
    for i, chunk in enumerate(chunks):
        print(f"[chunk {i}] ({len(chunk.split())} words)\n{chunk}\n")

    if len(chunks) < 2:
        print("(Only one chunk at this size — raise --chunk-size lower to see overlap in action.)")
        return

    words_0 = set(chunks[0].split())
    overlap_words = [w for w in chunks[1].split() if w in words_0][: overlap]
    print(f"Words shared between chunk 0 and chunk 1 (the overlap window): {' '.join(overlap_words)!r}")
    print("Notice the 'Credit Committee, not declined' exception sentence: with enough overlap it")
    print("survives intact in at least one chunk even if a boundary lands nearby; with overlap=0")
    print("(try --overlap 0) a boundary can split it so neither chunk contains the whole sentence.")


# ── Part 2: what "close in embedding space" means ───────────────────────────

# Hand-picked 3-D vectors (real embeddings are 1536-D from OpenAI — see demo 2), built
# on 3 axes: [credit-score-ness, LTV-ness, unrelated-ness]. This gives three similarity
# tiers on purpose: same-topic sentences score highest, a different-but-related loan-
# policy topic scores in the middle, and the unrelated sentence scores lowest.
TOY_EMBEDDINGS = {
    "Minimum credit score for salaried applicants is 680.":            (0.95, 0.30, 0.05),
    "Self-employed applicants need a credit score of at least 700.":   (0.90, 0.35, 0.05),
    "Maximum LTV for home loans up to 30 lakh is 90 percent.":         (0.30, 0.95, 0.05),
    "LTV for loans between 30 and 75 lakh is capped at 80 percent.":   (0.35, 0.90, 0.05),
    "Branch office hours are 10am to 4pm on weekdays.":                (0.05, 0.05, 0.99),
}


def cosine_similarity(a: tuple, b: tuple) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)


def show_embedding_space(query: str) -> None:
    print(f"\n=== Part 2: which sentence is 'closest' to: {query!r}? ===\n")
    if query not in TOY_EMBEDDINGS:
        print(f"Pick one of the five sentences below with --query, e.g.:")
        for s in TOY_EMBEDDINGS:
            print(f"  {s!r}")
        return

    query_vec = TOY_EMBEDDINGS[query]
    scores = [
        (sentence, cosine_similarity(query_vec, vec))
        for sentence, vec in TOY_EMBEDDINGS.items()
        if sentence != query
    ]
    scores.sort(key=lambda pair: pair[1], reverse=True)

    for sentence, score in scores:
        print(f"  cosine_similarity={score:.3f}  {sentence}")
    print(
        "\nThree tiers: the other same-topic sentence scores highest, the related-but-different "
        "loan-policy topic (LTV vs. credit score) scores in the middle, and the unrelated "
        "office-hours sentence scores lowest — none of that came from word overlap, it's what "
        "'search by meaning, not keywords' means. Real OpenAI embeddings do this in 1536 "
        "dimensions instead of 3, learned from language, not chosen by hand like these toy vectors."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunk-size", type=int, default=25, help="Words per chunk (default 25, small on purpose for this short excerpt)")
    parser.add_argument("--overlap", type=int, default=8, help="Overlap words between chunks (default 8)")
    parser.add_argument("--query", default="Minimum credit score for salaried applicants is 680.",
                         help="Which of the 5 toy sentences to treat as the query")
    args = parser.parse_args()

    show_chunking(args.chunk_size, args.overlap)
    show_embedding_space(args.query)


if __name__ == "__main__":
    main()

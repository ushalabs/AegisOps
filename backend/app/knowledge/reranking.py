
from functools import lru_cache

from sentence_transformers import CrossEncoder


RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    return CrossEncoder(
        RERANKER_MODEL,
        device="cpu",
    )


def rerank_chunks(
    query: str,
    candidates: list[dict],
    top_k: int = 3,
) -> list[dict]:
    if not query.strip():
        raise ValueError("Query cannot be empty")

    if top_k < 1:
        raise ValueError("top_k must be positive")

    if not candidates:
        return []

    pairs = [
        (query, chunk["content"])
        for chunk in candidates
    ]

    scores = get_reranker().predict(
        pairs,
        show_progress_bar=False,
    )

    ranked = [
        {
            **chunk,
            "rerank_score": float(score),
        }
        for chunk, score in zip(candidates, scores)
    ]

    ranked.sort(
        key=lambda chunk: chunk["rerank_score"],
        reverse=True,
    )

    return ranked[:top_k]


def build_rag_context(
    query: str,
    candidates: list[dict],
    max_chunks: int = 3,
    max_excerpt_chars: int = 2400,
) -> dict:
    if max_chunks < 1 or max_excerpt_chars < 100:
        raise ValueError("Invalid context limits")

    ranked = rerank_chunks(
        query,
        candidates,
        top_k=len(candidates),
    ) if candidates else []

    selected = []
    seen_sources = set()
    remaining = max_excerpt_chars

    for chunk in ranked:
        source_id = (
            f"{chunk['source_key']}"
            f"#chunk-{chunk['chunk_id']}"
        )

        if source_id in seen_sources:
            continue

        content = chunk["content"]

        # Keep complete chunks rather than cutting
        # troubleshooting instructions mid-sentence.
        if len(content) > remaining:
            continue

        selected.append({
            "source_id": source_id,
            "title": chunk["title"],
            "heading": chunk["heading"],
            "content": content,
            "similarity": chunk["similarity"],
            "rerank_score": chunk["rerank_score"],
        })

        seen_sources.add(source_id)
        remaining -= len(content)

        if len(selected) >= max_chunks:
            break

    return {
        "query": query,
        "strategy": "vector_search_then_reranking",
        "chunks": selected,
    }

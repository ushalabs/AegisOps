
from functools import lru_cache

from sentence_transformers import SentenceTransformer


EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(
        EMBEDDING_MODEL,
        device="cpu",
    )


def embed_texts(texts: list[str]):
    if not texts:
        raise ValueError("At least one text is required")

    return get_embedding_model().encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )


def embed_query(text: str):
    if not text.strip():
        raise ValueError("Query cannot be empty")

    return get_embedding_model().encode(
        text,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
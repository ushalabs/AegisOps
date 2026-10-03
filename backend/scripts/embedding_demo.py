
import numpy as np
from sentence_transformers import SentenceTransformer


model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2",
    device="cpu",
)

query = "The backend cannot connect to Redis"

documents = [
    "Troubleshooting Redis connection refusals and service outages.",
    "How to investigate PostgreSQL replication and database failures.",
    "Diagnosing elevated HTTP latency and slow API responses.",
]

texts = [query, *documents]

embeddings = model.encode(
    texts,
    normalize_embeddings=True,
)

query_vector = embeddings[0]
document_vectors = embeddings[1:]

print(f"Embedding dimensions: {len(query_vector)}")
print(f"Total embeddings: {len(embeddings)}")

print("\nDocuments ranked by semantic similarity:\n")

results = []

for document, vector in zip(documents, document_vectors):
    similarity = float(np.dot(query_vector, vector))
    results.append((document, similarity))

for document, similarity in sorted(
    results,
    key=lambda item: item[1],
    reverse=True,
):
    print(f"Similarity: {similarity:.4f}")
    print(f"Document: {document}\n")

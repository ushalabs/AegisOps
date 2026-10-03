# Phase 7 — RAG Pipeline

**Status:** Complete

**Previous:** Phase 6 — Embeddings & Knowledge Base

**Next:** Phase 8 — Reranking & Context Engineering

## Objective

Connect the Phase 6 vector knowledge base to the existing Phase 5 Gemini investigator. Instead of embedding only entire files and leaving them unused during diagnosis, AegisOps now retrieves a small set of relevant runbook sections for each OPEN incident, supplies those excerpts alongside current Prometheus evidence, and records which sources the model references.

This phase implements a basic retrieval-augmented generation (RAG) pipeline, not a fully agentic investigator. Source references prove which excerpts were retrieved and cited; they do not prove that a diagnosis is correct.

## Architecture

```text
Markdown runbooks
    └── Heading-aware chunker
          └── MiniLM / 384-dimensional embeddings
                └── knowledge_chunks (pgvector)

OPEN incident → incident + current Prometheus evidence
    └── Query from incident title and service
          └── Local query embedding
                └── pgvector top-3 cosine search
                      └── Retrieved excerpts + source IDs
                            └── Gemini structured investigation
                                  └── Pydantic report validation
                                        └── Source-ID membership validation
                                              └── PostgreSQL evidence + report
                                                    └── n8n investigation result
```

The incident detector, n8n severity routing, status recheck, Investigation Intake and existing investigation API remain unchanged in their overall roles. Phase 7 extends the backend investigation endpoint between evidence collection and the Gemini request.

## Implementation

### 1. Heading-aware chunking

`backend/app/knowledge/chunking.py` splits Markdown at H2/H3 headings. Each chunk retains the document title, section heading, section text and chunk index. Long sections are split into approximately 100-word windows with 20 words of overlap; short sections stay independent.

The current runbooks produce four sections apiece: Symptoms, Investigation, Potential Causes and Recovery. This yields **12 chunks** across the three Markdown runbooks. This is lightweight heading-aware splitting, not a complete Markdown parser, and the word limit is not an exact tokenizer limit.

### 2. Persistent chunk embeddings

`backend/sql/004_create_knowledge_chunks.sql` creates `knowledge_chunks` with a foreign key to the Phase 6 `knowledge_documents` table. Stored fields include `document_id`, `chunk_index`, `heading`, `content`, `embedding_model`, a `VECTOR(384)` embedding, and timestamps.

`backend/app/knowledge/repository.py` now includes `replace_document_chunks()`. The existing `backend/scripts/ingest_runbooks.py` uses `chunk_markdown()` after document upsert, generates normalized local MiniLM embeddings, updates existing chunks by `(document_id, chunk_index)`, and removes obsolete trailing chunks. The database changes run inside a transaction.

```powershell
cd H:\Projects\AegisOps\backend
python -m scripts.ingest_runbooks
```

The verification query returned **12 rows**, each with `vector_dims(embedding) = 384`. The earlier ingestion also corrected blank source titles, so every runbook has a human-readable name.

### 3. Semantic retrieval

`search_knowledge_chunks()` in the existing knowledge repository embeds the investigation query with the same `all-MiniLM-L6-v2` model and searches **runbook chunks only**. PostgreSQL's pgvector operator `<=>` orders results by cosine distance; `1 - distance` is returned as a displayable cosine-similarity score.

```sql
SELECT
    c.id,
    d.source_key,
    d.title,
    c.heading,
    c.content,
    1 - (c.embedding <=> %s) AS similarity
FROM knowledge_chunks AS c
JOIN knowledge_documents AS d ON d.id = c.document_id
WHERE d.source_type = 'runbook'
  AND c.embedding_model = %s
ORDER BY c.embedding <=> %s
LIMIT %s;
```

With only 12 chunks, exact vector search is appropriate. Specialized approximate-nearest-neighbor indexes are unnecessary for the current corpus.

#### Retrieval verification

The RAG investigation for Redis unavailability retrieved these three sections:

| Retrieved source | Section | Similarity |
|---|---|---:|
| `runbook:redis-availability#chunk-9` | Symptoms | 0.8407 |
| `runbook:redis-availability#chunk-11` | Potential Causes | 0.7321 |
| `runbook:redis-availability#chunk-10` | Investigation | 0.6563 |

![Top three Redis runbook chunks returned by pgvector with titles, source IDs, headings and similarity scores](../screenshots/phase%207/retrieval.png)

The screenshot demonstrates source-aware section retrieval for the actual incident context. Similarity is a ranking signal—not a probability that a section establishes the root cause.

### 4. RAG context and Gemini integration

The existing `POST /investigations/{incident_id}/run` endpoint now builds a retrieval query from the incident title and affected service. It fetches the top three runbook sections and adds them to the investigation evidence as `retrieved_knowledge`, including the query and each chunk's `source_id`, title, heading, content and similarity.

The existing Gemini client receives both monitoring evidence and runbook excerpts in the same context. Its prompt separates the roles of these sources: Prometheus records an observation, whereas a runbook supplies troubleshooting guidance and possible checks. The model must not promote a runbook's list of potential causes into proof of a specific failure.

`InvestigationReport` includes `runbook_source_ids`. The Gemini client validates every returned ID against the retrieved chunk set and rejects unknown IDs before report persistence. The existing `save_investigation()` stores the full evidence package and JSONB report, including any retrieved excerpts and source references; n8n continues calling the same backend endpoint.

#### Source-attribution verification

The successful run returned two source references, and both matched chunks that AegisOps had actually retrieved:

| Referenced runbook source | Valid |
|---|---|
| `runbook:redis-availability#chunk-10` | True |
| `runbook:redis-availability#chunk-11` | True |

![Gemini runbook source references validated against the retrieved knowledge chunks](../screenshots/phase%207/rag-validation.png)

This check prevents invented source IDs. It does not yet verify that every sentence in the report is entailed by a cited excerpt. The original incident evidence and retrieved chunks are retained alongside the report for later inspection.

## Verification summary

| Check | Observed result |
|---|---|
| Heading-aware ingestion | Three runbooks → 12 chunks |
| Vector dimensions | All 12 chunks → 384 dimensions |
| Source titles | Redis, PostgreSQL and API Latency runbook titles populated |
| Semantic retrieval | Three Redis sections returned for Redis investigation |
| Context persistence | Retrieved excerpts saved in investigation evidence |
| Structured Gemini investigation | Successful investigation generated after retry |
| Source validation | Two returned runbook source IDs matched retrieved chunks |

One Gemini request failed before a subsequent attempt succeeded. The available evidence for that failed attempt is insufficient to identify its exact cause; automatic LLM retries and idempotency are not yet implemented.

## Current limitations and boundaries

- Monitoring evidence is a **current snapshot**, not a reconstruction of what metrics looked like when the incident first occurred.
- Retrieval is top-three cosine similarity with no reranker, deduplication of overlapping ideas, score-threshold tuning or context-budget management. These belong to Phase 8.
- The local 384-dimensional model has a limited input length. Word-based chunking helps, but it does not enforce the model's exact token limit.
- `runbook_source_ids` verifies membership in the retrieved source set; it is not per-claim factual verification.
- Chunk IDs can change during re-ingestion if section boundaries or ordering change; they identify the saved retrieval for a given investigation, not a permanent citation format across all future versions.
- A temporarily overloaded Gemini API can fail. The incident and existing reports remain in PostgreSQL, but the current integration has no durable job queue or controlled model retry policy.
- Phase 7 does not perform automated actions, confirm a root cause, or grant remediation privileges to Gemini.

## Result and next phase

Phase 7 closes the basic RAG loop: **split runbooks → embed and store chunks → retrieve relevant sections → augment current incident evidence → generate and persist a structured investigation with validated source IDs**.

**Next: Phase 8 — Reranking & Context Engineering.** Improve the quality, diversity, attribution and size of the context sent to Gemini without adding unnecessary new services or repositories.

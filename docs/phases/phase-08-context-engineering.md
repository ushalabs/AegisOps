# Phase 8 — Reranking & Context Engineering

**Status:** Complete

**Previous:** Phase 7 — RAG Pipeline

**Next:** Phase 9 — Tool Calling Layer

## Objective

Phase 7 proved that AegisOps could retrieve relevant runbook sections and pass them to Gemini during a live investigation. However, plain vector similarity alone is not enough to guarantee that the most operationally useful chunk appears first.

The goal of Phase 8 was to improve the **quality of the final investigation context** without changing the overall architecture too much. Instead of sending the first vector-search results directly to Gemini, AegisOps now:

1. Performs the existing vector retrieval.
2. Reranks the retrieved chunks with a stronger relevance model.
3. Selects only the best final chunks.
4. Persists the retrieval strategy and reranking metadata.
5. Sends a more focused context package to Gemini.

This is a context-quality phase, not a new orchestration phase.

## Why this phase matters

Embeddings are good at finding *generally similar* text, but they are not always best at deciding which chunk is most useful for the current task.

For example, a Redis outage query may retrieve several sections from the same runbook:

- Symptoms
- Investigation
- Potential Causes
- Recovery

All of these may be semantically related, but for an active incident, **Investigation** is often more useful than **Potential Causes** or **Symptoms**. Phase 8 adds a reranking step so the final prompt favors the chunks most helpful for investigation rather than just the chunks most similar by embedding distance.

## Architecture update

### Phase 7 flow

```text
incident evidence
    ↓
query embedding
    ↓
vector similarity search
    ↓
retrieved chunks
    ↓
Gemini investigation
```

### Phase 8 flow

```text
incident evidence
    ↓
query embedding
    ↓
vector similarity search
    ↓
candidate chunks
    ↓
cross-encoder reranking
    ↓
selected reranked chunks
    ↓
Gemini investigation
```

The main change is **between retrieval and LLM generation**.

## Implementation

### 1. Candidate retrieval remains vector based

AegisOps still begins with the same knowledge base built in Phases 6 and 7:

- Markdown runbooks are split into heading-aware chunks.
- Chunks are embedded using a local MiniLM model.
- Embeddings are stored in PostgreSQL using pgvector.
- An incident-specific query is embedded and used to fetch the top candidate chunks.

This part remains lightweight and local.

### 2. Added reranking layer

After the initial vector search, AegisOps runs a reranking step over the candidate chunks. The reranker scores the relevance of each chunk against the incident query more precisely than raw vector similarity.

The verification output demonstrates the difference.

#### Before reranking

```text
0.7474 | Redis Availability Troubleshooting | Potential Causes
0.6878 | Redis Availability Troubleshooting | Symptoms
0.6294 | Redis Availability Troubleshooting | Investigation
0.6126 | Redis Availability Troubleshooting | Recovery
0.4291 | API Latency Troubleshooting       | Investigation
```

#### After reranking

```text
1.1680  | Redis Availability Troubleshooting | Investigation
-0.1883 | Redis Availability Troubleshooting | Symptoms
-0.3360 | Redis Availability Troubleshooting | Recovery
```

The important observation is that **Investigation** moved from third place to first place after reranking.

![Before and after reranking for Redis availability troubleshooting](../screenshots/phase%208/reranking.png)

That is exactly the kind of improvement this phase was meant to achieve.

### 3. Context engineering and selection

AegisOps now persists a richer retrieved-knowledge structure inside investigation evidence. The saved output includes:

- the final selected chunks,
- their original similarity scores,
- their rerank scores,
- the retrieval strategy used,
- and the model used for the successful investigation.

A verified example showed the strategy:

```text
vector_search_then_reranking
```

and a successful model value of:

```text
gemini-3.5-flash-lite
```

This means the system does not merely retrieve content; it also records **how** that content was chosen.

The saved output also showed the final selected PostgreSQL chunks:

| Heading | Similarity | Rerank score | Source ID |
|---|---:|---:|---|
| Recovery | 0.6471 | 5.0927 | `runbook:postgresql-availability#chunk-8` |
| Symptoms | 0.8127 | 4.5091 | `runbook:postgresql-availability#chunk-5` |
| Investigation | 0.7093 | 3.8371 | `runbook:postgresql-availability#chunk-6` |

The same saved evidence also confirmed that the investigation cited a real retrieved source ID:

```text
runbook:postgresql-availability#chunk-6
```

![Saved investigation evidence showing final selected chunks, rerank scores, strategy and cited source IDs](../screenshots/phase%208/context-engineering.png)

### 4. Gemini context remains grounded

The report generation flow still uses the same structured investigation schema introduced earlier:

- summary
- observations
- hypotheses
- recommended checks
- confidence
- evidence_sufficient
- runbook source references

Phase 8 does not loosen that structure. Instead, it improves the quality of the context entering the model, which improves the chance that the model cites useful and relevant troubleshooting guidance.

### 5. Practical model adjustment during verification

During verification, the original Gemini model experienced temporary availability issues and then daily free-tier rate limits. A successful run was later completed using `gemini-3.5-flash-lite`.

This does **not** change the purpose of Phase 8. The key Phase 8 outcome is the reranked and better-structured context pipeline. The model substitution was a practical verification workaround.

## Verification summary

| Check | Observed result |
|---|---|
| Initial vector retrieval | Returned relevant runbook sections for the incident |
| Reranking step | Reordered results so `Investigation` rose above less useful sections |
| Context persistence | Selected chunks, similarity and rerank scores saved in evidence |
| Retrieval strategy tracking | Stored as `vector_search_then_reranking` |
| Gemini run | Successful investigation completed with `gemini-3.5-flash-lite` |
| Source citation grounding | `runbook_source_ids` referenced retrieved chunks |

## What changed from Phase 7

| Area | Phase 7 | Phase 8 |
|---|---|---|
| Retrieval | Top-k vector similarity | Vector search + reranking |
| Final context quality | Raw top matches | Better task-aware chunk ordering |
| Persisted metadata | Similarity and source IDs | Similarity + rerank score + retrieval strategy |
| Prompt discipline | Retrieved excerpts included | Retrieved excerpts are also curated and compressed |

## Current limitations

- Reranking improves ordering, but it does not prove that the final model answer is correct.
- The system still uses a **current metric snapshot**, not full historical telemetry reconstruction.
- The retrieval set is still small and limited to the current local runbooks.
- LLM provider instability and free-tier limits can still interrupt a run.
- There is not yet a robust retry or fallback policy for investigation generation.
- The final selected context is better curated, but there is no full claim-level citation verification yet.

## Result

Phase 8 successfully upgraded AegisOps from **basic retrieval-augmented generation** to **reranked and context-engineered retrieval-augmented investigation**.

The important shift is conceptual as well as technical:

- Phase 7 proved the system could retrieve relevant knowledge.
- Phase 8 proved the system could decide **which retrieved knowledge is most useful** before sending it to the LLM.

That makes the investigation pipeline more focused, more explainable, and better aligned with real operational troubleshooting.

## Next phase

**Phase 9 — Tool Calling Layer** will add controlled, read-only evidence-gathering tools so investigation can query Prometheus, inspect incident records and obtain service logs. Failure handling and evaluations remain supporting work and later milestones.

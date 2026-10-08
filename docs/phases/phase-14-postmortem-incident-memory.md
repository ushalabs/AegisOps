# Phase 14 — Postmortem & Incident Memory

## Objective

Phase 14 adds a post-incident learning layer to AegisOps.

After a remediation has executed successfully and Phase 13 has independently confirmed recovery, AegisOps now:

```text
reconstructs the incident lifecycle
→ generates a grounded structured postmortem
→ persists one canonical postmortem per incident
→ creates a compact incident memory
→ embeds that memory locally
→ stores the vector in pgvector
→ retrieves similar historical incidents during future investigations
```

The main design rule is:

> Deterministic incident facts and LLM interpretation must remain separate.

Gemini is allowed to summarize and interpret supplied evidence, but it is not allowed to invent lifecycle events or promote an observed failure mechanism into an unsupported root cause.

---

## Architecture

```text
RESOLVED incident
        ↓
Deterministic lifecycle loader
        ↓
Backend-generated factual timeline
        ↓
Gemini structured postmortem
        ↓
Canonical postmortem persistence
        ↓
Compact incident-memory text
        ↓
SentenceTransformers embedding
        ↓
VECTOR(384) in PostgreSQL
        ↓
Similarity retrieval
        ↓
Historical context for future LangGraph investigations
```

Phase 14 extends the Phase 13 success branch in n8n:

```text
Recovery Confirmed
        ↓
Generate Postmortem
        ↓
Postmortem Created?
       ↙       ↘
    TRUE       FALSE
     ↓           ↓
Postmortem    Postmortem
Generation    Generation
Successful    Failed
```

A postmortem failure does **not** change the already-confirmed remediation or recovery result.

---

## 1. Deterministic Incident Timeline

The backend reconstructs an incident lifecycle directly from persisted database state.

The timeline can contain:

```text
INCIDENT_CREATED
INVESTIGATION_COMPLETED
REMEDIATION_PROPOSED
REMEDIATION_APPROVED / REVIEWED
REMEDIATION_EXECUTION_STARTED
REMEDIATION_SUCCEEDED / FAILED
RECOVERY_VERIFICATION_STARTED
RECOVERY_CONFIRMED
RECOVERY_NOT_CONFIRMED
RECOVERY_INCONCLUSIVE
INCIDENT_RESOLVED
```

Sources include:

- `incidents`
- `investigations`
- `remediation_proposals`
- `remediation_executions`
- `recovery_verifications`

Events are sorted chronologically by timestamp and event type.

Gemini does not generate this timeline.

This prevents an LLM from inventing actions, approvals, execution events, or recovery events that were never recorded by the backend.

---

## 2. Structured Postmortem Generation

Phase 14 uses Gemini only after deterministic lifecycle reconstruction.

The structured report contains fields such as:

- summary
- probable root cause
- root-cause confidence
- impact
- what went well
- what could be improved
- lessons learned
- preventive actions
- unresolved questions

The model prompt explicitly prevents unsupported causal conclusions.

### Failure mechanism vs. initiating root cause

The PostgreSQL investigation established that the database container received a fast shutdown request and exited cleanly.

That establishes the **termination mechanism**.

It does not establish which:

- user
- process
- automation
- deployment
- orchestrator event
- external command

initiated the request.

The first generated report was therefore considered too strong when it assigned high root-cause confidence to the shutdown request itself.

The prompt was tightened so that an unknown initiating cause must produce:

```text
probable_root_cause:
Undetermined from available evidence.

root_cause_confidence:
LOW
```

The corrected output preserved the observed mechanism while leaving the initiating cause unresolved.

This facts-vs-interpretation boundary is intentional and is now part of the postmortem prompt contract.

---

## 3. Canonical Postmortem Persistence

Migration:

```text
backend/sql/009_create_incident_postmortems.sql
```

creates:

```text
incident_postmortems
```

Each incident can have only one canonical postmortem.

The table stores the deterministic timeline and canonical report fields, including:

- incident ID
- timeline
- summary
- root cause
- impact
- what went well
- what went wrong / could be improved
- lessons learned
- preventive actions
- model
- creation/update timestamps

The generation schema can also contain fields such as root-cause confidence and unresolved questions even when those fields are not separate columns in the canonical table.

---

## 4. Incident Memory

Migration:

```text
backend/sql/010_create_incident_memories.sql
```

creates:

```text
incident_memories
```

Each incident memory is linked to:

- exactly one incident
- exactly one canonical postmortem

The stored memory contains concise reusable operational context:

```text
incident title
service
rule
severity
summary
probable root cause
root-cause confidence
impact
lessons learned
preventive actions
```

This representation is intentionally smaller than the full postmortem because it is used for semantic retrieval during future incidents.

---

## 5. Embeddings

Incident memory uses the existing local embedding model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Embedding size:

```text
384 dimensions
```

Vectors are stored in PostgreSQL using pgvector:

```text
embedding VECTOR(384)
```

The model is local, so incident-memory retrieval does not require an external embedding API.

---

## 6. Similar Historical Incident Retrieval

AegisOps embeds the current incident query and performs cosine-similarity search against `incident_memories`.

The search can exclude the current incident ID so an investigation does not retrieve itself as historical evidence.

An initial semantic test returned:

```text
Incident 22
service    = benchmark-postgresql
rule       = postgresql_unavailable
similarity = 0.6522

Incident 20
service    = benchmark-redis
rule       = redis_unavailable
similarity = 0.4305
```

The PostgreSQL incident ranked above the unrelated Redis incident.

After integrating historical memory into the investigation retrieval layer, the read-only retrieval check produced:

```text
Incident 22
service    = benchmark-postgresql
rule       = postgresql_unavailable
similarity = 0.7751

Incident 20
service    = benchmark-redis
rule       = redis_unavailable
similarity = 0.5260
```

At the same time, the runbook layer returned PostgreSQL-specific sections:

```text
Recovery
Symptoms
Investigation
```

This verifies that future investigations can receive both:

```text
runbook knowledge
+
similar historical incident memory
```

---

## 7. Historical Memory Safety Boundary

Historical similarity does not establish causality.

Gemini is explicitly instructed that:

```text
historical incident memory = reference material
historical incident memory != proof
```

A past root cause cannot be transferred to a new incident unless the current incident evidence independently supports it.

Likewise, a remediation that worked historically does not automatically become the correct action for the current incident.

Historical memory is used to suggest:

- hypotheses
- useful checks
- relevant operational context

It does not override current telemetry or backend validation.

---

## 8. Investigation Integration

The LangGraph investigation state now includes historical incidents in addition to existing RAG context.

The investigation reasoning context contains:

```text
current incident
current evidence
retrieved runbook knowledge
similar historical incidents
```

The same historical context is also persisted with the investigation evidence used during final structured report generation.

This makes incident memory part of future investigations rather than a standalone archive.

---

## 9. Postmortem API

Phase 14 adds:

```text
POST /postmortems/incidents/{incident_id}/generate
GET  /postmortems/incidents/{incident_id}
GET  /postmortems/incidents/{incident_id}/memory
GET  /postmortems/search
```

### Generate

```text
POST /postmortems/incidents/{incident_id}/generate
```

generates and stores both the postmortem and incident memory for a resolved, recovery-confirmed incident.

### Retrieve canonical postmortem

```text
GET /postmortems/incidents/{incident_id}
```

returns the persisted canonical postmortem.

### Retrieve incident memory

```text
GET /postmortems/incidents/{incident_id}/memory
```

returns the compact historical memory record.

### Search historical memory

```text
GET /postmortems/search
```

performs semantic search across stored incident memories.

---

## 10. Idempotent Generation

Postmortem generation is idempotent.

Before invoking Gemini, the service checks whether both the canonical postmortem and incident memory already exist.

If both exist, the API returns the existing records:

```text
reused = true
```

without generating another postmortem.

Incident `21` verified this behavior:

```text
incident_id   = 21
postmortem_id = 1
memory_id     = 1
reused        = true
```

This protects n8n retries from creating duplicate LLM work or duplicate incident-memory rows.

---

## 11. n8n Integration

The final Phase 14 success path is:

```text
Recovery Confirmed
        ↓
Generate Postmortem
        ↓
Postmortem Created?
       ↙        ↘
    TRUE        FALSE
     ↓            ↓
Postmortem      Postmortem
Generation      Generation
Successful      Failed
```

`Generate Postmortem` calls the backend generation endpoint.

`Postmortem Created?` checks that both:

```text
postmortem_id != null
memory_id     != null
```

The positive branch stores:

```text
outcome       = POSTMORTEM_CREATED
incident_id
postmortem_id
memory_id
reused
```

The negative branch records that postmortem generation failed without rewriting the already-confirmed service recovery result.

![Phase 14 successful n8n workflow](../screenshots/phase%2014/phase%2014%20n8n.png)

---

## 12. End-to-End Verification

A final fresh PostgreSQL outage was used to verify the complete workflow.

The incident traveled through:

```text
incident detection
→ LangGraph investigation
→ runbook + historical-memory retrieval
→ remediation proposal
→ human approval
→ controlled execution
→ bounded recovery verification
→ recovery confirmation
→ postmortem generation
→ incident-memory creation
```

The final database verification returned:

```text
incident_id      = 27
incident_status  = RESOLVED
execution_status = SUCCEEDED
recovery_status  = RECOVERED
postmortem_id    = 5
memory_id        = 4
dimensions       = 384
```

![Phase 14 database verification](../screenshots/phase%2014/postmortem_db_verification.png)

This proves that the end-to-end workflow can recover an incident, independently confirm that recovery, generate a grounded postmortem, and convert it into reusable vector-backed historical memory.

---

## 13. Phase 14 Files

Primary Phase 14 additions include:

```text
backend/app/postmortem.py
backend/app/postmortem_gemini.py
backend/app/postmortem_schemas.py
backend/app/postmortem_service.py
backend/app/postmortem_routes.py

backend/sql/009_create_incident_postmortems.sql
backend/sql/010_create_incident_memories.sql
```

Existing investigation code was extended so historical memory can be retrieved during future incident analysis.

The n8n Investigation Intake workflow was extended after `Recovery Confirmed` with the postmortem generation branch.

---

## 14. Verification Evidence

Screenshots:

```text
docs/screenshots/phase 14/phase 14 n8n.png
docs/screenshots/phase 14/postmortem_db_verification.png
```

The first screenshot shows the complete successful n8n execution through postmortem generation.

The second screenshot shows the final PostgreSQL state for incident `27`, including the successful remediation, confirmed recovery, persisted postmortem, persisted incident memory, and 384-dimensional vector.

---

## Result

Phase 14 is complete.

AegisOps now has a closed learning loop:

```text
detect
→ investigate
→ approve
→ remediate
→ verify
→ document
→ remember
→ reuse historical context
```

The system does not merely restore service. It converts verified incidents into grounded operational memory that can improve future investigations without treating historical similarity as causal proof.

**Next: Phase 15 — Operator Dashboard.**

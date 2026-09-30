# Phase 3 — Incident Detection Engine

## Objective

Phase 3 turns the telemetry created in Phase 2 into durable operational incidents.

Before this phase, AegisOps could observe that a dependency was down, HTTP errors were increasing, or latency was elevated. Phase 3 adds the deterministic layer that decides when a monitored condition should become an incident, stores that incident in AegisOps PostgreSQL, prevents duplicate active incidents, and automatically resolves incidents when the triggering signal returns to normal.

This phase intentionally does **not** perform root-cause analysis. It answers:

> **What is unhealthy right now?**

Later AI phases will answer:

> **Why is it unhealthy, what evidence supports that conclusion, and what should be done about it?**

---

## Phase 3 Architecture

```text
Controlled Benchmark
        │
        ▼
    Prometheus
        │
        │ PromQL
        ▼
Prometheus Client
        │
        ▼
Detection Rules
        │
        ▼
Detection Engine
        │
        ▼
Incident Manager
   ┌────┼─────┐
   │    │     │
CREATE UPDATE RESOLVE
   └────┼─────┘
        ▼
AegisOps PostgreSQL
```

The AegisOps backend now consumes Prometheus directly. Grafana remains a visualization layer; it is not used as a source of truth for incident detection.

---

## Prometheus Integration

A dedicated Prometheus client was added under:

```text
backend/app/monitoring/prometheus.py
```

The backend queries Prometheus through its HTTP API:

```text
GET /api/v1/query
```

The Prometheus address is configured through:

```env
PROMETHEUS_URL=http://127.0.0.1:9090
```

This keeps infrastructure configuration outside detection logic and allows the address to change later without modifying application code.

The current AegisOps backend runs directly on the host, while Prometheus runs in Docker and exposes port `9090` to the host.

---

## Detection Rules

Phase 3 uses deterministic rules rather than AI.

The current rule set covers four operational conditions:

| Rule | Service | Trigger | Severity |
|---|---|---|---|
| `postgresql_unavailable` | benchmark-postgresql | dependency gauge equals `0` | HIGH |
| `redis_unavailable` | benchmark-redis | dependency gauge equals `0` | HIGH |
| `http_5xx_rate_high` | benchmark-api | 5xx rate exceeds `0.05 req/s` | MEDIUM |
| `api_latency_high` | benchmark-api | P95 latency exceeds `2.0 s` | MEDIUM |

The rules live in:

```text
backend/app/incidents/rules.py
```

Each rule contains:

```text
key
title
service
severity
PromQL query
comparison operator
threshold
```

A rule decides whether a measured value is unhealthy. It does **not** attempt to explain the cause.

---

## Detection Engine

The detection engine lives in:

```text
backend/app/incidents/detector.py
```

For every configured rule it:

1. queries Prometheus,
2. extracts the metric value,
3. applies the rule comparison,
4. returns a normalized `DetectionResult`.

A detection result contains:

```text
rule_key
title
service
severity
triggered
value
threshold
```

If Prometheus cannot provide a metric, the value is treated as unknown instead of healthy. This prevents AegisOps from incorrectly resolving an incident simply because monitoring data is temporarily unavailable.

---

## Incident Persistence

Phase 3 introduces the first real AegisOps incident table.

Schema:

```text
backend/sql/001_create_incidents.sql
```

Each record stores:

```text
id
fingerprint
rule_key
title
service
severity
status
trigger_value
threshold
first_detected_at
last_seen_at
resolved_at
```

The current incident states are intentionally simple:

```text
OPEN
RESOLVED
```

More detailed investigation/remediation states will be introduced only when later phases need them.

---

## Deduplication

A recurring detection loop must not create a new incident every few seconds for the same outage.

A fingerprint is therefore generated from:

```text
service + rule_key
```

Example:

```text
benchmark-redis:redis_unavailable
```

While an incident is `OPEN`, the same fingerprint is updated rather than inserted again.

The database also enforces this rule with a partial unique index:

```sql
CREATE UNIQUE INDEX IF NOT EXISTS unique_open_incident_fingerprint
ON incidents (fingerprint)
WHERE status = 'OPEN';
```

This gives AegisOps two layers of duplicate protection:

```text
Application-level lookup
        +
Database-level uniqueness
```

Once an incident is resolved, a future recurrence is allowed to create a new incident record.

---

## Incident Manager

The incident manager lives in:

```text
backend/app/incidents/manager.py
```

It translates detection results into incident state changes.

```text
metric unavailable
    → SKIPPED

triggered + no open incident
    → CREATED

triggered + open incident
    → UPDATED

healthy + open incident
    → RESOLVED

healthy + no open incident
    → HEALTHY
```

This is the core state transition logic for Phase 3.

---

## Automatic Detection Worker

A background worker was added under:

```text
backend/app/incidents/worker.py
```

The polling interval is configurable:

```env
INCIDENT_DETECTION_INTERVAL_SECONDS=10
```

The worker runs one detection cycle every ten seconds.

Because the Prometheus and PostgreSQL operations are synchronous, the detection cycle is executed through `asyncio.to_thread()` so it does not block FastAPI's event loop.

If one cycle fails, the worker logs the error and continues on the next interval instead of dying permanently.

---

## Incident API

Phase 3 adds:

```text
POST /incidents/detect
GET  /incidents
```

`POST /incidents/detect` manually runs one detection cycle. It is useful for testing and debugging.

`GET /incidents` returns the stored incident history.

Automatic detection does not depend on the manual endpoint; the background worker continuously evaluates rules while the AegisOps backend is running.

---

## Telemetry Evidence During Incident Testing

The Phase 2 Grafana dashboard became the evidence layer used to validate Phase 3 behavior.

During the Phase 3 tests, the dashboard showed the benchmark PostgreSQL outage and recovery, the burst of HTTP 500 traffic, the artificial slow requests, and the corresponding latency increase.

![Grafana telemetry during Phase 3 incident testing](../screenshots/phase%203/grafana.png)

The important architectural point is that Grafana is only presenting what Prometheus collected. The incident engine independently queries the same Prometheus data and makes its own deterministic decision.

---

## Incident Lifecycle Evidence

The incident API confirmed that AegisOps converted those metrics into persistent incident records.

![AegisOps incident records created from Prometheus telemetry](../screenshots/phase%203/incidents.png)

The captured incident history demonstrates several different states at once:

- Redis outage detected as `HIGH` and later `RESOLVED`
- PostgreSQL outage detected as `HIGH` and later `RESOLVED`
- HTTP 5xx spike detected as `MEDIUM`
- high P95 latency detected as `MEDIUM`

The HTTP error rule was observed with a trigger value of approximately:

```text
0.408 req/s
```

against a threshold of:

```text
0.05 req/s
```

The latency rule was observed with a P95 value of approximately:

```text
2.79 s
```

against a threshold of:

```text
2.0 s
```

---

## End-to-End Verification

### Redis outage

Test flow:

```text
docker compose stop benchmark-redis
        ↓
benchmark_dependency_up{dependency="redis"} = 0
        ↓
Prometheus stores the signal
        ↓
AegisOps detection worker reads it
        ↓
redis_unavailable triggers
        ↓
OPEN incident created
```

Repeated detection cycles did not create duplicate incidents.

Instead:

```text
same incident ID
        ↓
last_seen_at updated
```

After Redis was restarted:

```text
dependency gauge returns to 1
        ↓
same incident
        ↓
RESOLVED
```

---

### PostgreSQL outage

Stopping only the benchmark PostgreSQL service created a separate `postgresql_unavailable` incident.

AegisOps remained operational because its own PostgreSQL database is independent from the benchmark database.

After the benchmark database returned, the incident automatically transitioned to `RESOLVED`.

---

### HTTP 5xx spike

A burst of controlled `/simulate/error` requests pushed the rolling 5xx rate above the configured threshold.

AegisOps created:

```text
http_5xx_rate_high
severity = MEDIUM
```

Because the rule uses a five-minute rate window, the incident remains active until the error traffic ages out of the window.

---

### P95 latency

Repeated requests to:

```text
/simulate/slow?seconds=3
```

raised the Prometheus P95 latency estimate above the `2.0 s` threshold.

AegisOps created:

```text
api_latency_high
severity = MEDIUM
```

As with the 5xx rule, the five-minute Prometheus window allows the incident to resolve naturally after the slow traffic is no longer inside the active window.

---

## Current Phase 3 Data Flow

```text
Benchmark failure / degradation
            ↓
Benchmark application metrics
            ↓
Prometheus
            ↓
PromQL queries
            ↓
AegisOps PrometheusClient
            ↓
Incident rules
            ↓
DetectionResult
            ↓
Incident manager
            ↓
CREATE / UPDATE / RESOLVE
            ↓
AegisOps PostgreSQL
            ↓
GET /incidents
```

---

## What Phase 3 Does Not Do

Phase 3 deliberately stops at deterministic incident detection.

It does not yet provide:

```text
AI diagnosis
root-cause analysis
RAG
tool calling
workflow orchestration
human approval
automatic remediation
recovery verification after remediation
postmortem generation
```

Those capabilities remain separate phases so each architectural responsibility is introduced for a clear reason.

---

## Key Lessons

- Monitoring data and incident records are different layers.
- Grafana visualizes telemetry; AegisOps should consume Prometheus directly.
- Deterministic thresholds are appropriate for deciding that a measurable condition is unhealthy.
- Detection should not be confused with diagnosis.
- Unknown telemetry must not be treated as healthy telemetry.
- Incident fingerprints prevent repeated polling from producing duplicate incident spam.
- Database constraints should reinforce application-level invariants.
- A benchmark dependency can fail while AegisOps remains available because the benchmark and AegisOps databases are isolated.
- Rolling Prometheus windows naturally delay recovery for rate- and latency-based incidents.
- A background detection worker must survive individual cycle failures.

---

## Result

Phase 3 converts passive telemetry into persistent, recovery-aware incident records.

AegisOps can now:

```text
observe telemetry
      ↓
detect unhealthy conditions
      ↓
assign deterministic severity
      ↓
create an incident
      ↓
deduplicate repeated detections
      ↓
track the incident while active
      ↓
resolve it automatically when telemetry recovers
```

**Status: Complete**

**Next: Phase 4 — Advanced Workflow Orchestration**

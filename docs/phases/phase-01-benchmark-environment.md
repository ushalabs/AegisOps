# Phase 1 — Benchmark Environment

## Objective

Phase 1 created a deliberately breakable target system for AegisOps to observe in later phases.

The benchmark system is logically separate from the main AegisOps backend, but all services are managed through the same root `docker-compose.yml`.

The benchmark environment contains:

- a FastAPI benchmark service
- a dedicated PostgreSQL database
- Redis
- controlled failure endpoints
- real dependency interactions

The purpose is not to build another full product. It is to give AegisOps a realistic environment where repeatable failures can be generated.

---

## Architecture

```text
Root Docker Compose
│
├── AegisOps PostgreSQL + pgvector
│
└── Benchmark Environment
    ├── benchmark-api
    ├── benchmark-db
    └── benchmark-redis
```

The benchmark database and Redis service are not exposed to Windows directly.

The benchmark API communicates with them using Docker's internal service-name DNS:

```text
benchmark-api
    ├── benchmark-db:5432
    └── benchmark-redis:6379
```

The benchmark API itself is exposed to the host on:

```text
localhost:8001
```

---

## Benchmark API

The benchmark application lives under:

```text
benchmark/
├── app/
│   ├── __init__.py
│   └── main.py
├── Dockerfile
└── requirements.txt
```

The API includes:

```text
GET  /health
GET  /ready
POST /items
GET  /items
GET  /activity
GET  /simulate/error
GET  /simulate/slow
```

---

## PostgreSQL Behavior

The benchmark API uses its own PostgreSQL database.

The `/items` endpoints provide a small but real persistence workload:

```text
POST /items
    ↓
store record in benchmark PostgreSQL

GET /items
    ↓
read records from benchmark PostgreSQL
```

This creates realistic database-dependent application behavior without adding unnecessary ORM complexity.

---

## Redis Behavior

Redis is used as a fast in-memory datastore.

The `/activity` endpoint increments a Redis counter:

```text
GET /activity
    ↓
benchmark:activity_requests += 1
```

This gives the benchmark system a second dependency with different failure characteristics from PostgreSQL.

---

## Controlled Failures

The benchmark supports four repeatable failure categories.

### PostgreSQL outage

```powershell
docker compose stop benchmark-db
```

Expected result:

```text
GET /ready
→ 503 PostgreSQL unavailable
```

---

### Redis outage

```powershell
docker compose stop benchmark-redis
```

Expected result:

```text
GET /ready
→ 503 Redis unavailable
```

---

### HTTP 500 simulation

```text
GET /simulate/error
```

Expected result:

```text
500 Internal Server Error
```

---

### Artificial latency

```text
GET /simulate/slow?seconds=3
```

Expected result:

```text
response delayed by approximately 3 seconds
```

---

## Final Verification

The complete Phase 1 verification confirmed:

- `/health` returns healthy
- `/ready` reports PostgreSQL and Redis connected
- items can be inserted into PostgreSQL
- items can be read back from PostgreSQL
- Redis counters increment correctly
- controlled HTTP 500 responses work
- artificial response latency works
- stopping benchmark PostgreSQL produces a readiness failure
- restoring PostgreSQL returns the service to readiness
- stopping Redis produces a Redis readiness failure
- restoring Redis returns the service to readiness

---

## Phase 1 Data Flow

```text
                  Benchmark API
                 /             \
                ▼               ▼
       Benchmark PostgreSQL    Redis
                │               │
         persistent data   fast temporary state
```

---

## Key Lessons

- The benchmark system must be logically separate from AegisOps itself.
- Separate services can still live in the same Compose project.
- Docker service names provide internal DNS between containers.
- Dependencies do not need host ports unless a host process must access them directly.
- A useful benchmark should create realistic, repeatable failures without hardcoding diagnoses.
- The benchmark exists to support later monitoring, incident detection, AI investigation, and remediation phases.

---

## Result

Phase 1 produced a controlled target environment with real dependencies and repeatable failures.

**Status: Complete**

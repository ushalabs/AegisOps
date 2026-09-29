# Phase 0 — Project Foundation

## Objective

Phase 0 established the minimum technical foundation required for AegisOps before any monitoring, automation, AI reasoning, or incident-handling logic was introduced.

The focus was deliberately limited to:

- Git and GitHub
- FastAPI
- PostgreSQL
- pgvector
- Docker
- Docker Compose
- environment-based configuration
- backend-to-database connectivity

The goal was to create a stable base that later phases could build on without overengineering temporary architecture.

---

## What Was Built

### Git and GitHub

A new Git repository was initialized for AegisOps and connected to GitHub.

Repository-level configuration included:

- `.gitignore`
- `.env.example`
- `README.md`
- clean incremental commits

Real secrets remain local inside `.env`, while `.env.example` documents the configuration variables required by the project.

---

### FastAPI Backend

A FastAPI backend was created under:

```text
backend/
├── app/
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   └── database.py
│   └── main.py
├── tests/
├── requirements.txt
└── requirements-dev.txt
```

The initial API exposes:

```text
GET /health
GET /ready
```

`/health` verifies that the API process itself is alive.

`/ready` verifies that the backend can reach its required PostgreSQL dependency.

This distinction is important because a process can be alive while the wider system is not operational.

---

### PostgreSQL + pgvector

PostgreSQL runs in Docker using the pgvector-enabled image:

```text
pgvector/pgvector:pg16
```

The `vector` extension was enabled and verified successfully.

This gives AegisOps a PostgreSQL database that can later support semantic retrieval for:

- historical incidents
- runbooks
- postmortems
- RAG-based evidence retrieval

No RAG logic was implemented in Phase 0; only the storage capability was established.

---

### Docker and Docker Compose

The root `docker-compose.yml` was introduced to manage infrastructure.

The AegisOps PostgreSQL service uses:

- a persistent Docker volume
- a health check
- environment-based credentials
- configurable host port mapping

The default PostgreSQL port remains `5432` in shared configuration. Local developers can override it in `.env` when another PostgreSQL instance already occupies that port.

---

### Backend → PostgreSQL Connectivity

The backend uses `psycopg` for direct PostgreSQL connectivity.

The configuration layer loads database settings from the root `.env` file.

The working path is:

```text
FastAPI / Python
      ↓
psycopg
      ↓
Docker host port
      ↓
PostgreSQL container
      ↓
pgvector-enabled database
```

A real port conflict with another local PostgreSQL installation was diagnosed during development. The issue was resolved by overriding the AegisOps host port locally while leaving the shared project default unchanged.

---

## Verification Performed

Phase 0 verification confirmed:

- Docker Desktop and Docker Compose work correctly
- containers can be pulled and executed
- PostgreSQL starts successfully
- the PostgreSQL health check reports healthy
- pgvector is enabled
- vector values are accepted by PostgreSQL
- the backend can connect to PostgreSQL
- `/health` remains available when the DB is down
- `/ready` correctly changes from `200` to `503` when the DB becomes unavailable
- readiness returns to `200` after the DB is restored

---

## Phase 0 Architecture

```text
AegisOps Backend
      │
      ├── /health
      └── /ready
             │
             ▼
          psycopg
             │
             ▼
      PostgreSQL 16
             +
          pgvector
             │
             ▼
      persistent volume
```

---

## Key Lessons

- GitHub should store configuration templates, not real secrets.
- Docker container state and Docker volume state are different concerns.
- A service being alive is not the same as the system being ready.
- Authentication failures can be caused by reaching the wrong service, not only by a wrong password.
- Shared configuration should use sane defaults, while machine-specific conflicts belong in local `.env` overrides.
- Temporary infrastructure should not be overengineered before the real application model exists.

---

## Result

Phase 0 established a clean and reproducible foundation for the rest of AegisOps.

**Status: Complete**

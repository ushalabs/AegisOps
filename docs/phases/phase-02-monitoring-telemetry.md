# Phase 2 — Monitoring & Telemetry

## Objective

Phase 2 gave AegisOps its observability layer.

The benchmark environment created in Phase 1 can now expose measurable evidence through:

- Prometheus application metrics
- dependency-health metrics
- cAdvisor container metrics
- Grafana dashboards

This phase does not perform incident detection or AI reasoning. It only collects and visualizes objective telemetry that later phases can use.

---

## Monitoring Architecture

```text
Benchmark API
    │
    ├── HTTP metrics
    ├── latency metrics
    └── dependency health
            │
            ▼
        Prometheus
            ▲
            │
        cAdvisor
            ▲
            │
      Docker containers
            │
            ▼
         Grafana
```

---

## Application Metrics

The benchmark FastAPI application now exports Prometheus metrics through:

```text
GET /metrics
```

The main custom metrics are:

```text
benchmark_http_requests_total
benchmark_http_request_duration_seconds
benchmark_dependency_up
```

### Request counter

Tracks:

- HTTP method
- request path
- response status

Example labels:

```text
path="/health"
status="200"

path="/simulate/error"
status="500"
```

### Request duration histogram

Measures endpoint response latency and supports percentile calculations such as P95 latency.

### Dependency gauge

Tracks dependency availability:

```text
benchmark_dependency_up{dependency="postgresql"} 1
benchmark_dependency_up{dependency="redis"} 1
```

Values:

```text
1 = available
0 = unavailable
```

---

## Background Dependency Monitoring

An important design issue was discovered during Phase 2.

The first implementation performed PostgreSQL and Redis health checks directly inside `/metrics`.

When Redis was stopped:

```text
Prometheus
    ↓
GET /metrics
    ↓
Redis health probe stalls
    ↓
Prometheus scrape timeout
    ↓
benchmark-api target becomes DOWN
```

This made observability unreliable exactly when a dependency failed.

The design was changed so dependency checks run in a background task instead.

```text
background monitor
    ├── check PostgreSQL
    └── check Redis
            ↓
        update gauges

Prometheus
    ↓
GET /metrics
    ↓
return current metrics immediately
```

After this change:

```text
Redis DOWN
    ↓
benchmark_dependency_up{dependency="redis"} = 0
    ↓
Prometheus target remains UP
```

This was a significant observability improvement because monitoring remains available during dependency outages.

---

## Prometheus

Prometheus runs as a Docker Compose service.

It scrapes:

```text
benchmark-api:8000/metrics
cadvisor:8080/metrics
```

The scrape interval is:

```text
5 seconds
```

Prometheus successfully records:

- request counters
- HTTP status codes
- latency histograms
- PostgreSQL availability
- Redis availability
- container CPU metrics
- container memory metrics
- container network metrics
- container filesystem metrics

---

## cAdvisor

cAdvisor was added to expose container-level telemetry.

This provides infrastructure metrics for the Docker environment, including:

- CPU usage
- memory usage
- network activity
- filesystem usage

This creates a second evidence layer alongside the application-level metrics produced by FastAPI.

---

## Grafana

Grafana is connected automatically to Prometheus through provisioning.

The final dashboard is:

```text
AegisOps Benchmark Monitoring
```

It contains four panels:

1. **Dependency Health**
2. **HTTP 5xx Rate**
3. **HTTP Request Rate**
4. **P95 Request Latency**

### Dashboard

![AegisOps Benchmark Monitoring Dashboard](../screenshots/phase%202/grafana.png)

### Running monitoring stack

![AegisOps Phase 2 Docker Stack](../screenshots/phase%202/stack-running.png)

---

## Dashboard Queries

### Dependency Health

```promql
benchmark_dependency_up
```

### HTTP Request Rate

```promql
sum by (path, status) (
  rate(benchmark_http_requests_total[5m])
)
```

### HTTP 5xx Rate

```promql
sum(
  rate(benchmark_http_requests_total{status=~"5.."}[5m])
)
```

### P95 Request Latency

```promql
histogram_quantile(
  0.95,
  sum by (le, path) (
    rate(benchmark_http_request_duration_seconds_bucket[5m])
  )
)
```

---

## Final Verification

Phase 2 verification confirmed:

- benchmark application metrics are exposed
- Prometheus scrapes the benchmark API successfully
- Prometheus scrapes cAdvisor successfully
- Grafana queries Prometheus successfully
- dependency state is visible as `1` or `0`
- stopping Redis changes its dependency gauge to `0`
- restoring Redis changes the gauge back to `1`
- the Prometheus benchmark target remains available during dependency outages
- HTTP 500 traffic appears in the 5xx metric
- artificial latency appears in the P95 latency graph
- generated benchmark traffic appears in request-rate telemetry
- container telemetry is available through cAdvisor

---

## Phase 2 Architecture

```text
                   Benchmark API
                        │
         ┌──────────────┼──────────────┐
         │              │              │
    request count    latency      dependency state
         │              │              │
         └──────────────┴──────────────┘
                        │
                        ▼
                    Prometheus
                        ▲
                        │
                     cAdvisor
                        ▲
                        │
                 Docker containers
                        │
                        ▼
                     Grafana
```

---

## Key Lessons

- Monitoring should remain available when dependencies fail.
- `/metrics` should be fast and should not depend directly on unhealthy downstream services.
- Application telemetry and container telemetry provide different evidence and are both valuable.
- Prometheus collects and stores time-series data; Grafana visualizes it.
- Histograms provide distributions rather than exact request durations, so percentile values are estimated from bucket boundaries.
- Objective telemetry should be collected before incident reasoning is introduced.

---

## Result

Phase 2 produced a working observability stack capable of monitoring benchmark behavior, dependency state, HTTP errors, response latency, and container resource usage.

**Status: Complete**


# API Latency Troubleshooting

## Symptoms

The benchmark API experiences elevated response times.
The P95 request latency exceeds the configured threshold.

## Investigation

1. Inspect the P95 latency panel in Grafana.
2. Identify which endpoints have elevated response times.
3. Compare latency changes with HTTP request rates.
4. Check PostgreSQL and Redis dependency health.
5. Inspect benchmark API logs and container resource usage.

## Potential Causes

- Slow application operations.
- Delayed responses from dependencies.
- Increased request traffic.
- CPU or memory pressure.
- Database queries or external operations taking too long.

## Recovery

Identify the affected endpoint and collect evidence before
selecting an appropriate recovery action.

A service restart may temporarily restore performance in
some cases, but it does not necessarily resolve the underlying cause.

Verify recovery using fresh latency measurements rather than
assuming that a successful command means the incident is resolved.
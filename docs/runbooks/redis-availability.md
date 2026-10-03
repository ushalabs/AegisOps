
# Redis Availability Troubleshooting

## Symptoms

The benchmark API reports Redis as unavailable.
The `benchmark_dependency_up` metric for Redis is 0.

## Investigation

1. Check the Redis container with `docker compose ps`.
2. Inspect recent logs with `docker compose logs --tail=100 benchmark-redis`.
3. Check Redis connectivity and readiness.
4. Inspect benchmark API logs for connection errors.
5. Compare Redis availability with PostgreSQL availability.

## Potential Causes

- Redis container stopped or crashed.
- Redis failed during startup.
- Network or connection configuration problems.
- Resource exhaustion.

## Recovery

If the container is stopped, an operator can restart it with
`docker compose start benchmark-redis`.

Verify that Redis becomes healthy and that the benchmark API
reports the dependency as available again.

Do not assume the original incident is resolved merely because
the restart command succeeded.
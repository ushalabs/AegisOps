
# PostgreSQL Availability Troubleshooting

## Symptoms

The benchmark API reports PostgreSQL as unavailable.
The PostgreSQL dependency health metric has a value of 0.

## Investigation

1. Check the benchmark database with `docker compose ps`.
2. Inspect its logs with `docker compose logs --tail=100 benchmark-db`.
3. Check database readiness using `pg_isready`.
4. Inspect benchmark API logs for database connection errors.
5. Verify database credentials, connection limits and network connectivity.

## Potential Causes

- PostgreSQL container stopped or crashed.
- Database startup or recovery failure.
- Incorrect connection configuration.
- Connection exhaustion or resource limitations.

## Recovery

If the benchmark database is stopped, an operator can run
`docker compose start benchmark-db`.

Wait until PostgreSQL accepts connections, then verify that the
benchmark API reports PostgreSQL as available.

Do not restart the separate AegisOps PostgreSQL database
when troubleshooting the benchmark database.
# Operations / Production Checklist

## Reliability
- Redis is optional: `/health` remains usable when Redis is unavailable and `/ready` reports `degraded`.
- Empty cache is a normal cache miss; API rebuilds it from Gold.
- Duplicate ingestion is handled by `incremental_upsert.py` using `ON CONFLICT(id) DO UPDATE`.
- Failed batches are transactional per batch; rerun is safe for the same IDs.
- API has DB connection pooling (2–20 connections), 30s client benchmark timeout, and container health checks.

## Backup / restore
```bash
docker-compose exec -T api sh scripts/backup.sh /app/backup
docker-compose exec -T api sh scripts/restore.sh /app/backup/<file>.dump
```
Backup retention in the POC is 7 days; production should move dumps to durable object storage and test restores on a schedule.

## Security
- Secrets are supplied through `.env` / deployment secret store; `.env` is git-ignored.
- `API_KEY` is reserved for production gateway authentication; keep the POC behind a trusted network.
- Restrict CORS, database ports, Redis ports and Swagger in production.

## Observability
- `/health`, `/ready`, `/metrics` provide basic health/resource telemetry.
- Container logs are the application logs; collect them with the production platform.
- Recommended alerts: DB unavailable, Redis degraded, high P95/P99, disk growth, connection-pool exhaustion, failed refresh.

## Data lifecycle
- `is_active=false` is the soft-delete state.
- `updated_at` is the synchronization watermark.
- Retention/archival policy must be finalized with the source-data owner before production.

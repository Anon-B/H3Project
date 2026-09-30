# Operations

## Runtime
Services: db, redis, api, frontend.
Ports: PostgreSQL 5432, Redis 6379, API 8000, frontend 8080.
Local runtime uses Colima with a typical allocation of 10 CPU / 20 GiB RAM / 80 GiB disk.

## Health
```bash
docker-compose ps
curl http://localhost:8000/health
curl http://localhost:8000/ready
docker-compose logs --tail=100 api
```

## Backup
```bash
docker-compose exec -T api sh scripts/backup.sh /app/backup
```
Backup script uses pg_dump custom format and deletes local dumps older than 7 days.

## Restore
```bash
docker-compose exec -T api sh scripts/restore.sh /app/backup/<file>.dump
```
Use only on an intentionally replaceable database; restore uses --clean --if-exists.

## Redis
Redis is an optimization. If unavailable, /health still works and /ready reports degraded.
Summary cache TTL is 300 seconds.
Dataset deletion/ingestion currently flushes cache when Redis is reachable.

## Security
Set secrets through .env/deployment secret store; never commit .env.
API_KEY enables X-API-Key protection for non-health endpoints.
POC CORS is allow-all; restrict origins/ports/Swagger at deployment time.

## Observability
Use /health, /ready, /metrics plus container logs.
Recommended production alerts: DB unavailable, Redis degraded, disk growth, high latency, pool exhaustion, failed ingestion.

## Data lifecycle
Canonical entity deletion currently cascades from dataset delete.
Ingestion history is retained through ingestion_runs and related tables until dataset/run lifecycle policy is finalized.


# H3Project v1.3 Hardening Review

## Purpose

v1.3 is a hardening cycle. The goal is to improve correctness, security,
maintainability and operational safety without changing the canonical
Dataset → Entity → Spatial Part → Boundary H3 architecture.

## Decisions

| Item | Decision | Implementation |
|---|---|---|
| 1 | Do | Active dataset filtering + partial unique name index |
| 2 | Do | schema_migrations + startup migration runner |
| 4 | Do | API-key roles, JWT roles, endpoint RBAC, frontend token headers |
| 5 | Do | CORS, logging, route-safe metrics, forwarded headers, Redis offload |
| 6 | Do | RFC 5987 export filename + generator streaming |
| 8 | Do | Analysis uses h3_index; ingestion preview invalidation |
| 9 | Do | ASGI behavioral security/integrity tests; CI remains manual |
| 14 | Do | App component extraction, lint/format tooling, pinned dependencies, Docker hardening |
| 15 | Do | focus-visible + prefers-reduced-motion |
| 16 | Keep current | Background ingestion jobs already exist; partitioning waits for benchmark evidence |
| 17 | Do selectively | healthz/readyz aliases and multiprocess metrics; APM/tracing deferred |
## Intentionally deferred

The following changes are not applied merely for theoretical scalability:

- H3 table partitioning: wait for measured workload at million+ row scale.
- RabbitMQ/Celery/BullMQ: the current persistent ingestion_jobs + worker pool is sufficient for the POC.
- OpenTelemetry/Sentry/Datadog: add after API → DB → Redis → worker flows are stable and a real tracing requirement exists.
- Removing ingestion_h3_cells: retain it for ingestion history, audit and rollback support.
- Converting h3_index from TEXT to BIGINT: avoid cross-layer schema churn without a measured storage/query benefit.
- Removing GIN/bbox indexes: keep until query benchmarks prove they are unused.
- Replacing full coverage logic: current polygon coverage/reconstruction already supports display fill.
## Release documentation rule

Every release update must explain:

1. What changed.
2. Why it changed.
3. Database/schema impact.
4. API/frontend compatibility impact.
5. Migration or startup steps.
6. Test/build verification.
7. Operational or rollback considerations.
8. Items intentionally deferred to a later release.

The release note must be updated together with the implementation so a future
developer can understand the reason for a change without reconstructing it
from commit history alone.
## Verification target

Before v1.3 is released:

- Backend pytest suite passes.
- Ruff check is clean or has documented exceptions.
- Frontend TypeScript/Vite build passes.
- Frontend ESLint check passes.
- Frontend Prettier check passes.
- Docker Compose stack starts and healthchecks pass.
- Migration runner is idempotent.
- Auth/RBAC, soft-delete, rate-limit and Thai export tests pass.

# v1.2 Review Closure

## Completed

- JWT/API-key authentication and RBAC with OIDC JWKS validation.
- OIDC algorithm allow-list, required token expiry, issuer/audience validation when configured, and configurable clock-skew leeway.
- Redis rate limiting, request IDs, structured request logging, and Prometheus metrics.
- Dataset soft delete and ingestion lifecycle timestamps/indexes.
- Ingestion H3 deduplication.
- PostgreSQL COPY batching for bulk `entity_part_h3` and `ingestion_h3_cells` writes.
- Background ingestion with DB-backed persistent job state.
- Queued/running jobs are recovered after API restart using a PostgreSQL advisory lock.
- Job status API reads persistent state from `ingestion_jobs`.
- Rollback and GeoJSON export remain supported.
- Viewport loading through `/ingestion/dataset/viewport`.
- H3 reconstruction in a Web Worker.
- Frontend Map/Deck.gl/MapLibre/Draw code is lazy-loaded; the initial JS bundle is about 259 KB while GIS engine chunks load on demand.
- Frontend dependency audit: 0 vulnerabilities.
- Known Zod Rollup annotation warning is filtered because it originates in third-party dependency code and does not indicate an application failure.
- 100,000-row current-schema Boundary-H3 micro-benchmark: P50 0.347 ms, P95 0.727 ms, P99 1.683 ms on the development Mac Mini.

## Architecture decision

Canonical storage remains Boundary H3. Full display-resolution H3 coverage is not persisted as canonical storage. Display cells are reconstructed on demand, with viewport loading and a Web Worker reducing frontend work.

## Environment-only warning

`docker-compose` on this Mac reports that the Docker Buildx CLI plugin is unavailable and falls back to the classic builder. This is a local Docker installation warning, not an application build failure. The images still build successfully.

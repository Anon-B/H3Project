# Review Fixes — feature/next

## Implemented

- Fixed advanced /query polygon filtering to use PostGIS ST_Intersects.
- Added /query support for nearby; unknown spatial types now return HTTP 400.
- Query results now return stored geometry so map layers can render them.
- Added original per-part geometry storage in entity_parts.geom with GiST index.
- Replaced max(entity_id)+1 with PostgreSQL identity generation.
- Added ingestion_run_id to entities for ingestion traceability.
- Added coordinate validation with [lng, lat] plus altitude/Z support.
- Added polygon validity validation.
- Added H3 workload preflight guard before expensive polygon conversion.
- Replaced Redis flushdb() with prefix-based cache invalidation.
- Prevented appending data when the same dataset name uses a different resolution/type.
- Added schema bootstrap for fresh PostgreSQL volumes.
- Removed destructive DROP statements from the canonical schema bootstrap.
- Bound PostgreSQL and Redis ports to localhost.
- Made API database credentials derive from POSTGRES_* variables.
- Added configurable CORS origins and constant-time API-key comparison.
- Added frontend /api proxy and VITE_API_URL support.
- Fixed Preview success state on failed/invalid previews.
- Execute is disabled until a valid Preview exists.
- Improved toast duration and accessibility announcement.
- Fixed dark workspace from overriding the selected basemap.
- Fixed entity marker inspector source label.
- Added backend/frontend regression tests.
- Reworked CI to start a real Compose stack, apply migrations, seed test data, run API tests, and build the frontend.

## Verified

- API health: OK
- Frontend /api/health: HTTP 200
- Backend tests: 8 passed
- Frontend production build: passed
- git diff --check: passed

## Remaining review items

- JWT/OIDC + RBAC is not implemented yet.
- Background ingestion / COPY batching is not implemented yet.
- Full H3 coverage vs boundary-only storage decision remains.
- Web Worker / viewport tiling remains.
- Full App.tsx component split remains.
- Pydantic request/response models remain.
- Prometheus-compatible metrics, structured logging, request IDs and rate limiting remain.
- ingestion_h3_cells deduplication/retention remains.
- Soft-delete, export and ingestion rollback UI remain.

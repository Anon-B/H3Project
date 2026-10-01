# v1.2 Review Closure

## Security
- JWT HS256 and OIDC JWKS bearer-token validation are supported.
- Optional or required authentication is controlled by AUTH_MODE.
- RBAC accepts roles, groups, and Keycloak-style realm_access.roles.
- Mutating endpoints require admin/editor/writer when AUTH_MODE=required.
- Redis-backed per-subject rate limiting is enabled.
- X-Request-ID and structured request logging are enabled.
- Prometheus metrics are exposed at /metrics/prometheus.
- CORS and API-key settings are environment-driven.

## Data lifecycle
- Dataset deletion is soft-delete.
- Ingestion runs have finished_at and status lifecycle.
- Ingestion can be rolled back by run ID.
- GeoJSON datasets can be exported as GeoJSON.
- Ingestion H3 rows are deduplicated with a unique index.
- Entity records retain ingestion_run_id for traceability.

## Ingestion
- Background ingestion is available with ?background=true.
- Background jobs expose /ingestion/jobs/{job_id}.
- Preview validates coordinates, polygon validity and H3 workload.
- Existing dataset resolution/type mismatches return 409.

## Performance
- H3 display reconstruction can run in a Web Worker.
- Redis cache invalidation is prefix-scoped.
- PostGIS geometry is indexed with GiST.
- PostgreSQL resources are configurable.

## Architecture decisions
- Canonical storage remains Boundary H3 to control storage growth.
- Display H3 is reconstructed from boundary coverage.
- Full H3 coverage is intentionally not persisted as the canonical dataset layer.
- Viewport-scale loading is implemented through /ingestion/dataset/viewport and Map onMoveEnd.
- UI shared primitives are extracted into frontend/src/components/ui.tsx.

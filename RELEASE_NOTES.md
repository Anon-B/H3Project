# H3Project v1.3.0 — Development Update

## Release update standard

Each release documents the change, reason, schema/API impact, migration steps,
verification, rollback considerations, and intentionally deferred work.
This keeps the release history understandable without relying on commit history.

## Current hardening scope

This development cycle applies the selected recommendations **1, 2, 4, 5, 6,
8, 9, 14, 15, 16 and 17** where they fit the current POC architecture.

### Database

- Active dataset queries exclude soft-deleted datasets.
- Active dataset names use a partial unique index.
- schema_migrations tracks applied migrations.
- scripts/migrate.sh is idempotent and is called by start-project.sh.
- ingestion_run_id remains part of the canonical ingestion lineage.
- Existing ingestion_h3_cells is retained for audit/history/rollback.

### Security and API

- API keys support explicit roles through API_KEYS_JSON.
- Invalid API keys are rejected in every authentication mode.
- JWT/OIDC roles continue to be recognized.
- Write endpoints use FastAPI role dependencies instead of method-only authorization.
- Frontend API calls support VITE_API_KEY and VITE_API_TOKEN.
- CORS is registered as real middleware.
- Request metrics use route templates where available.
- Redis rate-limit operations are moved off the async request path.
- Export filenames support RFC 5987 UTF-8 encoding.

### Operations and scale

- /healthz and /readyz are available alongside the existing endpoints.
- Prometheus multiprocess collection is configured for the multi-worker API.
- API and frontend Docker images have runtime healthchecks.
- Backend runs as a non-root user.
- Persistent background ingestion remains the current async batch mechanism.
- Table partitioning, message queues and APM/tracing remain benchmark-driven follow-up work.

### Frontend quality

- Dataset page logic is extracted from App.tsx.
- API access is centralized in frontend/src/lib/api.ts.
- Frontend dependencies are pinned.
- ESLint and Prettier checks are available.
- Ingestion preview is cleared when dataset name, resolution or attributes change.
- Analysis displays r.h3_index.
- focus-visible and prefers-reduced-motion accessibility support are added.

### Verification

The release gate is:

- backend pytest
- Ruff
- frontend TypeScript/Vite build
- ESLint
- Prettier check
- Docker healthchecks
- migration idempotency
- auth/RBAC, soft-delete, rate-limit and Thai export behavior

See docs/REVIEW_HARDENING_V1.3.md for the decision matrix and deferred items.

### Git branch cleanup

The repository branch set is simplified to the branches that are actually used:

```text
main
develop
feature/next
release/vX.Y.Z  # temporary, only when preparing a release
```

Permanent domain branches and experiment branches were removed from local and remote tracking. Future temporary branches must be scoped to a specific task and deleted after merge.

---

# H3Project v1.2.0

## Release scope

This release consolidates the MapLibre 6 runtime, System Health monitoring, and live System Settings workspace.

### Frontend
- MapLibre GL 6.11.2 runtime with stable public worker assets.
- Globe / Flat projection toggle with persisted workspace preference.
- Native map controls with configurable visibility.
- System Health page with backend, runtime and mapping checks plus auto-refresh.
- System Settings connected to live application behavior and local preferences.
- Theme, accent color, compact mode and animation settings.
- Map defaults: basemap, projection, H3 resolution and map controls.
- H3 visualization defaults: grid, 3D extrusion and height.
- Ingestion defaults: H3 resolution and auto-validation.
- Dataset delete confirmation preference.
- Reset all local workspace settings.

### Ingestion
- GeoJSON source resolution is persisted from System Settings.
- Auto-validation preference controls the Preview → Execute workflow.

### Verification
- Frontend production build passes.
- Backend test suite: 22 passed.
- Docker frontend runtime includes MapLibre worker and shared module assets.

---

# H3Project v1.1.0

## Release scope

This release consolidates the current H3 data platform implementation and developer tooling.

### Platform
- Canonical Dataset → Entity → Spatial Part → Boundary H3 model.
- GeoJSON ingestion with Preview → Execute workflow.
- Point / Line / Polygon / Multi-geometry ingestion support.
- Boundary H3 generation and display-resolution reconstruction.
- H3 analytics and dataset catalog.
- MapLibre + deck.gl map rendering.
- Style & 3D controls for H3 visualization.
- Async map loading protection against stale dataset requests.

### Frontend
- React + TypeScript + Vite.
- Material UI workspace design system.
- Dataset catalog and dataset detail management.
- Ingestion workflow UI.
- Analysis page.
- Map Inspector and JSON-only result view.
- Nginx cache policy for reliable frontend updates.

### Operations
- Docker Compose runtime for PostgreSQL/PostGIS, Redis, API and frontend.
- `start-project.sh` starts and health-checks the full stack.
- `stop-project.sh` stops the full stack while preserving Docker volumes.

### Documentation
- Architecture, developer guide and frontend map guide.
- API reference and database/data dictionary.
- Database space / table relationship documentation.
- GeoJSON ingestion, operations, migrations and troubleshooting guides.
- Implementation status and project overview.

## Verification

Release verification includes:

- Frontend production build passes.
- API tests pass.
- Docker Compose stack starts successfully.
- PostgreSQL and Redis health checks pass.
- API `/health` returns `status=ok`.
- Frontend is available on port `8080`.
- API is available on port `8000`.

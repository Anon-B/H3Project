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

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

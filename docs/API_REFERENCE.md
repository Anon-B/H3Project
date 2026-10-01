# API Reference

Base URL: `http://localhost:8000`
FastAPI Swagger: `/docs`. Responses use ORJSON; GZip is enabled for responses >= 1000 bytes.

## Public health
### GET /health
Returns database status, entity count and Redis availability.
### GET /ready
Returns ready/degraded. Redis degradation does not make the API itself unavailable.
### GET /metrics
Returns database, user-table, user-index byte sizes and Redis status.

## Dataset catalog
### GET /ingestion/datasets
Query: `limit=1..500`. Returns dataset registry + entity/part/Boundary-H3 counts.
### GET /datasets/{dataset_id}
Returns one dataset with metadata/catalog and counts.

### GET /datasets/{dataset_id}/export
Returns GeoJSON. The Content-Disposition header includes an RFC 5987 UTF-8 filename for non-ASCII dataset names.
### PATCH /datasets/{dataset_id}
Accepts name, metadata, source, owner, version, source_format, geographic_coverage, tags, license, update_frequency, schema, lineage and h3_resolution.
Frontend intentionally locks resolution during normal edit.
### DELETE /datasets/{dataset_id}
Deletes dataset and cascaded canonical data; current implementation flushes Redis if available.

## GeoJSON ingestion
### POST /ingestion/geojson/preview
Body: GeoJSON FeatureCollection, Feature, or supported Geometry.
Query: `resolution=5..15`. No DB write.
Returns feature count, boundary cell counts, display cell counts and per-feature preview.
Preview limit: 10,000 features; generated preview is capped to protect memory/output.

### POST /ingestion/geojson/execute
Body: same GeoJSON. Query: `resolution=5..15`, optional `dataset=<name>`.
Writes dataset/entities/parts/attributes/Boundary-H3 and ingestion audit rows in one transaction.
If dataset name exists, the current implementation reuses it.

## Entity inspection
### GET /entities/{entity_id}
Returns entity parts and canonical Boundary H3 grouped by part/ring.
### GET /entities/{entity_id}/coverage
Query: optional resolution. Returns reconstructed H3 GeoJSON for display/inspection.

## Dataset display
### POST /ingestion/dataset/preview
Body: {dataset, resolution, limit}. Returns reconstructed H3 FeatureCollection.
This is a server-side preview endpoint; normal Map loading uses the H3-ID endpoint below.

### GET /ingestion/dataset/h3
Required: `dataset`; optional `resolution=5..15`.
Returns source_resolution, boundary_h3, boundary_parts and entity_h3.
It does NOT return polygon geometry for every display cell.
Frontend reconstructs display cells from boundary_parts.

## Analytics
### GET /analytics/h3
Query: optional dataset; resolution 5..15; limit 1..200000.
Returns grouped h3_index, entity_count and feature_count from entity_part_h3.
Coverage values are currently null in this API response.

### POST /query
Advanced attribute/spatial query. Body supports dataset, conditions, spatial and limit.
Condition fields currently include entity_id, properties.<key>, attribute, h3_index and resolution.
Spatial types currently include bbox and polygon.

## Legacy/general spatial APIs
### GET /summary
Query: res=5..15, optional dataset.
Returns H3 polygons as GeoJSON and may use Redis cache with 300s TTL.

### GET /nearby
Required lat/lng. radius_m 0..50000, limit 1..5000, optional dataset.
Current code executes exact PostGIS distance against entity_point. Do not document this as an H3 broad-phase path unless the implementation is changed.

### GET /bbox
Required min_lat,min_lng,max_lat,max_lng; limit 1..20000; optional dataset.
Current code filters entity_point coordinates directly.

## Ingestion history
### POST /ingestion/dataset/execute
Compatibility endpoint. Current implementation is effectively a no-op and returns status/reason; use GeoJSON execute for canonical ingestion.
### GET /ingestion/runs
Returns recent ingestion runs; limit 1..100.
### GET /ingestion/runs/{run_id}
Returns run metadata and H3 storage statistics.

## Authentication
Authentication supports API keys and JWT/OIDC bearer tokens.

- API keys can be mapped to roles with API_KEYS_JSON, for example {"viewer-key":"viewer","editor-key":"editor"}.
- API_KEY remains supported as a backward-compatible single admin key.
- Invalid API keys always return 401.
- AUTH_MODE=required requires credentials on non-public endpoints.
- Write endpoints use role dependencies: editor/writer/admin for dataset updates and ingestion; admin/editor for rollback.
- Frontend can send VITE_API_KEY through X-API-Key or VITE_API_TOKEN through Authorization: Bearer.
- Public health endpoints include /health, /healthz, /ready, /readyz, /metrics and /metrics/prometheus.
- CORS is controlled by CORS_ORIGINS.

## Background ingestion
POST /ingestion/geojson/execute supports `background=true`.
It returns HTTP 202 with a job_id. Poll GET /ingestion/jobs/{job_id} for queued/running/completed/failed status.


# Architecture

## 1. Components
1. Browser: React + TypeScript + MUI.
2. Map: MapLibre GL + react-map-gl + maplibre-gl-draw.
3. GPU rendering: deck.gl H3HexagonLayer / GeoJsonLayer / ScatterplotLayer.
4. API: FastAPI + ORJSON + GZip + optional API key.
5. DB: PostgreSQL 17 + PostGIS 3.6.4.
6. Cache: Redis 8.
7. Runtime: Docker Compose + Colima on local Apple Silicon.

## 2. Ingestion flow
```text
File GeoJSON / Draw
       -> normalize GeoJSON
       -> validate / Preview
       -> H3 conversion
       -> dataset
       -> entity
       -> entity_parts
       -> entity_attributes
       -> entity_part_h3
       -> ingestion_runs / ingestion_parts / ingestion_h3_cells
```

## 3. Display flow
```text
Dataset selected
 -> GET /ingestion/dataset/h3
 -> receive Boundary H3
 -> frontend groups by entity/part/ring
 -> reconstruct display cells at selected resolution
 -> H3HexagonLayer renders GPU
```

## 4. Canonical rule
`entity_part_h3` is the canonical spatial H3 store.
`h3_features` is removed and must not be recreated.
`entity_h3` is only a compatibility view over entity_part_h3.

## 5. Boundary representation
For polygons, only boundary cells are persisted.
Outer rings identify filled areas; hole rings are subtracted during display reconstruction.
This is compact but not lossless representation of the original polygon.

## 6. Query principle
H3 can narrow spatial candidates or represent coverage, but exact spatial predicates must be done with appropriate geometry logic when exact geometry is available.
Current GeoJSON canonical model intentionally does not persist original polygon geometry, so polygon exact reconstruction is not equivalent to the original source geometry.

## 7. Redis
Redis caches summary responses. Cache loss must not break correctness.
Current summary cache TTL is 300 seconds.
Dataset deletion flushes Redis in the current API implementation.

## 8. API middleware
- ORJSON responses
- GZip for responses >= 1000 bytes
- CORS currently allows all origins in POC
- API key is optional via API_KEY; /health and /ready remain public

## 9. Frontend state
Map state includes active dataset, display resolution, display cells, entities, analytics, layer visibility, basemap and Style & 3D preferences.
Async map loading uses a request sequence guard to prevent stale dataset requests from overwriting newer state.

## 10. Rendering caveat
MapLibreOverlay is interleaved. Visual layer state is tied to React layer inputs and overlay props.
If Style & 3D stops updating, inspect DeckGLOverlay lifecycle before changing data generation.


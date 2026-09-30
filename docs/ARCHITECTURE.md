# Architecture

## Layers
1. Raw: synthetic/source-like input
2. Silver: one row per spatial entity + H3 Res 11/8/5
3. Gold: counts/metrics aggregated by H3
4. Redis: hot cache for coarse summaries
5. API: broad-phase → narrow-phase → GeoJSON
6. Frontend: map rendering by zoom

## Spatial query
Radius/BBox first derives candidate H3 cells. Database then performs exact PostGIS filtering.
H3 is a candidate index, not an exact distance predicate.

## Storage
H3 is stored as text in this POC for portability. A separate benchmark can test bigint/native representation before production lock-in.

## Rendering
Res 5/8 summary polygons are visualization layers. Object-level Res 11 is used for precise queries.
Geometry simplification is optional and must not alter analytical boundaries.

## Performance
Measure P50/P95/P99, throughput, payload size, DB CPU, Redis hit rate and storage.
SLA targets are hypotheses until the benchmark establishes realistic limits.

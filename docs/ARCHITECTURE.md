# Architecture

## Layers
1. Raw: source input such as GeoJSON (and future raster sources)
2. Canonical spatial store: entities + parts + Boundary H3
3. H3 Analytics: derived `h3_features` with H3 rows, entity counts and polygon coverage metrics
4. Gold: counts/metrics aggregated by H3 for summaries and map analytics
5. Redis: hot cache for coarse summaries
6. API: spatial query + analytics + dataset catalog
7. Frontend: MapLibre camera/map controls + deck.gl GPU H3 rendering

`h3_features` is derived data; it does not replace Boundary H3. Original source geometry is still not persisted.

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

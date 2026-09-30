# Ingestion Pipeline — GeoJSON / Draw

## Goal
Convert source geometry into canonical Entity + Boundary H3 storage without persisting full polygon geometry.

## Input paths
1. File / GeoJSON
2. Draw on Map
Both paths produce a GeoJSON FeatureCollection before Preview.

## Draw
MapLibre Draw supports Point, Line, Polygon, Select/Move, Edit Vertices, Use Drawing and Clear.
draw.create/update/delete events synchronize the FeatureCollection used by Preview/Execute.

## Pipeline
```text
Source
 -> normalize GeoJSON
 -> Preview
 -> choose source H3 resolution
 -> Execute
 -> datasets
 -> entities + entity_attributes
 -> entity_parts
 -> entity_part_h3
 -> ingestion audit
```

## Preview
`POST /ingestion/geojson/preview?resolution=11`.
No canonical DB write.
Preview reports feature count, boundary H3 count, display H3 count and per-feature errors.
Limit: 10,000 input features.

## Execute
`POST /ingestion/geojson/execute?resolution=11&dataset=<name>`.
The current transaction writes dataset, entity, attributes, parts, point coordinates and H3 rows plus ingestion audit.
Redis is flushed after successful ingestion when available.

## Geometry behavior
Point -> exact coordinate + one H3.
MultiPoint -> one point part per coordinate.
LineString/MultiLineString -> H3 coverage along segments.
Polygon -> Boundary H3 for outer ring + Boundary H3 for holes.
MultiPolygon -> one polygon part per polygon.
GeometryCollection -> flattened into parts.

## Boundary H3
Polygon conversion first finds overlapping H3 cells and keeps edge/boundary cells.
Interior cells are not stored canonically.

## Display
Frontend reconstructs approximate filled cells from boundary H3.
Target display resolution may be 5..15 and is independent from source resolution.

## Attributes
Source Feature.properties are written to entity_attributes.properties.
Inspector/API consumers should treat these as Entity attributes.

## Safety
Always Preview before Execute for large polygons.
High resolution + large polygon can generate very large H3 output.
Boundary representation is not lossless geometry.

## Acceptance
After Execute verify Dataset Registry, entity/Boundary-H3 counts, Map display, click Inspector and JSON attributes.


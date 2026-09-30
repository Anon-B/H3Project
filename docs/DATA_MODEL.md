# Data Model

## Design goal

The database is a lightweight entity registry with Boundary H3 as the canonical polygon representation.

- Original Polygon/MultiPolygon geometry is not stored.
- Polygon storage keeps only boundary H3 cells.
- Polygon holes are stored as separate H3 rings.
- MultiPolygon parts stay grouped under one entity when they come from one GeoJSON Feature.
- Polygon attributes are stored per part as JSONB.
- Line uses H3 coverage along the line.
- Point keeps exact latitude/longitude plus H3.
- Dataset controls one canonical H3 resolution.

## Tables

### datasets

Dataset definition and H3 configuration.

Fields: dataset_id, name, data_type, h3_resolution, metadata, timestamps.

### entities

Minimal entity registry.

Fields: entity_id, dataset_id.

### entity_parts

One spatial part of an entity. MultiPolygon uses multiple polygon parts.

Fields: part_id, entity_id, part_index, part_type, bbox, properties JSONB, metadata.

### entity_part_h3

Canonical H3 storage.

Fields: part_id, resolution, ring_id, ring_type, h3_index.

Polygon ring_type: outer or hole. Line: line. Point: none.

### entity_point

Exact point coordinates for point entities.

### raster_datasets

Raster metadata and external file URI only.

### ingestion_runs / ingestion_parts / ingestion_h3_cells

Pipeline history and generated boundary/line H3 output. These are separate from canonical entity storage.

## Display model

Database stores:

Boundary H3 -> ring metadata -> part attributes

API display reconstructs:

Boundary H3 -> approximate ring -> H3 fill -> hole subtraction -> Map cells

Therefore the database stays small while the Map still shows interior H3 cells.

## Query strategy

Attribute: JSONB GIN index on entity_parts.properties.

BBox: part bbox candidates.

Polygon: boundary H3 candidates plus bbox candidates; exact original geometry intersection is intentionally unavailable.

Nearby: exact point distance for entity_point.

Line: H3 coverage lookup.

## H3 Analytics layer

`h3_features` is a derived analytics table. It does not replace `entity_part_h3`.

- `entity_part_h3` = canonical Boundary H3 storage for compact spatial representation.
- `h3_features` = analytics-oriented H3 rows for counting, coverage and map metrics.
- Polygon rows can store `cell_coverage` (fraction of cell covered) and `polygon_coverage` (fraction of part area covered).
- `centroid_cell` marks the H3 cell containing the part centroid.
- `pixel_coverage` is reserved for raster-derived coverage and is nullable for vector data.
- Original geometry is still not persisted.

## Dataset Catalog

`datasets` now also supports source, owner, version, source format, geographic coverage, tags, license, update frequency, schema and lineage.

## Compatibility

entity_h3 is exposed as a view over entity_part_h3 so simple H3 lookup code can continue to work.

## Storage principle

Do not store full polygon coverage as the canonical data. Store boundary H3 only and reconstruct display coverage when required.

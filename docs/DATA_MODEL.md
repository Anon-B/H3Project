# Data Model

## Canonical model
The current application model is dataset -> entity -> entity_part -> entity_part_h3, with entity_attributes for source properties.

## datasets
Dataset registry and configuration.
Important fields: dataset_id, name, data_type, h3_resolution, metadata, source, owner, version, source_format, geographic_coverage, tags, license, update_frequency, schema_definition, lineage.

## entities
Minimal entity registry: entity_id + dataset_id.

## entity_attributes
One row per entity. Source properties are stored as JSONB in `properties`.
Use this table for Entity-level attributes; do not duplicate source properties into new H3 display tables.

## entity_parts
One spatial part per entity.
part_type = point | line | polygon.
Stores part index, bbox, reserved properties JSONB and reconstruction metadata.

## entity_point
Exact latitude/longitude for Point entities.

## entity_part_h3
Canonical H3 storage.
Primary key: part_id + resolution + ring_id + h3_index.
ring_type = none | outer | hole | line.
Polygon rows are boundary cells only.

## entity_h3
Compatibility view joining entity_part_h3 to entity_parts and exposing entity_id, resolution and h3_index.

## ingestion history
ingestion_runs = one pipeline execution.
ingestion_parts = source feature/part mapping for that run.
ingestion_h3_cells = generated H3 audit rows for that run.

## raster_datasets
Metadata and external file URI for future raster ingestion. Raster processing is not the primary current web ingestion path.

## Display model
```text
Boundary H3 + ring metadata
        -> frontend reconstruction
        -> display H3 cells
        -> GPU rendering
```

## Storage rules
1. Do not add h3_features.
2. Do not persist every display cell as canonical data.
3. Keep source attributes in entity_attributes.
4. Keep polygon ring semantics in entity_part_h3.
5. If changing canonical storage, update schema, API, ingestion, frontend and migration docs together.

## Schema lifecycle
`sql/schema.sql` is the current complete schema definition.
`sql/migrations/002_h3_analytics_catalog.sql` contains migration history for the analytics/catalog transition.
For a fresh DB, load schema.sql. For an existing DB, apply migrations deliberately and verify the resulting schema.


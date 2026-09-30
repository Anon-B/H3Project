# Data Dictionary

## datasets

| Column | Type | Meaning |
|---|---|---|
| dataset_id | BIGSERIAL | dataset ID |
| name | TEXT | unique dataset name |
| data_type | TEXT | point, multipoint, polygon, multipolygon, geometry_collection, raster, or mixed |
| h3_resolution | SMALLINT | H3 resolution selected by the dataset |
| metadata | JSONB | dataset configuration/metadata |
| created_at | TIMESTAMPTZ | creation time |
| updated_at | TIMESTAMPTZ | last update time |

## entities

| Column | Type | Meaning |
|---|---|---|
| entity_id | BIGINT | global entity ID |
| dataset_id | BIGINT | owning dataset |

This table intentionally contains no geometry, coordinates, bbox, or dynamic properties.

## entity_point

| Column | Type | Meaning |
|---|---|---|
| entity_id | BIGINT | entity reference |
| latitude | DOUBLE PRECISION | WGS84 latitude |
| longitude | DOUBLE PRECISION | WGS84 longitude |

Only entities that have point coordinates need a row here.

## entity_h3

| Column | Type | Meaning |
|---|---|---|
| entity_id | BIGINT | entity reference |
| resolution | SMALLINT | H3 resolution |
| h3_index | TEXT | H3 cell identifier |

Primary key: `entity_id, resolution, h3_index`.

Lookup index: `resolution, h3_index, entity_id`.

## entity_attributes

| Column | Type | Meaning |
|---|---|---|
| entity_id | BIGINT | entity reference |
| properties | JSONB | flexible dataset-specific attributes |

A GIN index supports general JSONB searches.

## raster_datasets

| Column | Type | Meaning |
|---|---|---|
| raster_id | BIGSERIAL | raster record ID |
| dataset_id | BIGINT | owning dataset |
| file_uri | TEXT | external raster location |
| min_lat/max_lat | DOUBLE PRECISION | latitude extent |
| min_lng/max_lng | DOUBLE PRECISION | longitude extent |
| format | TEXT | raster format |
| size_bytes | BIGINT | file size |
| metadata | JSONB | raster metadata |

## ingestion_runs

Tracks each ingestion execution.

## ingestion_h3_cells

Stores generated H3 cells for ingestion runs before/independent of canonical entity loading.

## Governance

- Coordinate system: EPSG:4326 / WGS84.
- Original geometry is intentionally not retained.
- Dataset chooses its H3 resolution.
- Do not duplicate H3 resolutions as fixed columns on entities.
- Keep frequently queried attributes indexed; avoid unnecessary per-attribute indexes.
- Raster binary data belongs in object storage/filesystem, not the entity tables.

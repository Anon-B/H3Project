# Data Model

## Design goal

The database is a lightweight entity registry plus specialized tables.

- Original geometry is not stored.
- `entities` stores only identity and dataset ownership.
- Point coordinates are stored only for point entities.
- H3 is the primary spatial index.
- Dynamic attributes are stored as JSONB.
- Raster files stay outside PostgreSQL; PostgreSQL stores metadata and URI.
- Dataset controls the H3 resolution.

## Tables

### datasets

Dataset definition and configuration.

```
dataset_id
name
data_type
h3_resolution
metadata
created_at
updated_at
```

### entities

Minimal entity registry.

```
entity_id
dataset_id
```

### entity_point

Optional point coordinates.

```
entity_id
latitude
longitude
```

### entity_h3

Spatial index for all supported spatial entities.

```
entity_id
resolution
h3_index
```

### entity_attributes

Flexible dataset-specific attributes.

```
entity_id
properties JSONB
```

### raster_datasets

Raster metadata only. Raster bytes are stored in object storage/filesystem.

### ingestion_runs / ingestion_h3_cells

Pipeline execution history and generated H3 output. These are separate from canonical entities.

## Query strategy

BBox:
H3 candidate lookup -> entity lookup -> point coordinate filter where applicable.

Nearby:
H3 neighborhood -> entity_point -> exact distance calculation from latitude/longitude.

Polygon intersection:
H3 coverage overlap is used as the spatial candidate/intersection mechanism because original geometry is intentionally not retained.

Attribute search:
JSONB GIN index for flexible properties. Frequently queried attributes can later be promoted to typed/search-specific indexes.

## Storage principle

Do not duplicate Res5/Res8/Res11 columns in every entity. A dataset stores one selected resolution, and entity_h3 stores the generated H3 cells at that resolution.

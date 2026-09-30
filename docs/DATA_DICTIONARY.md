# Data Dictionary

## datasets

| Column | Meaning |
|---|---|
| dataset_id | Dataset identifier |
| name | Unique dataset name |
| data_type | point, line, polygon, multipolygon, geometry_collection, raster, mixed |
| h3_resolution | Canonical H3 resolution 5-15 |
| metadata | Dataset configuration JSONB |

## entities

| Column | Meaning |
|---|---|
| entity_id | Entity identifier |
| dataset_id | Owning dataset |

## entity_parts

| Column | Meaning |
|---|---|
| part_id | Spatial part identifier |
| entity_id | Parent entity |
| part_index | Part order inside entity |
| part_type | point, line, polygon |
| min_lat/max_lat | Derived latitude bounding box |
| min_lng/max_lng | Derived longitude bounding box |
| properties | Attributes for this spatial part, JSONB |
| metadata | Storage/reconstruction metadata |

## entity_part_h3

| Column | Meaning |
|---|---|
| part_id | Spatial part |
| resolution | H3 resolution |
| ring_id | Ring identifier; 0 is outer for Polygon |
| ring_type | outer, hole, line, none |
| h3_index | Stored H3 cell |

For Polygon, only boundary H3 cells are stored. Interior H3 cells are reconstructed at display time.

## entity_point

Exact latitude/longitude for Point entities.

## ingestion_parts

Records the source feature part created during a pipeline run.

## ingestion_h3_cells

Pipeline output H3 records, including ring metadata. Polygon rows represent stored boundary H3; Line rows represent line coverage H3.

## h3_features

| Column | Meaning |
|---|---|
| h3_feature_id | Analytics row identifier |
| dataset_id | Dataset |
| entity_id | Source entity |
| part_id | Source spatial part |
| resolution | H3 resolution |
| h3_index | Analytics H3 cell |
| feature_type | point, line, polygon |
| cell_coverage | Fraction of the H3 cell covered by a polygon |
| polygon_coverage | Fraction of the source polygon part covered by the H3 cell |
| centroid_cell | H3 cell contains the part centroid |
| pixel_coverage | Raster pixel coverage; nullable for vector |
| properties | Copied source attributes |

## datasets catalog fields

`source`, `owner`, `version`, `source_format`, `geographic_coverage`, `tags`, `license`, `update_frequency`, `schema_definition`, `lineage`

## entity_h3 compatibility view

The entity_h3 view exposes entity_id, resolution and h3_index from entity_part_h3 for simple legacy H3 lookups.

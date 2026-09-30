# Data Dictionary

## spatial_entities
| Column | Type | Meaning |
|---|---|---|
| id | BIGINT | unique entity ID |
| dataset | TEXT | source/dataset name |
| lat/lng | DOUBLE | WGS84 coordinate |
| geom | Point(4326) | PostGIS geometry |
| h3_res11 | TEXT | object-level H3 |
| h3_res8 | TEXT | medium aggregation cell |
| h3_res5 | TEXT | coarse aggregation cell |
| is_active | BOOLEAN | soft-delete/status flag |
| updated_at | TIMESTAMPTZ | last source update |

## Gold tables
`h3_summary` aggregates Res5; `h3_summary_res8` aggregates Res8.
Both contain `entity_count`, `active_count`, and `updated_at`.

## Governance rules
- Coordinate system: EPSG:4326 / WGS84.
- H3 parent relationship must be Res11 → Res8 → Res5.
- `id` is unique.
- Inactive rows remain for history and are excluded by default from API queries.
- Analytical geometry is not visually smoothed.

# Data Model

## spatial_entities
id, dataset, lat, lng, geom, h3_res11, h3_res8, h3_res5, is_active, updated_at

## h3_summary
h3_res5, h3_res8, entity_count, updated_at

## Index rationale
H3 indexes accelerate candidate lookup. GiST handles exact geometry predicates.

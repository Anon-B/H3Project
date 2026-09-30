ALTER TABLE datasets ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT '';
ALTER TABLE datasets ADD COLUMN IF NOT EXISTS owner TEXT NOT NULL DEFAULT '';
ALTER TABLE datasets ADD COLUMN IF NOT EXISTS version TEXT NOT NULL DEFAULT '1.0.0';
ALTER TABLE datasets ADD COLUMN IF NOT EXISTS source_format TEXT NOT NULL DEFAULT '';
ALTER TABLE datasets ADD COLUMN IF NOT EXISTS geographic_coverage JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE datasets ADD COLUMN IF NOT EXISTS tags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[];
ALTER TABLE datasets ADD COLUMN IF NOT EXISTS license TEXT NOT NULL DEFAULT '';
ALTER TABLE datasets ADD COLUMN IF NOT EXISTS update_frequency TEXT NOT NULL DEFAULT '';
ALTER TABLE datasets ADD COLUMN IF NOT EXISTS schema_definition JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE datasets ADD COLUMN IF NOT EXISTS lineage JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS h3_features (
  h3_feature_id BIGSERIAL PRIMARY KEY,
  dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id) ON DELETE CASCADE,
  entity_id BIGINT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  part_id BIGINT NOT NULL REFERENCES entity_parts(part_id) ON DELETE CASCADE,
  resolution SMALLINT NOT NULL CHECK (resolution BETWEEN 5 AND 15),
  h3_index TEXT NOT NULL,
  feature_type TEXT NOT NULL CHECK (feature_type IN ('point','line','polygon')),
  cell_coverage DOUBLE PRECISION,
  polygon_coverage DOUBLE PRECISION,
  centroid_cell BOOLEAN NOT NULL DEFAULT FALSE,
  pixel_coverage DOUBLE PRECISION,
  properties JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(dataset_id,part_id,resolution,h3_index)
);

CREATE INDEX IF NOT EXISTS idx_h3_features_lookup
  ON h3_features(dataset_id,resolution,h3_index);
CREATE INDEX IF NOT EXISTS idx_h3_features_entity
  ON h3_features(entity_id,resolution);
CREATE INDEX IF NOT EXISTS idx_h3_features_properties
  ON h3_features USING GIN(properties);

INSERT INTO h3_features(
  dataset_id,entity_id,part_id,resolution,h3_index,feature_type,
  cell_coverage,polygon_coverage,centroid_cell,pixel_coverage,properties
)
SELECT DISTINCT e.dataset_id,p.entity_id,p.part_id,h.resolution,h.h3_index,
       p.part_type,NULL::double precision,NULL::double precision,FALSE,
       NULL::double precision,p.properties
FROM entity_part_h3 h
JOIN entity_parts p ON p.part_id=h.part_id
JOIN entities e ON e.entity_id=p.entity_id
ON CONFLICT DO NOTHING;
CREATE INDEX IF NOT EXISTS idx_datasets_catalog_tags
  ON datasets USING GIN(tags);

COMMENT ON TABLE h3_features IS
  'Derived H3 analytics layer. Original geometry is not stored.';
COMMENT ON COLUMN h3_features.cell_coverage IS
  'Fraction of H3 cell area covered by the source polygon, 0..1.';
COMMENT ON COLUMN h3_features.polygon_coverage IS
  'Fraction of source polygon area covered by this H3 cell, 0..1.';
COMMENT ON COLUMN h3_features.pixel_coverage IS
  'Raster pixel coverage, nullable for vector datasets.';


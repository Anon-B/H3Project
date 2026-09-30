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

CREATE TABLE IF NOT EXISTS entity_attributes (
  entity_id BIGINT PRIMARY KEY REFERENCES entities(entity_id) ON DELETE CASCADE,
  properties JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_entity_attributes_gin
  ON entity_attributes USING GIN(properties);

INSERT INTO entity_attributes(entity_id,properties)
SELECT e.entity_id,COALESCE(p.properties,'{}'::jsonb)
FROM entities e
JOIN entity_parts p ON p.entity_id=e.entity_id AND p.part_index=0
ON CONFLICT(entity_id) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_datasets_catalog_tags
  ON datasets USING GIN(tags);

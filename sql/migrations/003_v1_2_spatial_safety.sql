-- v1.2 data-safety and spatial correctness
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_attribute
    WHERE attrelid='entities'::regclass
      AND attname='entity_id'
      AND attidentity <> ''
  ) THEN
    ALTER TABLE entities
      ALTER COLUMN entity_id ADD GENERATED ALWAYS AS IDENTITY;
  END IF;
END $$;

SELECT setval(
  pg_get_serial_sequence('entities','entity_id'),
  GREATEST(COALESCE((SELECT MAX(entity_id) FROM entities),0),1),
  true
);

ALTER TABLE entity_parts
  ADD COLUMN IF NOT EXISTS geom geometry(Geometry,4326);

CREATE INDEX IF NOT EXISTS idx_entity_parts_geom
  ON entity_parts USING GIST (geom);

ALTER TABLE ingestion_runs
  ADD COLUMN IF NOT EXISTS finished_at TIMESTAMPTZ;

ALTER TABLE entities
  ADD COLUMN IF NOT EXISTS ingestion_run_id BIGINT
  REFERENCES ingestion_runs(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_entities_ingestion_run
  ON entities(ingestion_run_id);

UPDATE entity_parts
SET geom=ST_SetSRID(
  ST_MakeEnvelope(min_lng,min_lat,max_lng,max_lat,4326),
  4326
)
WHERE geom IS NULL
  AND min_lng IS NOT NULL
  AND min_lat IS NOT NULL
  AND max_lng IS NOT NULL
  AND max_lat IS NOT NULL;

ANALYZE;

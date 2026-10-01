-- v1.3 hardening: active datasets, migration tracking, auth support and safe observability
ALTER TABLE datasets DROP CONSTRAINT IF EXISTS datasets_name_key;
CREATE UNIQUE INDEX IF NOT EXISTS uq_datasets_active_name
  ON datasets(name) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  description TEXT NOT NULL,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO schema_migrations(version,description)
VALUES ('001','legacy schema baseline'),('002','analytics catalog'),('003','spatial safety'),('004','lifecycle and jobs')
ON CONFLICT(version) DO NOTHING;
CREATE INDEX IF NOT EXISTS idx_entity_parts_geom
  ON entity_parts USING GIST(geom);

CREATE INDEX IF NOT EXISTS idx_entity_parts_bbox
  ON entity_parts(min_lat,max_lat,min_lng,max_lng);

CREATE INDEX IF NOT EXISTS idx_entities_ingestion_run
  ON entities(ingestion_run_id);

CREATE INDEX IF NOT EXISTS idx_ingestion_runs_status
  ON ingestion_runs(status,id DESC);

INSERT INTO schema_migrations(version,description)
VALUES ('005','v1.3 hardening')
ON CONFLICT(version) DO NOTHING;

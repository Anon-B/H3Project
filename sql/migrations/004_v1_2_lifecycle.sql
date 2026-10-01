-- v1.2 lifecycle, soft delete and ingestion dedupe
ALTER TABLE datasets ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_datasets_active_name ON datasets(name) WHERE deleted_at IS NULL;

ALTER TABLE ingestion_runs ADD COLUMN IF NOT EXISTS finished_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_status ON ingestion_runs(status, id DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_ingestion_h3_run_cell
ON ingestion_h3_cells(run_id,resolution,h3_index,feature_index,part_index,ring_id,ring_type);

CREATE INDEX IF NOT EXISTS idx_entities_ingestion_run
ON entities(ingestion_run_id);

ANALYZE;

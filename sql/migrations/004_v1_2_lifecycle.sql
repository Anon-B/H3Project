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

CREATE TABLE IF NOT EXISTS ingestion_jobs (
  job_id UUID PRIMARY KEY,
  dataset TEXT NOT NULL,
  resolution INTEGER NOT NULL CHECK (resolution BETWEEN 5 AND 15),
  payload JSONB NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','running','completed','failed')),
  result JSONB,
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status_created ON ingestion_jobs(status,created_at);

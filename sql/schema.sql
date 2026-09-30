CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE IF NOT EXISTS spatial_entities (
 id BIGINT PRIMARY KEY, dataset TEXT NOT NULL, lat DOUBLE PRECISION NOT NULL,
 lng DOUBLE PRECISION NOT NULL, geom geometry(Point,4326),
 h3_res11 TEXT NOT NULL, h3_res8 TEXT NOT NULL, h3_res5 TEXT NOT NULL,
 is_active BOOLEAN NOT NULL DEFAULT TRUE, updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_entities_h3_11 ON spatial_entities(h3_res11);
CREATE INDEX IF NOT EXISTS idx_entities_h3_8 ON spatial_entities(h3_res8);
CREATE INDEX IF NOT EXISTS idx_entities_h3_5_active ON spatial_entities(h3_res5,is_active);
CREATE INDEX IF NOT EXISTS idx_entities_updated_at ON spatial_entities(updated_at);
CREATE INDEX IF NOT EXISTS idx_entities_geom_gist ON spatial_entities USING GIST(geom);
CREATE TABLE IF NOT EXISTS h3_summary (
 h3_res5 TEXT PRIMARY KEY, entity_count BIGINT NOT NULL, active_count BIGINT NOT NULL,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS h3_summary_res8 (
 h3_res8 TEXT PRIMARY KEY, entity_count BIGINT NOT NULL, active_count BIGINT NOT NULL,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_summary_res5_updated ON h3_summary(updated_at);
CREATE INDEX IF NOT EXISTS idx_summary_res8_updated ON h3_summary_res8(updated_at);

CREATE TABLE IF NOT EXISTS ingestion_runs (
 id BIGSERIAL PRIMARY KEY, source_type TEXT NOT NULL, input_feature_count INTEGER NOT NULL,
 output_cell_count BIGINT NOT NULL, status TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE TABLE IF NOT EXISTS ingestion_h3_cells (
 id BIGSERIAL PRIMARY KEY, run_id BIGINT NOT NULL REFERENCES ingestion_runs(id) ON DELETE CASCADE,
 feature_id TEXT, feature_index INTEGER NOT NULL, source_type TEXT NOT NULL,
 resolution SMALLINT NOT NULL CHECK (resolution BETWEEN 5 AND 15), h3_index TEXT NOT NULL,
 properties JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ingestion_h3_cells_run ON ingestion_h3_cells(run_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_h3_cells_h3 ON ingestion_h3_cells(resolution,h3_index);

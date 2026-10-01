CREATE EXTENSION IF NOT EXISTS postgis;


CREATE TABLE datasets (
  dataset_id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  data_type TEXT NOT NULL CHECK (data_type IN ('point','multipoint','line','multiline','polygon','multipolygon','geometry_collection','raster','mixed')),
  h3_resolution SMALLINT NOT NULL CHECK (h3_resolution BETWEEN 5 AND 15),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  source TEXT NOT NULL DEFAULT '',
  owner TEXT NOT NULL DEFAULT '',
  version TEXT NOT NULL DEFAULT '1.0.0',
  source_format TEXT NOT NULL DEFAULT '',
  geographic_coverage JSONB NOT NULL DEFAULT '{}'::jsonb,
  tags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  license TEXT NOT NULL DEFAULT '',
  update_frequency TEXT NOT NULL DEFAULT '',
  schema_definition JSONB NOT NULL DEFAULT '{}'::jsonb,
  lineage JSONB NOT NULL DEFAULT '{}'::jsonb,
  deleted_at TIMESTAMPTZ
);

CREATE TABLE entities (
  entity_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id) ON DELETE CASCADE
);
CREATE INDEX idx_entities_dataset ON entities(dataset_id, entity_id);
CREATE UNIQUE INDEX uq_datasets_active_name ON datasets(name) WHERE deleted_at IS NULL;

CREATE TABLE entity_parts (
  part_id BIGSERIAL PRIMARY KEY,
  entity_id BIGINT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  part_index INTEGER NOT NULL,
  part_type TEXT NOT NULL CHECK (part_type IN ('point','line','polygon')),
  min_lat DOUBLE PRECISION,
  min_lng DOUBLE PRECISION,
  max_lat DOUBLE PRECISION,
  max_lng DOUBLE PRECISION,
  geom geometry(Geometry,4326),
  properties JSONB NOT NULL DEFAULT '{}'::jsonb,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE(entity_id, part_index),
  CHECK (min_lat IS NULL OR min_lat BETWEEN -90 AND 90),
  CHECK (max_lat IS NULL OR max_lat BETWEEN -90 AND 90),
  CHECK (min_lng IS NULL OR min_lng BETWEEN -180 AND 180),
  CHECK (max_lng IS NULL OR max_lng BETWEEN -180 AND 180)
);
CREATE INDEX idx_entity_parts_entity ON entity_parts(entity_id, part_index);
CREATE INDEX idx_entity_parts_bbox ON entity_parts(min_lat, max_lat, min_lng, max_lng);
CREATE INDEX idx_entity_parts_geom ON entity_parts USING GIST(geom);
CREATE INDEX idx_entity_parts_properties ON entity_parts USING GIN(properties);

CREATE TABLE entity_point (
  entity_id BIGINT PRIMARY KEY REFERENCES entities(entity_id) ON DELETE CASCADE,
  latitude DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
  longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180)
);
CREATE INDEX idx_entity_point_lat_lng ON entity_point(latitude, longitude);

CREATE TABLE entity_part_h3 (
  part_id BIGINT NOT NULL REFERENCES entity_parts(part_id) ON DELETE CASCADE,
  resolution SMALLINT NOT NULL CHECK (resolution BETWEEN 5 AND 15),
  ring_id INTEGER NOT NULL DEFAULT 0,
  ring_type TEXT NOT NULL CHECK (ring_type IN ('none','outer','hole','line')),
  h3_index TEXT NOT NULL,
  PRIMARY KEY (part_id, resolution, ring_id, h3_index)
);
CREATE INDEX idx_entity_part_h3_lookup ON entity_part_h3(resolution, h3_index, part_id);
CREATE INDEX idx_entity_part_h3_part ON entity_part_h3(part_id, resolution);

CREATE VIEW entity_h3 AS
SELECT p.entity_id, h.resolution, h.h3_index
FROM entity_part_h3 h JOIN entity_parts p ON p.part_id=h.part_id;

CREATE TABLE entity_attributes (
  entity_id BIGINT PRIMARY KEY REFERENCES entities(entity_id) ON DELETE CASCADE,
  properties JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX idx_entity_attributes_gin ON entity_attributes USING GIN(properties);

CREATE TABLE raster_datasets (
  raster_id BIGSERIAL PRIMARY KEY,
  dataset_id BIGINT NOT NULL UNIQUE REFERENCES datasets(dataset_id) ON DELETE CASCADE,
  file_uri TEXT NOT NULL,
  min_lat DOUBLE PRECISION,
  min_lng DOUBLE PRECISION,
  max_lat DOUBLE PRECISION,
  max_lng DOUBLE PRECISION,
  format TEXT,
  size_bytes BIGINT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (min_lat IS NULL OR min_lat BETWEEN -90 AND 90),
  CHECK (max_lat IS NULL OR max_lat BETWEEN -90 AND 90),
  CHECK (min_lng IS NULL OR min_lng BETWEEN -180 AND 180),
  CHECK (max_lng IS NULL OR max_lng BETWEEN -180 AND 180)
);
CREATE INDEX idx_raster_bbox ON raster_datasets(min_lat, min_lng, max_lat, max_lng);

CREATE TABLE ingestion_runs (
  id BIGSERIAL PRIMARY KEY,
  dataset_id BIGINT REFERENCES datasets(dataset_id) ON DELETE SET NULL,
  source_type TEXT NOT NULL,
  input_feature_count INTEGER NOT NULL,
  output_cell_count BIGINT NOT NULL,
  status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  finished_at TIMESTAMPTZ
);
CREATE INDEX idx_ingestion_runs_dataset ON ingestion_runs(dataset_id, id DESC);

CREATE TABLE ingestion_parts (
  id BIGSERIAL PRIMARY KEY,
  run_id BIGINT NOT NULL REFERENCES ingestion_runs(id) ON DELETE CASCADE,
  feature_id TEXT,
  feature_index INTEGER NOT NULL,
  part_index INTEGER NOT NULL,
  part_type TEXT NOT NULL,
  ring_count INTEGER NOT NULL DEFAULT 0,
  properties JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX idx_ingestion_parts_run ON ingestion_parts(run_id);

CREATE TABLE ingestion_h3_cells (
  id BIGSERIAL PRIMARY KEY,
  run_id BIGINT NOT NULL REFERENCES ingestion_runs(id) ON DELETE CASCADE,
  part_id BIGINT REFERENCES ingestion_parts(id) ON DELETE CASCADE,
  feature_id TEXT,
  feature_index INTEGER NOT NULL,
  part_index INTEGER NOT NULL DEFAULT 0,
  ring_id INTEGER NOT NULL DEFAULT 0,
  ring_type TEXT NOT NULL DEFAULT 'none',
  source_type TEXT NOT NULL,
  resolution SMALLINT NOT NULL CHECK (resolution BETWEEN 5 AND 15),
  h3_index TEXT NOT NULL,
  properties JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_ingestion_h3_cells_run ON ingestion_h3_cells(run_id);
CREATE INDEX idx_ingestion_h3_cells_h3 ON ingestion_h3_cells(resolution, h3_index);
CREATE UNIQUE INDEX uq_ingestion_h3_run_cell ON ingestion_h3_cells(run_id,resolution,h3_index,feature_index,part_index,ring_id,ring_type);

ANALYZE;


CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  description TEXT NOT NULL,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
INSERT INTO schema_migrations(version,description) VALUES ('004','baseline from current schema') ON CONFLICT(version) DO NOTHING;

CREATE TABLE IF NOT EXISTS ingestion_jobs (
  job_id UUID PRIMARY KEY,
  dataset TEXT NOT NULL,
  resolution INTEGER NOT NULL CHECK (resolution BETWEEN 5 AND 15),
  payload JSONB NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','running','completed','failed')),
  result JSONB, error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), started_at TIMESTAMPTZ, finished_at TIMESTAMPTZ, updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status_created ON ingestion_jobs(status,created_at);

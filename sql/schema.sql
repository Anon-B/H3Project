CREATE EXTENSION IF NOT EXISTS postgis;

DROP TABLE IF EXISTS spatial_entities CASCADE;
DROP TABLE IF EXISTS ingestion_h3_cells CASCADE;
DROP TABLE IF EXISTS ingestion_runs CASCADE;
DROP TABLE IF EXISTS raster_datasets CASCADE;
DROP TABLE IF EXISTS entity_attributes CASCADE;
DROP TABLE IF EXISTS entity_h3 CASCADE;
DROP TABLE IF EXISTS entity_point CASCADE;
DROP TABLE IF EXISTS entities CASCADE;
DROP TABLE IF EXISTS datasets CASCADE;
DROP TABLE IF EXISTS h3_summary_res8 CASCADE;
DROP TABLE IF EXISTS h3_summary CASCADE;

CREATE TABLE datasets (
  dataset_id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  data_type TEXT NOT NULL CHECK (data_type IN ('point','multipoint','polygon','multipolygon','geometry_collection','raster','mixed')),
  h3_resolution SMALLINT NOT NULL CHECK (h3_resolution BETWEEN 5 AND 15),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE entities (
  entity_id BIGINT PRIMARY KEY,
  dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id) ON DELETE CASCADE
);
CREATE INDEX idx_entities_dataset ON entities(dataset_id, entity_id);

CREATE TABLE entity_point (
  entity_id BIGINT PRIMARY KEY REFERENCES entities(entity_id) ON DELETE CASCADE,
  latitude DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
  longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180)
);
CREATE INDEX idx_entity_point_lat_lng ON entity_point(latitude, longitude);

CREATE TABLE entity_h3 (
  entity_id BIGINT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
  resolution SMALLINT NOT NULL CHECK (resolution BETWEEN 5 AND 15),
  h3_index TEXT NOT NULL,
  PRIMARY KEY (entity_id, resolution, h3_index)
);
CREATE INDEX idx_entity_h3_lookup ON entity_h3(resolution, h3_index, entity_id);
CREATE INDEX idx_entity_h3_dataset_lookup ON entity_h3(entity_id, resolution);
CREATE TABLE entity_attributes (
  entity_id BIGINT PRIMARY KEY REFERENCES entities(entity_id) ON DELETE CASCADE,
  properties JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX idx_entity_attributes_gin ON entity_attributes USING GIN (properties);

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
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX idx_ingestion_runs_dataset ON ingestion_runs(dataset_id, id DESC);
CREATE TABLE ingestion_h3_cells (
  id BIGSERIAL PRIMARY KEY,
  run_id BIGINT NOT NULL REFERENCES ingestion_runs(id) ON DELETE CASCADE,
  feature_id TEXT,
  feature_index INTEGER NOT NULL,
  source_type TEXT NOT NULL,
  resolution SMALLINT NOT NULL CHECK (resolution BETWEEN 5 AND 15),
  h3_index TEXT NOT NULL,
  properties JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_ingestion_h3_cells_run ON ingestion_h3_cells(run_id);
CREATE INDEX idx_ingestion_h3_cells_h3 ON ingestion_h3_cells(resolution, h3_index);

ANALYZE;

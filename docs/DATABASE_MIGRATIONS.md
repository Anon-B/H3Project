# Database & Migration Guide

## Source of truth
`sql/schema.sql` describes the current complete schema for a fresh database.
`sql/migrations/` contains changes applied to existing databases.

## Current canonical tables
`datasets`, `entities`, `entity_attributes`, `entity_parts`, `entity_point`, `entity_part_h3`, `raster_datasets`, `ingestion_runs`, `ingestion_parts`, `ingestion_h3_cells`.

## Migration 002
`002_h3_analytics_catalog.sql` belongs to the transition that introduced entity attributes, Boundary-H3 analytics/catalog concepts and dataset metadata.
Always inspect the migration before applying it to an existing DB.

## Migration tracking

Current databases use schema_migrations with one row per applied migration.
The canonical fresh schema records the current baseline and the startup runner
applies any migration files that are newer than that baseline.

The standard startup path is:

1. Start PostgreSQL/Redis/API/frontend.
2. Wait for API availability.
3. Run scripts/migrate.sh inside the API container.
4. Start/verify the API health endpoints.

scripts/migrate.sh is idempotent: an already applied migration is skipped.

## Fresh database
```bash
docker-compose down
docker volume ls
docker-compose up -d --build
docker-compose exec -T db psql -U h3 -d h3project -f /app/sql/schema.sql
```
Do not run schema.sql against a database that contains data you need; use the migration runner instead.

## Existing database
Back up first.
```bash
docker-compose exec -T api sh scripts/backup.sh /app/backup
docker-compose exec -T db psql -U h3 -d h3project -v ON_ERROR_STOP=1 < sql/migrations/<migration>.sql
```

## After migration
Run API tests, inspect table definitions and verify dataset/map ingestion.

## Migration rules
1. Never silently change canonical storage.
2. Add migration before changing existing production-like DBs.
3. Update DATA_MODEL and DATA_DICTIONARY.
4. Update API_REFERENCE when response/schema changes.
5. Add regression test.
6. Back up before destructive changes.

## Warning
The benchmark-era scripts that reference spatial_entities/h3_summary are not the canonical GeoJSON application model. Treat them as legacy benchmark assets until migrated.


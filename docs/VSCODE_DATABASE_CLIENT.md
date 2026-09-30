# VS Code Database Client — H3Project

## PostgreSQL
Current Docker database is published to the Mac host.
- Host: 127.0.0.1
- Port: 5432
- Database: h3project
- Username: h3
- Password: h3
- SSL: disabled/default local connection

Connection URI:
`postgresql://h3:h3@127.0.0.1:5432/h3project`

## VS Code
Install a PostgreSQL-capable database extension, then create a PostgreSQL connection with the values above.

## Current useful tables
- datasets
- entities
- entity_attributes
- entity_parts
- entity_point
- entity_part_h3
- ingestion_runs
- ingestion_parts
- ingestion_h3_cells

## Useful SQL
```sql
SELECT current_database(), current_user;
SELECT * FROM datasets ORDER BY dataset_id DESC LIMIT 20;
SELECT count(*) FROM entities;
SELECT count(*) FROM entity_part_h3;
SELECT * FROM ingestion_runs ORDER BY id DESC LIMIT 20;
```

## Legacy benchmark tables
If present, `spatial_entities`, `h3_summary` and `h3_summary_res8` belong to the historical benchmark track.
They should not be used as the definition of the current ingestion data model.

## Docker
```bash
docker-compose ps
docker ps --format '{{.Names}} {{.Ports}}'
```
The PostgreSQL data volume is `pgdata`.


# VS Code Database Client — H3Project

## PostgreSQL Connection

H3Project runs PostgreSQL in Docker and publishes it to the Mac host.

- Host: `127.0.0.1`
- Port: `5432`
- Database: `h3project`
- Username: `h3`
- Password: `h3`
- SSL: Disabled / default local connection

Connection URI:

`postgresql://h3:h3@127.0.0.1:5432/h3project`

## VS Code

Install the current Database Client extension from the VS Code Marketplace:

`cweijan.vscode-database-client2`

Then:

1. Open VS Code.
2. Open the **Database** panel.
3. Click `+`.
4. Select **PostgreSQL**.
5. Enter the connection values above.
6. Connect.
7. Refresh the connection metadata if the tables do not appear immediately.

Useful tables for H3Project:

- `spatial_entities` — 10M POC source/entity data
- `h3_summary` — Res5 summary
- `h3_summary_res8` — Res8 summary
- `ingestion_runs` — ingestion execution history
- `ingestion_h3_cells` — generated H3 cells per ingestion run

## Test SQL

```sql
SELECT current_database(), current_user;

SELECT dataset, count(*)
FROM spatial_entities
GROUP BY dataset
ORDER BY dataset;

SELECT id, source_type, input_feature_count, output_cell_count, status, created_at
FROM ingestion_runs
ORDER BY id DESC
LIMIT 20;
```

## Docker

Check that PostgreSQL is published on the host:

```bash
docker ps --format '{{.Names}} {{.Ports}}'
```

Expected:

`h3project-db 0.0.0.0:5432->5432/tcp`

The database is persisted in the Docker volume `pgdata`, so restarting the containers does not recreate the database from scratch.

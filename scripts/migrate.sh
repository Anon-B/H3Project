#!/bin/sh
set -eu

DB_URL="${DATABASE_URL:-postgresql://h3:h3@db:5432/h3project}"
MIGRATIONS_DIR="${MIGRATIONS_DIR:-/app/sql/migrations}"

echo "=== H3Project DB MIGRATIONS ==="
python3 - "$DB_URL" "$MIGRATIONS_DIR" <<'PY'
import os
import sys
import glob
import psycopg

db_url, migration_dir = sys.argv[1:3]
files = sorted(glob.glob(os.path.join(migration_dir, "*.sql")))

with psycopg.connect(db_url) as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    applied = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
    for path in files:
        version = os.path.basename(path).split("_", 1)[0]
        if version in applied:
            print(f"[skip] {os.path.basename(path)}")
            continue
        sql = open(path, encoding="utf-8").read()
        print(f"[apply] {os.path.basename(path)}")
        conn.execute(sql)
        conn.execute(
            "INSERT INTO schema_migrations(version,description) VALUES (%s,%s) ON CONFLICT(version) DO NOTHING",
            (version, os.path.basename(path)),
        )
        conn.commit()
print("=== MIGRATIONS READY ===")
PY

#!/bin/sh
set -eu
OUT=${1:-/app/backup}
mkdir -p "$OUT"
pg_dump -Fc "$DATABASE_URL" > "$OUT/h3project_$(date +%Y%m%d_%H%M%S).dump"
find "$OUT" -type f -name '*.dump' -mtime +7 -delete
printf 'backup complete: %s\n' "$OUT"

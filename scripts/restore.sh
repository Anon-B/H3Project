#!/bin/sh
set -eu
DUMP=${1:?usage: restore.sh /path/file.dump}
pg_restore --clean --if-exists --no-owner -d "$DATABASE_URL" "$DUMP"
printf 'restore complete\n'

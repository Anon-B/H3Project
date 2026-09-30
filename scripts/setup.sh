#!/bin/zsh
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"
colima start --cpu 10 --memory 20 --disk 80 || true
docker context use colima
docker-compose up -d --build
for migration in sql/migrations/*.sql; do
  [ -f "$migration" ] || continue
  echo "Applying $migration"
  docker-compose exec -T db psql -U "${POSTGRES_USER:-h3}" -d "${POSTGRES_DB:-h3project}" -v ON_ERROR_STOP=1 < "$migration"
done
echo "Docker environment is ready"

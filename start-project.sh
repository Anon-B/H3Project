#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=== H3Project START ==="
echo "Project: $PROJECT_DIR"

if ! command -v docker-compose >/dev/null 2>&1; then
  echo "ERROR: docker-compose not found"
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker is not running"
  echo "Please start Colima/Docker Desktop first."
  exit 1
fi

echo "[1/5] Starting DB, Redis, API, Frontend..."
docker-compose up -d --build

echo "[2/5] Waiting for services..."
for i in {1..30}; do
  if curl -fsS http://localhost:8000/health >/tmp/h3project-health.json 2>/dev/null; then
    break
  fi
  sleep 2
done

echo "[3/5] Applying database migrations..."
docker-compose exec -T api sh /app/scripts/migrate.sh

echo "[4/5] Checking API health..."
if ! curl -fsS http://localhost:8000/health; then
  echo
  echo "ERROR: API health check failed"
  docker-compose ps
  exit 1
fi

echo
echo "[5/5] Service status:"
docker-compose ps

echo
echo "=== H3Project READY ==="
echo "Frontend: http://localhost:8080"
echo "API:      http://localhost:8000"
echo "Health:   http://localhost:8000/health"

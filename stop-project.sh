#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=== H3Project STOP ==="
echo "Stopping DB, Redis, API, Frontend..."

if ! command -v docker-compose >/dev/null 2>&1; then
  echo "ERROR: docker-compose not found"
  exit 1
fi

docker-compose down

echo
echo "=== H3Project STOPPED ==="
echo "Docker volumes are preserved."
echo "Project data will remain available when started again."

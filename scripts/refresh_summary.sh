#!/bin/zsh
set -euo pipefail
cd /Users/anonpond/H3Project
docker-compose run --rm api python scripts/refresh_summary.py
docker-compose run --rm api python scripts/warm_redis.py

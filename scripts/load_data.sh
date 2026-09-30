#!/bin/zsh
set -euo pipefail
cd /Users/anonpond/H3Project
docker-compose run --rm api python scripts/load_data.py

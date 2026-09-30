#!/bin/zsh
set -euo pipefail
cd /Users/anonpond/H3Project
docker-compose up -d api frontend
echo "API: http://localhost:8000/docs"
echo "Map: http://localhost:8080"

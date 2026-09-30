#!/bin/zsh
set -euo pipefail
cd /Users/anonpond/H3Project
colima start --cpu 10 --memory 20 --disk 80 || true
docker context use colima
docker-compose up -d --build
echo "Docker environment is ready"

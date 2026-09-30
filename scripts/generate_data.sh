#!/bin/zsh
set -euo pipefail
cd /Users/anonpond/H3Project
N="${1:-1000000}"
.venv/bin/python scripts/generate_data.py --rows "$N" --output data/entities.csv

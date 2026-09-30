# H3Project

Spatial Data Platform POC: H3 + PostgreSQL/PostGIS + Redis + FastAPI + MapLibre.

## Start
```bash
cd /Users/anonpond/H3Project
colima start --cpu 10 --memory 20 --disk 80
docker-compose up -d --build
```

## URLs
- Map: http://localhost:8080
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Readiness: http://localhost:8000/ready
- Metrics: http://localhost:8000/metrics

## Data
Current validated POC dataset: 10,000,000 synthetic points.
```bash
docker-compose run --rm api python scripts/generate_data.py --rows 1000000 --output data/entities.csv
docker-compose run --rm api python scripts/load_data.py
docker-compose run --rm api python scripts/refresh_summary.py
docker-compose run --rm api python scripts/refresh_summary_res8.py
docker-compose run --rm api python scripts/warm_redis.py
```

## Verification
```bash
docker-compose exec -T api pytest -q
docker-compose exec -T api python scripts/data_quality.py
docker-compose exec -T api python scripts/correctness.py
docker-compose exec -T api python scripts/boundary_tests.py
```

## Benchmark
```bash
python3 benchmarks/benchmark_api.py
python3 benchmarks/concurrency.py
python3 benchmarks/matrix.py
```
Results are machine-specific; see `benchmarks/results/`.

## Docs
- `docs/USER_GUIDE.md` — usage and function guide
- `docs/DATA_DICTIONARY.md` — fields and governance rules
- `docs/OPERATIONS.md` — reliability, backup, security, observability
- `docs/ARCHITECTURE.md` — system design
- `IMPLEMENTATION_PLAN.md` — checklist/audit
- `docs/API_REFERENCE.md` — API parameters and examples

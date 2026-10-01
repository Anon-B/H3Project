# Benchmark Results

Baseline dataset: 1,000,000 synthetic spatial entities.

Metrics:
- P50/P95/P99 latency
- payload size
- concurrency at 10/50/100 users
- exact spatial correctness
- Redis summary cache

Results are machine-specific and are not production SLAs.

## v1.2 current architecture benchmark

`benchmarks/current_architecture.py` benchmarks the canonical `entity_part_h3` Boundary-H3 path using a synthetic 100,000-row temporary table. Latest Mac Mini run: P50 0.347 ms, P95 0.727 ms, P99 1.683 ms. These are local database micro-benchmark results, not production SLAs.

The older `scale_100k.py` expects the retired `spatial_entities` schema and is kept as historical benchmark material; use `current_architecture.py` for the current Boundary-H3 schema.

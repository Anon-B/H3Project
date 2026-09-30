# POC Plan — Historical / Benchmark Track

This document describes the original 1M/5M/10M synthetic-point benchmark track.
It is retained as historical evidence and is not the canonical GeoJSON application model.

## Historical flow
Synthetic points -> spatial_entities -> H3 summaries -> Redis -> spatial API -> GeoJSON.

## Historical phases
1. Generate 1M/5M/10M synthetic points.
2. Populate PostGIS geometry + H3 columns.
3. Build Res5/Res8 summaries.
4. Benchmark nearby/bbox and concurrency.
5. Validate exact PostGIS results.

## Current relationship
Current web ingestion uses datasets/entities/entity_parts/entity_part_h3.
Do not add new application features by copying the old spatial_entities schema.

## Retained benchmark assets
- benchmarks/
- scripts/generate_data.py
- scripts/load_data.py
- scripts/refresh_summary.py
- scripts/refresh_summary_res8.py
- scripts/data_quality.py
- scripts/correctness.py
- scripts/boundary_tests.py

## Migration opportunity
If benchmark coverage is still required, rewrite the benchmark scripts against the canonical entity model before calling them production verification.


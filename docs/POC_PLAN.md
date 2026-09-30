# POC Plan

## Phase 1
Generate 1M entities around Bangkok-like coordinates and assign H3 resolutions.

## Phase 2
Load PostGIS and create indexes:
- B-tree h3_res11
- B-tree h3_res8
- B-tree h3_res5 + is_active
- GiST geometry
- B-tree updated_at

## Phase 3
Build Gold summaries and warm Redis.

## Phase 4
Run API:
- /health
- /summary
- /nearby
- /bbox

## Phase 5
Benchmark:
- 1M baseline
- 5M scale
- 10M stress
- concurrent 10/50/100 clients

## Acceptance
- Exact spatial filter is correct at H3 boundaries.
- Empty coarse cells short-circuit.
- API returns valid GeoJSON.
- P95 is recorded for each query shape.
- No geometry smoothing is used for analytical truth.

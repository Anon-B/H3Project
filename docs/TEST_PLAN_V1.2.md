# H3Project Full Test Plan v1.2

## Scope

End-to-end verification of the H3 data platform: Docker services, PostgreSQL/PostGIS, Redis, API, GeoJSON ingestion, Boundary-H3 storage, display-H3 reconstruction, viewport loading, spatial queries, analytics, lifecycle/rollback/export, persistent background jobs, authentication/RBAC configuration, frontend production build, dependency security, and regression tests.

## Test case matrix

| ID | Area | Test | Expected |
|---|---|---|---|
| SYS-01 | Docker | DB/Redis/API/Frontend containers running | All services running |
| SYS-02 | API | `/health` | 200 + status ok |
| SYS-03 | API | `/ready` | 200 |
| SYS-04 | Observability | `/metrics/prometheus` | Prometheus metrics returned |
| API-01 | Catalog | list datasets | Dataset catalog returned |
| API-02 | Dataset | dataset detail | Metadata/schema returned |
| API-03 | Entity | entity detail + coverage | 200 |
| API-04 | Spatial | nearby query | GeoJSON FeatureCollection |
| API-05 | Spatial | bbox query | GeoJSON FeatureCollection |
| API-06 | Query | nearby/bbox generic query | Valid result |
| API-07 | Validation | invalid spatial type | 400 |
| ING-01 | Preview | Point | Accepted |
| ING-02 | Preview | LineString | Accepted |
| ING-03 | Preview | Polygon | Accepted |
| ING-04 | Preview | altitude coordinate | Accepted |
| ING-05 | Validation | invalid coordinate | 400 |
| ING-06 | Execute | GeoJSON ingestion | Run completed |
| ING-07 | H3 | Boundary H3 persisted | Cells persisted |
| ING-08 | Dedup | duplicate H3 rows | Unique constraint prevents duplicates |
| ING-09 | COPY | bulk H3 write path | PostgreSQL COPY used |
| ING-10 | Lifecycle | run status/finished_at | Completed lifecycle |
| ING-11 | Rollback | rollback run | Ingested data removed |
| ING-12 | Export | dataset GeoJSON export | 200 + export payload |
| JOB-01 | Background | async ingestion | 202 + job_id |
| JOB-02 | Persistence | job status from DB | Status survives process restart |
| JOB-03 | Recovery | queued/running recovery | Job resubmitted after API startup |
| MAP-01 | H3 API | dataset H3 | H3 list returned |
| MAP-02 | Viewport | bounded map query | Viewport result returned |
| MAP-03 | Reconstruction | boundary parts/display cells | Valid H3 output |
| ANA-01 | Analytics | H3 analytics | Aggregated H3 rows |
| SEC-01 | Auth | required-auth code path | Unauthenticated request rejected when enabled |
| SEC-02 | RBAC | roles/groups/realm_access | Roles recognized |
| SEC-03 | JWT | expiry/algorithm/audience/issuer | Hardened validation |
| SEC-04 | Rate limit | Redis-backed limiter | 429 after configured limit |
| DB-01 | Schema | lifecycle columns/indexes | Present |
| DB-02 | Integrity | job schema/indexes | Present |
| FE-01 | TypeScript | production build | Build succeeds |
| FE-02 | Performance | lazy GIS loading | GIS chunks separated from initial bundle |
| FE-03 | Security | npm production audit | 0 vulnerabilities |
| REG-01 | Regression | existing API tests | All pass |
| REG-02 | Full API | extended E2E tests | All pass |
| REG-03 | Docker | production compose smoke | All services healthy |

## Latest execution

Run commands:

```bash
API_BASE=http://localhost:8000 .venv/bin/pytest -q tests/test_api.py tests/test_full_api.py tests/test_security_and_integrity.py
cd frontend && npm run build && npm audit --omit=dev
```

Latest result: **22 automated tests passed**, frontend production build passed, and production dependency audit reported **0 vulnerabilities**.

The test suite intentionally separates host-side tests from Docker-internal tests so a failed hostname does not masquerade as an application failure.

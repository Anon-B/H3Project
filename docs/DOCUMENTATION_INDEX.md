# Documentation Index

เอกสารชุดนี้เป็น source of truth สำหรับผู้พัฒนาที่มารับช่วง H3Project.
ถ้าเอกสารเก่าขัดกับ code/schema ปัจจุบัน ให้ยึด code + schema + เอกสารชุดนี้ และแก้เอกสารที่ขัดทันที.

## Start here
| Document | ใช้เมื่อ |
|---|---|
| PROJECT_OVERVIEW.md | ต้องเข้าใจระบบทั้งก้อน |
| ARCHITECTURE.md | ต้องแก้ flow หรือ component |
| DATABASE_SPACE.md | อธิบาย Table ทั้งหมดและความเชื่อมโยง |
| DATA_MODEL.md | ต้องแก้ DB/storage |
| API_REFERENCE.md | ต้องเพิ่ม/แก้ endpoint |
| INGESTION_GEOJSON.md | ต้องแก้ ingestion |
| FRONTEND_MAP.md | ต้องแก้ Map/UI/rendering |
| DEVELOPER_GUIDE.md | ต้อง setup/build/test/deploy |
| TROUBLESHOOTING.md | ระบบมีปัญหา |
| OPERATIONS.md | backup/restore/runtime |
| DATABASE_MIGRATIONS.md | schema migration |
| DATA_DICTIONARY.md | field meaning |
| USER_GUIDE.md | end-user workflow |
| GIT_WORKFLOW.md | branch/commit |
| REVIEW_HARDENING_V1.3.md | hardening decisions and deferred scalability work |

## Current source of truth
- Backend: `app/main.py`
- Schema: `sql/schema.sql`
- Migrations: `sql/migrations/` (latest hardening: `005_v1_3_hardening.sql`)
- Frontend: `frontend/src/App.tsx`, `frontend/src/components/`, `frontend/src/lib/api.ts`, `styles.css`, `muiTheme.ts`
- Runtime: `docker-compose.yml`
- Tests: `tests/` และ `scripts/test_ingestion_api.py`

## Important terminology
- Canonical H3 = Boundary H3 ที่เก็บจริง
- Display H3 = cell ที่ frontend สร้างเพื่อแสดงผล
- Source resolution = resolution ที่ใช้ตอน ingest
- Display resolution = resolution ที่ผู้ใช้เลือกบน Map
- H3 = spatial index/representation; ไม่ใช่ exact geometry

## Documentation rule
ทุก feature ใหม่ต้องแก้เอกสารที่เกี่ยวข้องพร้อม code และระบุ migration/test ที่ต้องใช้.

# H3Project

**Release: v1.1.0**

Spatial Data Platform POC สำหรับ ingest และสำรวจข้อมูลเชิงพื้นที่ด้วย H3 + PostgreSQL/PostGIS + Redis + FastAPI + MapLibre + deck.gl

## อ่านเอกสารก่อนเริ่ม
1. `docs/DOCUMENTATION_INDEX.md` — จุดเริ่มต้นและแผนผังเอกสาร
2. `docs/PROJECT_OVERVIEW.md` — ภาพรวมระบบและสิ่งที่คนมารับช่วงต้องรู้
3. `docs/ARCHITECTURE.md` — architecture และ data flow
4. `docs/DATA_MODEL.md` — canonical data model
5. `docs/API_REFERENCE.md` — API ปัจจุบัน
6. `docs/DEVELOPER_GUIDE.md` — วิธีพัฒนา/build/test
7. `docs/USER_GUIDE.md` — วิธีใช้งานเว็บ
8. `docs/TROUBLESHOOTING.md` — ปัญหาที่พบบ่อย

## Current runtime
- Map: http://localhost:8080
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Readiness: http://localhost:8000/ready
- Metrics: http://localhost:8000/metrics
- Release: `v1.1.0`
- Branch: `feature/ingestion`

## Start
```bash
cd /Users/anonpond/H3Project
colima start --cpu 10 --memory 20 --disk 80
docker-compose up -d --build
docker-compose ps
curl http://localhost:8000/health
```

## Core rule
Boundary H3 ใน `entity_part_h3` คือ canonical spatial storage. ห้ามนำ `h3_features` กลับมาใช้.
Frontend รับ H3 IDs จาก API แล้ว reconstruct/fill display cells ด้วย h3-js; API ไม่ต้องส่ง polygon ของทุก display cell.

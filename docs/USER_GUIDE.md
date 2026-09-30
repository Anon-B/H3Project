# H3Project — คู่มือใช้งาน

## 1. ภาพรวม
POC นี้เป็น Spatial Data Platform สำหรับข้อมูลจุดจำนวนมาก โดยใช้ H3 เป็น broad-phase candidate index และ PostGIS เป็น exact spatial filter

Flow หลัก:
Raw CSV → H3 Res11/8/5 → PostgreSQL/PostGIS → Gold Summary → Redis → FastAPI → GeoJSON → MapLibre

## 2. เริ่มระบบ
```bash
cd /Users/anonpond/H3Project
colima start --cpu 10 --memory 20 --disk 80
docker-compose up -d --build
```
ตรวจสอบ:
```bash
docker-compose ps
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

## 3. หน้าใช้งาน
- Map: http://localhost:8080
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics

## 4. Data pipeline
สร้างข้อมูล:
```bash
docker-compose run --rm api python scripts/generate_data.py --rows 1000000 --output data/entities.csv
```
โหลดข้อมูลและสร้าง geometry/index:
```bash
docker-compose run --rm api python scripts/load_data.py
docker-compose exec -T db psql -U h3 -d h3project -f /app/sql/schema.sql
```
สร้าง Gold summary:
```bash
docker-compose run --rm api python scripts/refresh_summary.py
docker-compose run --rm api python scripts/refresh_summary_res8.py
```
Warm/clear Redis:
```bash
docker-compose run --rm api python scripts/warm_redis.py
docker-compose run --rm api python scripts/invalidate_cache.py
```

## 5. API
`GET /health` ตรวจ DB + จำนวน entity + Redis
`GET /ready` readiness ของระบบ; Redis ล่มจะรายงาน degraded
`GET /metrics` ขนาด DB/table/index และสถานะ Redis
`GET /summary?res=5|8&cache=true` คืน H3 Polygon summary เป็น GeoJSON
`GET /nearby?lat=&lng=&radius_m=&limit=&active_only=&mode=h3|db` ค้นหาจุดใกล้เคียง
`GET /bbox?min_lat=&min_lng=&max_lat=&max_lng=&limit=&active_only=` ค้นหาจุดในกรอบแผนที่

## 6. ความหมายของฟังก์ชัน
- `generate_data.py`: สร้าง synthetic lat/lng และ H3 3 ระดับ
- `load_data.py`: bulk load CSV และ populate geometry
- `incremental_upsert.py`: upsert ตาม id เหมาะกับ incremental batch และ soft delete
- `refresh_summary*.py`: สร้าง Gold aggregate Res5/Res8
- `warm_redis.py`: เติม cache summary
- `invalidate_cache.py`: ลบ cache เพื่อบังคับอ่าน DB ใหม่
- `data_quality.py`: ตรวจ range, geometry, H3, duplicate ID และ parent relationship
- `correctness.py`: เปรียบเทียบผล API กับ ST_DWithin
- `boundary_tests.py`: ทดสอบ boundary/cross-cell/empty/dense/large/small radius
- `benchmark_api.py`: P50/P95/P99/payload ของ endpoint
- `concurrency.py`: ทดสอบ 10/50/100 concurrent
- `matrix.py`: เปรียบเทียบ DB-only, H3+DB, Redis summary

## 7. หลักการ spatial query
1. แปลงจุดค้นหาเป็น H3 Res11
2. สร้าง candidate cells ด้วย grid disk
3. ใช้ H3 index ลดจำนวน candidate
4. ใช้ PostGIS `ST_DWithin` ตรวจระยะจริง
5. คืนผลเป็น GeoJSON

ดังนั้น H3 ไม่ได้แทน exact spatial predicate และไม่ควรใช้ H3 เพียงอย่างเดียวในการตัดสินระยะทาง

## 8. Web Ingestion Pipeline — GeoJSON
รายละเอียดเต็มอยู่ที่ `docs/INGESTION_GEOJSON.md`.
เปิด `http://localhost:8080` → Ingestion → เลือก/วาง GeoJSON → Preview H3 → เลือก Res11/Res8/Res5 → Run Pipeline หรือ Download H3 GeoJSON.

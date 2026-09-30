# GeoJSON Ingestion Pipeline — Web Guide

## Goal
หน้าเว็บสำหรับพัฒนา/ทดสอบ pipeline จาก GeoJSON → H3 Res11 / Res8 / Res5 ก่อนนำ logic ไปต่อกับ Polygon/Raster ingestion

## เปิดใช้งาน
```bash
cd /Users/anonpond/H3Project
docker-compose up -d --build
```
เปิด `http://localhost:8080`

## วิธีใช้งาน
1. เลือกไฟล์ `.geojson/.json` หรือวาง GeoJSON ในช่องข้อความ
2. กด **Load Sample** เพื่อทดลอง Point + Polygon
3. กด **Preview H3** เพื่อคำนวณโดยยังไม่เขียน DB
4. เลือก Res11 / Res8 / Res5 เพื่อดู grid บนแผนที่
5. กด **Run Pipeline** เพื่อบันทึก ingestion run และ H3 cells ลง PostgreSQL
6. กด **Download H3 GeoJSON** เพื่อ export grid ของ resolution ที่เลือก

## GeoJSON ที่รองรับ
- `FeatureCollection`
- `Feature`
- Geometry เดี่ยว: `Point`, `MultiPoint`, `Polygon`, `MultiPolygon`, `GeometryCollection`

### Point
Point จะถูก map เป็น H3 cell เดียวในแต่ละ resolution:
`lat/lng → Res11 → parent Res8 → parent Res5`

### Polygon / MultiPolygon
ใช้ H3 polyfill เพื่อสร้างทุก H3 cell ที่อยู่ภายใน geometry สำหรับแต่ละ resolution

> Res11 สามารถสร้างจำนวน cell มากเมื่อ polygon ใหญ่ จึงควร Preview ก่อน Run และใน production ควรมี cell-count guard / asynchronous job

## API
### Preview
`POST /ingestion/geojson/preview`

รับ GeoJSON โดยตรงและคืน:
- feature_count
- cell_counts
- unique_cells
- H3 list ต่อ feature

Preview **ไม่เขียน DB**

### Execute
`POST /ingestion/geojson/execute`

ทำเหมือน Preview แล้วบันทึก:
- `ingestion_runs`
- `ingestion_h3_cells`

คืน `run_id` และจำนวน H3 ที่สร้าง

### Runs
`GET /ingestion/runs`

ดูประวัติ ingestion run

`GET /ingestion/runs/{run_id}`

ดูรายละเอียด run และจำนวน cell แยก Res5/8/11

## ตารางที่ใช้
`ingestion_runs` เป็น metadata ของ pipeline run  
`ingestion_h3_cells` เป็น normalized H3 output: 1 row ต่อ feature × resolution × H3 cell

ตาราง ingestion แยกจาก `spatial_entities` เพื่อให้ทดลอง pipeline ได้โดยไม่กระทบ dataset production POC 10M

## Output semantics
- Res11 = object/high-detail index
- Res8 = medium aggregation
- Res5 = coarse aggregation
- H3 เป็น index/grid ไม่ใช่ exact polygon boundary
- Polygon H3 output เป็น analytical tessellation และไม่ควรนำไปตีความว่าเป็นขอบเขตจริงของ polygon

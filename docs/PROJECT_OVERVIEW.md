# Project Overview

## 1. Purpose
H3Project เป็น Spatial Data Platform POC สำหรับรับ GeoJSON/Draw, แปลง geometry เป็น H3, เก็บ canonical Boundary H3, วิเคราะห์ และแสดงผลบนแผนที่.

## 2. Current architecture
```text
GeoJSON / Draw
   -> FastAPI ingestion
   -> datasets / entities / entity_parts / entity_attributes
   -> entity_part_h3 (Boundary H3)
   -> /ingestion/dataset/h3
   -> Frontend reconstruct display H3
   -> deck.gl H3HexagonLayer + MapLibre
```

PostgreSQL/PostGIS เป็น persistent source of truth. Redis เป็น cache/optimization.

## 3. Current UI
- Map: สำรวจ dataset, H3 display resolution, layers, analytics, query, basemap, Style & 3D.
- Overview: KPI และ recent datasets.
- Datasets: registry, detail, metadata/catalog, edit/delete.
- Ingestion: File/GeoJSON หรือ Draw -> Preview -> Execute.
- Analysis: metric และ H3 analytics ของ dataset ที่ active.
- Settings: runtime และ map defaults.

## 4. H3 resolution
- Res 5: city/province/coarse view (~8.8 km)
- Res 8: neighborhood/subdistrict (~700 m)
- Res 11: fine/object analysis (~40 m)
- Res 12-15: detail เมื่อข้อมูลและจำนวน cell เหมาะสม

Resolution ของ dataset และ resolution ที่แสดงบน Map เป็นคนละเรื่อง.
Dataset source resolution ถูกกำหนดตอน ingest; display resolution เปลี่ยนได้ภายหลัง.

## 5. Canonical storage
Polygon/MultiPolygon ไม่เก็บ original geometry ใน canonical model.
เก็บเฉพาะ Boundary H3 และ ring metadata (outer/hole).
Point เก็บ lat/lng + H3; Line เก็บ H3 coverage ตามแนวเส้น.
Entity properties เก็บใน entity_attributes.properties.

## 6. Frontend display
API `/ingestion/dataset/h3` ส่ง H3 IDs + part/ring metadata + entity attributes.
Frontend ใช้ h3-js reconstruct/fill interior cells ตาม display resolution.
ดังนั้น API ไม่ควรสร้างและส่ง polygon GeoJSON จำนวนมหาศาลสำหรับทุก display cell.

## 7. Important current behavior
- Inspector แสดง JSON เท่านั้น.
- Click H3 จะคืน object ที่ flatten แล้ว เช่น `{hex, entity_id, A}`.
- Map analytics ปัจจุบันมี No metric และ Entity count.
- Style & 3D รองรับ color preset/custom, opacity, extrusion และ height.
- Basemap เปลี่ยนได้โดยไม่ต้อง reload.

## 8. Known boundary
ระบบปัจจุบันมี legacy benchmark/data scripts ที่อ้าง schema รุ่นเก่า `spatial_entities`.
อย่าใช้ legacy scripts เพื่อสรุปว่า current ingestion model ต้องมี spatial_entities.
Current GeoJSON application path ใช้ canonical entity model ตาม `sql/schema.sql`.

## 9. Production backlog
Real source/CDC ingestion, incremental canonical ingestion, formal AuthN/AuthZ, centralized observability, CI/CD hardening, Kubernetes/cloud sizing, large-scale stress test และ production backup/restore drill ยังเป็นงานต่อ.


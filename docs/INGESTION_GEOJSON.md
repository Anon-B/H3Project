# Ingestion Pipeline — GeoJSON / Draw

## เป้าหมาย

หน้าเว็บรองรับ 2 แหล่งข้อมูล:

- File / GeoJSON
- Draw บนแผนที่

ทั้งสองทางเข้ากระบวนการเดียวกัน:

```
Source
  ↓
GeoJSON FeatureCollection
  ↓
Preview H3
  ↓
Execute Pipeline
  ↓
Entity + Entity Part + Boundary H3
  ↓
H3 Analytics
```

## Draw บนแผนที่

หน้า **Ingestion → Draw** ใช้ `maplibre-gl-draw` กับ MapLibre โดยตรง

เครื่องมือที่มี:

- **Point** — คลิกตำแหน่ง
- **Line** — คลิกจุดตามแนวเส้น แล้ว double-click เพื่อจบ
- **Polygon** — คลิกจุดรอบพื้นที่ แล้ว double-click เพื่อจบ
- **Select / Move** — เลือกและย้าย feature
- **Edit Vertices** — แก้ไข vertex ของ feature ที่เลือก
- **Use Drawing** — sync drawing ปัจจุบันเข้า Pipeline
- **Clear** — ลบ drawing ทั้งหมด

เมื่อวาดเสร็จ ระบบรับ `draw.create`, `draw.update` และ `draw.delete` แล้ว sync เข้า `ingData` อัตโนมัติ ดังนั้น Preview และ Execute ใช้ข้อมูลที่วาดจริง

## Preview H3

กด **Preview H3**

ระบบเรียก:

`POST /ingestion/geojson/preview?resolution=<5..15>`

Preview ไม่เขียน Entity ลงฐานข้อมูล

ใช้ตรวจ:

- จำนวน Feature
- จำนวน Boundary H3
- จำนวน display H3
- geometry ที่แปลงสำเร็จ/ผิดพลาด

## Execute Pipeline

กด **Execute Pipeline**

ระบบเรียก:

`POST /ingestion/geojson/execute?resolution=<5..15>&dataset=<name>`

และสร้าง:

- `datasets`
- `entities`
- `entity_parts`
- `entity_part_h3`
- `h3_features`
- `ingestion_runs`
- `ingestion_parts`
- `ingestion_h3_cells`

## รูปแบบการเก็บ

Polygon:

```
Polygon
  ↓
Boundary H3
  ├── outer
  └── hole
```

MultiPolygon:

```
Feature
  ├── Part 0 → Boundary H3
  └── Part 1 → Boundary H3
```

Point:

- เก็บ latitude / longitude
- เก็บ H3 cell

Line:

- เก็บ H3 coverage ตามแนวเส้น

Original Polygon geometry ไม่ถูกเก็บใน canonical storage

## H3 Analytics

ข้อมูลที่ derive เพิ่มใน `h3_features`:

- `h3_index`
- `resolution`
- `feature_type`
- `cell_coverage`
- `polygon_coverage`
- `centroid_cell`
- `pixel_coverage`
- `properties`

API:

`GET /analytics/h3?dataset=<name>&resolution=<5..15>`

ใช้สำหรับ aggregation และ Map analytics

## Map

หลัง Execute สามารถ:

1. ไปที่ **Datasets**
2. เปิด Dataset
3. กด **Map**

แล้วเลือก:

- H3 Display Resolution
- Data Colors
- Entity / H3 layer
- Analytics metric
- 3D Extrude
- Height

## ข้อควรระวัง

Res สูงกับ polygon ใหญ่สามารถสร้าง H3 จำนวนมาก ควร Preview ก่อน Execute

H3 Boundary เป็น spatial representation ที่ใช้ลด storage และสำหรับ analytics ไม่ใช่สำเนา polygon เดิมแบบ lossless

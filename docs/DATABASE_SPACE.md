# Database Space — Tables & Relationships

## 1. ภาพรวม
Database ใช้ PostgreSQL + PostGIS เป็น Persistent Source of Truth สำหรับ Dataset, Entity, Spatial Parts และ Boundary H3

```text
datasets
   │
   ├────────── raster_datasets
   ├────────── entities
   │              ├── entity_attributes
   │              ├── entity_point
   │              └── entity_parts ─── entity_part_h3 ─── entity_h3 (VIEW)
   └────────── ingestion_runs ─── ingestion_parts / ingestion_h3_cells
```

หัวใจของ Spatial Data ปัจจุบันคือ datasets → entities → entity_parts → entity_part_h3
entity_part_h3 คือ Canonical Boundary H3 Storage

## 2. datasets — Dataset Registry
ตารางแม่ของข้อมูลแต่ละชุด เก็บชื่อ Dataset, ประเภทข้อมูล, Source H3 Resolution, metadata, source, owner, version, tags, license, schema และ lineage

Relationship: datasets 1:N entities, 1:1 raster_datasets, 1:N ingestion_runs

## 3. entities — Entity Registry
Object หลักภายใน Dataset มี entity_id และ dataset_id

Relationship:
```text
datasets 1 ─── N entities
```
Entity เป็นตัวกลางระหว่าง Dataset กับข้อมูลเชิงพื้นที่

## 4. entity_attributes — Entity Properties
เก็บ Source Feature.properties ใน JSONB เช่น {name, type, code}

Relationship: entities 1:1 entity_attributes
ใช้สำหรับ Attribute Query และ Inspector ไม่จำเป็นต้องสร้าง column ใหม่ทุกครั้งที่ Source มี field เพิ่ม

## 5. entity_parts — Spatial Parts
Entity หนึ่งตัวสามารถมีหลาย Spatial Parts รองรับ Point, Line, Polygon และ Multi geometry ที่แตกเป็นหลาย parts

Fields สำคัญ: part_id, entity_id, part_index, part_type, bbox, properties, metadata

Relationship:
```text
entities 1 ─── N entity_parts
```

## 6. entity_point — Point Coordinates
เก็บ latitude/longitude จริงสำหรับ Point Entity
Relationship: entities 1:0..1 entity_point

## 7. entity_part_h3 — Canonical Boundary H3
ตารางสำคัญที่สุดของ Spatial Model ปัจจุบัน เก็บ H3 ที่เกิดจากแต่ละ Spatial Part

Fields: part_id, resolution, ring_id, ring_type, h3_index

Relationship:
```text
entity_parts 1 ─── N entity_part_h3
```

ring_type:
| ค่า | ความหมาย |
|---|---|
| none | Point / geometry ที่ไม่มี ring |
| outer | Boundary ด้านนอก Polygon |
| hole | Boundary ของรูภายใน Polygon |
| line | H3 coverage ของ Line |

ตัวอย่าง Polygon:
```text
Entity 15 → Part 0 → outer H3 A/B/C + hole H3 X/Y
```

สำคัญ: ระบบไม่เก็บ Display H3 ทุก cell เป็น Canonical Data แต่เก็บ Boundary H3 แล้วให้ Frontend reconstruct ตาม Display Resolution

## 8. entity_h3 — View
เป็น Database View ที่ join entity_part_h3 กับ entity_parts แล้ว expose entity_id, resolution และ h3_index

ถ้าต้องแก้ Spatial Storage ให้แก้ entity_part_h3 เป็นหลัก ไม่ใช่ View

## 9. raster_datasets
เก็บ metadata ของ Raster เช่น file URI, bounding box, format, size และ metadata
Relationship: datasets 1:1 raster_datasets
เป็นส่วนรองรับ Raster ในอนาคต ไม่ใช่เส้นทางหลักของ GeoJSON ปัจจุบัน

## 10. Ingestion History
### ingestion_runs
แทนการ Execute หนึ่งครั้ง เช่น dataset, input feature count, output cell count และ status
Relationship: datasets 1:N ingestion_runs

### ingestion_parts
เก็บรายละเอียด Feature/Part ที่เกิดจาก Ingestion Run
Relationship: ingestion_runs 1:N ingestion_parts

### ingestion_h3_cells
เก็บ H3 ที่เกิดขึ้นระหว่าง Ingestion Run เพื่อ audit/history
เป็น Audit/History ไม่ใช่ Canonical Map Data
Canonical Map Data อยู่ที่ entity_part_h3

## 11. Complete Relationship
```text
                         datasets
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
          entities    raster_datasets  ingestion_runs
              │                           │
       ┌──────┼──────┐                    ├── ingestion_parts
       │      │      │                    └── ingestion_h3_cells
       ▼      ▼      ▼
entity_attributes entity_point entity_parts
                                  │
                                  ▼
                           entity_part_h3
                                  │
                                  ▼
                             entity_h3 VIEW
```

## 12. GeoJSON Data Flow
```text
GeoJSON / Draw
      ↓
  Ingestion API
      ↓
  datasets
      ↓
  entities ─── entity_attributes
      ↓
  entity_parts ─── entity_point (Point)
      ↓
  entity_part_h3
      ↓
  Boundary H3
```
พร้อม Audit:
```text
ingestion_runs → ingestion_parts → ingestion_h3_cells
```

## 13. Database → API → Frontend
```text
PostgreSQL entity_part_h3
          ↓
GET /ingestion/dataset/h3
          ↓
Boundary H3 + ring metadata
          ↓
Frontend reconstruct
          ↓
Display H3
          ↓
deck.gl H3HexagonLayer
          ↓
Map
```
ดังนั้น Database ไม่ได้เก็บทุก H3 cell ที่ผู้ใช้เห็นบนหน้าจอ

## 14. Delete / Cascade
Dataset deletion cascade ไปยัง entities และข้อมูลลูกตาม Foreign Key ที่กำหนด ส่วน ingestion history ใช้ความสัมพันธ์ของ ingestion_runs และลูกของมัน

## 15. Developer Rules
- ใช้ datasets เป็น Dataset registry
- ใช้ entities เป็น Entity registry
- ใช้ entity_attributes สำหรับ Entity properties
- ใช้ entity_parts สำหรับ Spatial parts
- ใช้ entity_part_h3 เป็น Canonical H3
- ใช้ ingestion_* สำหรับ audit/history
- เพิ่ม migration เมื่อเปลี่ยน schema ที่มีอยู่แล้ว
- ห้ามสร้าง h3_features กลับมา
- ห้ามเก็บ Display H3 ทุก cell เป็น Canonical table
- ห้ามใช้ ingestion_h3_cells แทน entity_part_h3
- ห้ามถือว่า Boundary H3 เป็น Original Polygon Geometry
- ห้ามเปลี่ยน Dataset source resolution โดยไม่ rebuild/re-ingest

## 16. Quick Reference
| Table/View | หน้าที่ | ความสัมพันธ์หลัก |
|---|---|---|
| datasets | Dataset registry | Parent |
| entities | Entity ใน Dataset | dataset → entities |
| entity_attributes | Entity properties | entity 1:1 |
| entity_parts | Spatial parts | entity 1:N |
| entity_point | Point coordinates | entity 1:0..1 |
| entity_part_h3 | **Canonical Boundary H3** | part 1:N |
| entity_h3 | H3 query View | derived from entity_part_h3 |
| raster_datasets | Raster metadata | dataset 1:1 |
| ingestion_runs | Ingestion execution | dataset 1:N |
| ingestion_parts | Ingestion part audit | run 1:N |
| ingestion_h3_cells | Ingestion H3 audit | run 1:N |

## 17. Mental Model
Dataset มี Entity → Entity มี Spatial Part → Spatial Part มี Boundary H3 → Frontend ใช้ Boundary H3 สร้าง Display H3

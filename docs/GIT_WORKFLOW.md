# Git Workflow — H3Project
เอกสาร workflow สำหรับพัฒนา H3Project ด้วย Git

> **กฎสำคัญของโปรเจกต์:** ทำงานคนเดียว และงานพัฒนา/แก้ไขโค้ดทุกอย่างต้องเริ่มและทำบน `feature/*` ก่อนเสมอ ห้ามพัฒนาโดยตรงบน `develop` หรือ `main`

## 1. Branch หลัก

- `main` — เวอร์ชัน stable / production
- `develop` — รวมงาน development และ integration/test
- `feature/*` — งานพัฒนาและ feature ทั้งหมด
- `experiment` — งานทดลอง / benchmark / POC ที่ยังไม่พร้อมเข้า develop
- `release/*` — ใช้เฉพาะเมื่อเตรียม release version สำคัญ
- `fix/*` — ใช้เมื่อจำเป็นต้องแยก bug fix จาก develop
- `hotfix/*` — ใช้เฉพาะปัญหาเร่งด่วนบน main

## 2. Workflow ที่ใช้จริง

สำหรับการทำงานคนเดียว ใช้ workflow หลักแบบง่าย:

```text
feature/*
    ↓
develop
    ↓
main
```

เมื่อเตรียม release version สำคัญ สามารถเพิ่ม:

```text
feature/*
    ↓
develop
    ↓
release/vX.Y.Z
    ↓
main
```

### หลักการ

1. **เขียนโค้ด / เพิ่ม feature / แก้ไขงาน → ทำบน `feature/*`**
2. **รวมงานและทดสอบ integration → `develop`**
3. **พร้อมใช้งานจริง → `main`**
4. **งานทดลองที่ยังไม่แน่ใจ → `experiment`**
5. **release branch ไม่ต้องสร้างทุกครั้ง ใช้เมื่อมีเหตุผลด้าน release**
6. หลัง merge แล้วสามารถลบ feature branch ได้ แต่ branch หลักของโปรเจกต์ยังคงใช้ตามหน้าที่เดิม

## 3. Feature Branch ที่ใช้ใน H3Project

ใช้เฉพาะ Feature branch ระดับหลัก ไม่แตก branch ย่อยตามฟังก์ชัน:

- `feature/api`
- `feature/database`
- `feature/h3`
- `feature/ingestion`
- `feature/map`

ตัวอย่าง: GeoJSON, drawing, bbox หรือ Redis ให้ทำภายใต้ Feature ที่เกี่ยวข้อง

**ห้ามสร้าง feature branch ย่อย** เช่น `feature/ingestion-geojson`

## 4. วิธีเริ่มงานใหม่

เลือก Feature ที่เกี่ยวข้อง แล้วทำงานบน branch นั้น:

```bash
git switch develop
git pull origin develop
git switch feature/<ชื่อ-feature>
```

ถ้า Feature branch ยังไม่มี ให้สร้างจาก develop:

```bash
git switch develop
git pull origin develop
git switch -c feature/<ชื่อ-feature>
```

> **สำคัญ:** หลังจาก switch เข้า `feature/*` แล้ว การแก้ไขทั้งหมดของงานนั้นให้ทำบน Feature branch เท่านั้น

## 5. Commit และ Push

```bash
git status
git add .
git commit -m "feat: <รายละเอียด>"
git push -u origin feature/<ชื่อ-feature>
```

จากนั้น merge เข้า `develop` หลังทดสอบงานเรียบร้อย

## 6. ตัวอย่าง

### GeoJSON Ingestion

ใช้:

```bash
git switch feature/ingestion
```

ทำ GeoJSON, Polygon, Dataset หรือ ingestion function ทั้งหมดใน branch นี้

ไม่สร้าง branch แยกตามฟังก์ชัน

### Map

ใช้:

```bash
git switch feature/map
```

งาน drawing, layer toggle, map query และ map UI ทำใน branch นี้

### API

ใช้:

```bash
git switch feature/api
```

งาน endpoint และ API behavior ทำใน branch นี้

## 7. Bug Fix

ถ้าเป็น bug ของงานที่กำลังพัฒนา ให้แก้ใน Feature branch ที่เกี่ยวข้องก่อน

ตัวอย่าง:

```bash
git switch feature/ingestion
```

ถ้าเป็น bug ที่ไม่สามารถผูกกับ Feature หลักได้จริง ค่อยสร้าง `fix/*` จาก `develop`

```text
fix/* → develop
```

## 8. Develop

`develop` มีหน้าที่เป็น **integration/testing branch**

ห้ามใช้ `develop` เป็นพื้นที่พัฒนาโดยตรง

Flow:

```text
feature/*
     ↓
   merge
     ↓
 develop
     ↓
integration test
```

## 9. Main

`main` คือ stable / production

ห้ามพัฒนาโดยตรงบน `main`

Flow ปกติ:

```text
feature/*
    ↓
develop
    ↓
main
```

## 10. Release

ไม่จำเป็นต้องสร้าง `release/*` ทุกครั้ง

ใช้เมื่อมีการเตรียม version สำคัญ:

```text
develop
    ↓
release/v1.1.0
    ↓
main
```

ก่อน release ให้ตรวจสอบ:

- API
- Frontend
- Database
- Docker
- Tests
- Documentation

หลัง release ให้สร้าง tag:

```bash
git switch main
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin main
git push origin v1.1.0
```

## 11. Experiment

มี branch ทดลองเพียงตัวเดียว:

```text
experiment
```

ใช้สำหรับ:

- benchmark
- query tuning
- Redis test
- H3 performance
- 50M / 100M scale test
- POC ที่ยังไม่พร้อมเข้า develop

ไม่ต้องสร้าง experiment branch เพิ่มสำหรับแต่ละการทดลอง

## 12. Commit Convention

- `feat:` เพิ่ม feature
- `fix:` แก้ bug
- `docs:` แก้เอกสาร
- `refactor:` ปรับโครงสร้าง code
- `test:` เพิ่มหรือแก้ test
- `chore:` maintenance / config

ตัวอย่าง:

```text
feat: add GeoJSON ingestion
fix: correct H3 resolution validation
docs: update Git workflow
test: add nearby API test
chore: update docker configuration
```

## 13. สิ่งที่ไม่ควร Commit

ห้าม commit:

- `.env` และ secret/token
- Database dump ขนาดใหญ่
- generated data
- log
- local cache
- credentials

โปรเจกต์นี้มี:

```gitignore
backups/*.dump
```

เพื่อป้องกัน database dump เข้า Git

## 14. ตรวจสอบก่อน Commit

```bash
git status
git diff
git diff --cached
```

หลัง commit:

```bash
git log --oneline -5
git status
```

## 15. Sync Feature กับ Develop

ถ้า Feature ทำงานนานและ `develop` มีการเปลี่ยนแปลง:

```bash
git switch develop
git pull origin develop
git switch feature/<ชื่อ-feature>
git merge develop
```

แก้ conflict ถ้ามี แล้ว test ใหม่ก่อน push

## 16. ลบ Feature Branch หลัง Merge

เมื่อ Feature merge เข้า `develop` แล้ว:

```bash
git branch -d feature/<ชื่อ-feature>
git push origin --delete feature/<ชื่อ-feature>
```

## 17. GitHub Remote

Repository:

`https://github.com/Anon-B/H3Project.git`

ตรวจสอบ:

```bash
git remote -v
git branch -a
```

## 18. Workflow สั้น ๆ ที่ต้องจำ

```text
งานใหม่
   ↓
feature/*
   ↓
test
   ↓
merge
   ↓
develop
   ↓
integration test
   ↓
main
```

Release สำคัญ:

```text
develop → release/vX.Y.Z → main
```

Experiment:

```text
experiment
```

## 19. Project Rule / Note

> **H3Project เป็นโปรเจกต์ที่ทำงานคนเดียว ดังนั้นให้ใช้ Git workflow แบบเรียบง่าย**
>
> **ทุกการพัฒนา การเพิ่ม function การแก้ไข code และ bug fix ต้องทำบน `feature/*` ก่อน**
>
> `develop` ใช้สำหรับรวมงานและทดสอบ  
> `main` ใช้สำหรับ stable / production  
> `release/*` ใช้เฉพาะตอนเตรียม release สำคัญ  
> `experiment` ใช้สำหรับงานทดลอง
>
> **ห้ามพัฒนาโดยตรงบน `develop` หรือ `main`**

Repository:
`https://github.com/Anon-B/H3Project.git`

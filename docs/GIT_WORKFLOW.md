# Git Workflow — H3Project
เอกสาร workflow สำหรับพัฒนา H3Project ด้วย Git

## 1. Branch หลัก
- `main` — เวอร์ชัน stable / release
- `develop` — branch รวมงาน development
- `feature/*` — feature หลักของระบบ
- `fix/*` — แก้ bug ทั่วไป
- `hotfix/*` — แก้ปัญหาเร่งด่วนบน main
- `experiment` — งานทดลอง / benchmark / performance / scale
- `release/*` — เตรียม release ก่อนเข้า main

## 2. โครงสร้าง Branch ปัจจุบัน
```
main
├── release/v1.0.0
├── develop
│   ├── feature/api
│   ├── feature/database
│   ├── feature/h3
│   ├── feature/ingestion
│   └── feature/map
└── experiment
```

ใช้ Feature branch เฉพาะระดับหลัก ไม่แตก branch ย่อยตามฟังก์ชันย่อย
เช่น GeoJSON, drawing, bbox หรือ Redis ให้ทำภายใต้ Feature ที่เกี่ยวข้อง

## 3. Branch ที่มีอยู่จริง
- `main`
- `develop`
- `release/v1.0.0`
- `experiment`
- `feature/api`
- `feature/database`
- `feature/h3`
- `feature/ingestion`
- `feature/map`

ไม่ใช้ `experiment-performance` หรือ `experiment-scale-100m`

## 4. Workflow ทำ Feature
เริ่มจาก `develop`

```bash
git switch develop
git pull origin develop
git switch -c feature/<ชื่อ-feature>
```

ทำงานแล้ว commit และ push:

```bash
git status
git add .
git commit -m "feat: <รายละเอียด>"
git push -u origin feature/<ชื่อ-feature>
```

จากนั้นเปิด Pull Request:
`feature/<ชื่อ-feature> → develop`

เมื่อ review และ test ผ่าน จึง merge เข้า `develop`

## 5. ตัวอย่าง Feature
สำหรับงาน GeoJSON ingestion ให้ใช้ `feature/ingestion` ไม่สร้าง `feature/ingestion-geojson`

```bash
git switch develop
git pull origin develop
git switch feature/ingestion
```

หรือสร้าง branch ใหม่จาก develop เมื่อเริ่มงาน:

```bash
git switch develop
git switch -c feature/ingestion
```

## 6. Bug Fix
Bug ทั่วไปให้แตกจาก `develop`

```bash
git switch develop
git pull origin develop
git switch -c fix/<ชื่อ-bug>
git add .
git commit -m "fix: <รายละเอียด>"
git push -u origin fix/<ชื่อ-bug>
```

แล้วเปิด PR เข้า `develop`

## 7. Release Workflow
เมื่อ `develop` พร้อม release:

```bash
git switch develop
git pull origin develop
git switch -c release/v1.0.0
```

ตรวจสอบ API, Frontend, Database, Docker, Tests และ Documentation

จากนั้น:

```text
release/v1.0.0 → main
release/v1.0.0 → develop
```

สร้าง tag บน main:

```bash
git switch main
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin main
git push origin v1.0.0
```

## 8. Hotfix
ใช้เมื่อมีปัญหาเร่งด่วนบน `main`

```bash
git switch main
git pull origin main
git switch -c hotfix/<ชื่อ-bug>
git add .
git commit -m "fix: <รายละเอียด>"
git push -u origin hotfix/<ชื่อ-bug>
```

หลังแก้และทดสอบแล้ว merge เข้า `main` และ `develop`

## 9. Experiment
มี branch ทดลองเพียงตัวเดียวคือ `experiment`

ใช้สำหรับ:
- benchmark
- query tuning
- Redis test
- H3 performance
- 50M / 100M scale test
- POC ที่ยังไม่พร้อมเข้า develop

ตัวอย่าง:

```bash
git switch experiment
```

การทดลองหลายเรื่องให้แยกด้วย commit ไม่ต้องสร้าง branch ใหม่ เช่น:

```text
experiment: benchmark nearby query
experiment: test 100m dataset
experiment: optimize h3 lookup
```

## 10. Commit Convention
- `feat:` เพิ่ม feature
- `fix:` แก้ bug
- `docs:` แก้เอกสาร
- `refactor:` ปรับโครงสร้าง code
- `test:` เพิ่มหรือแก้ test
- `chore:` งาน maintenance / config

ตัวอย่าง:

```text
feat: add GeoJSON ingestion
fix: correct H3 resolution validation
docs: update Git workflow
test: add nearby API test
chore: update docker configuration
```

## 11. สิ่งที่ไม่ควร Commit
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

## 12. ตรวจสอบก่อน Commit

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

## 13. Sync Branch
ถ้า Feature ทำงานนานและ `develop` มีการเปลี่ยนแปลง:

```bash
git switch develop
git pull origin develop
git switch feature/<ชื่อ-feature>
git merge develop
```

แก้ conflict ถ้ามี แล้ว test ใหม่ก่อน push

## 14. ลบ Branch หลัง Merge
เมื่อ Feature merge เข้า `develop` แล้ว สามารถลบ branch ได้:

```bash
git branch -d feature/<ชื่อ-feature>
git push origin --delete feature/<ชื่อ-feature>
```

ไม่จำเป็นต้องลบ `experiment` หากต้องการเก็บผลการทดลอง

## 15. GitHub Remote
Repository:
`https://github.com/Anon-B/H3Project.git`

ตรวจสอบ remote:

```bash
git remote -v
git branch -a
```

## 16. Workflow สั้น ๆ
งานใหม่:

```text
feature/* → Pull Request → develop
                         ↓
                    test / review
                         ↓
                  release/vX.Y.Z
                         ↓
                       main
                         ↓
                     tag vX.Y.Z
```

Bug:
```text
fix/* → develop
```

ปัญหาเร่งด่วน:
```text
hotfix/* → main + develop
```

ทดลอง:
```text
experiment
```

# Git Workflow — H3Project
เอกสาร workflow สำหรับพัฒนา H3Project ด้วย Git

## 1. Branch หลัก
- `main` — เวอร์ชัน stable / release
- `develop` — branch รวมงานสำหรับ development
- `feature/*` — งาน feature ใหม่
- `fix/*` — แก้ bug ทั่วไป
- `hotfix/*` — แก้ปัญหาเร่งด่วนบน main
- `experiment-*` — งานทดลอง / performance / scale test
- `release/*` — เตรียม release ก่อน merge เข้า main

## 2. โครงสร้าง Branch ปัจจุบัน
```
main
└── develop
    ├── feature/ingestion
    │   ├── feature/ingestion-geojson
    │   ├── feature/ingestion-dataset
    │   └── feature/ingestion-drawing
    ├── feature/map
    │   ├── feature/map-query
    │   ├── feature/map-layer-toggle
    │   └── feature/map-drawing
    ├── feature/h3
    │   ├── feature/h3-resolution
    │   └── feature/h3-polyfill
    ├── feature/api
    │   ├── feature/api-nearby
    │   └── feature/api-bbox
    ├── feature/database
    │   ├── feature/postgis
    │   └── feature/redis
    └── experiment-*
```
## 3. หมายเหตุเรื่องชื่อ Branch
Git ไม่สามารถมี branch `experiment` พร้อมกับ
`experiment/performance` ได้พร้อมกัน เพราะใช้ namespace เดียวกัน

ดังนั้นในโปรเจกต์นี้ใช้ชื่อจริง:
- `experiment-performance`
- `experiment-scale-100m`

## 4. Workflow ทำ Feature
เริ่มจาก `develop`

```bash
git switch develop
git pull origin develop
git switch -c feature/<ชื่อ-feature>

# ทำงาน / แก้ไฟล์
git status
git add .
git commit -m "feat: <รายละเอียด>"

git push -u origin feature/<ชื่อ-feature>
```

จากนั้นเปิด Pull Request:
`feature/<ชื่อ-feature> → develop`

เมื่อ review และ test ผ่าน จึง merge เข้า `develop`

## 5. ตัวอย่าง
```bash
git switch develop
git pull origin develop
git switch -c feature/ingestion-geojson

git add app/main.py docs/INGESTION_GEOJSON.md
git commit -m "feat: add GeoJSON H3 ingestion"
git push -u origin feature/ingestion-geojson
```
## 6. Bug Fix
Bug ทั่วไปให้แตกจาก `develop`

```bash
git switch develop
git pull origin develop
git switch -c fix/<ชื่อ-bug>

# แก้ไข + test
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

ตรวจสอบ:
- API
- Frontend
- Database migration
- Docker
- Tests
- Documentation

จากนั้น merge:
`release/v1.0.0 → main`

และ merge กลับ:
`release/v1.0.0 → develop`

สุดท้ายสร้าง tag:
```bash
git switch main
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```
## 8. Hotfix
ใช้เมื่อมีปัญหาเร่งด่วนบน `main`

```bash
git switch main
git pull origin main
git switch -c hotfix/<ชื่อ-bug>

# แก้ไข + test
git add .
git commit -m "fix: <รายละเอียด>"
git push -u origin hotfix/<ชื่อ-bug>
```

Merge เข้า:
1. `main`
2. `develop`

เพื่อให้ code ทั้งสองสายตรงกัน

## 9. Experiment
งานทดลองไม่ควรกระทบ `develop`

ตัวอย่าง:
```bash
git switch develop
git switch -c experiment-performance
```

เหมาะสำหรับ:
- benchmark
- query tuning
- Redis test
- H3 performance
- 50M / 100M scale test

เมื่อทดลองเสร็จ จะ merge หรือทิ้ง branch ก็ได้
## 10. Commit Convention
ใช้ prefix ให้สื่อความหมาย:

- `feat:` เพิ่ม feature
- `fix:` แก้ bug
- `docs:` แก้เอกสาร
- `refactor:` ปรับโครงสร้าง code
- `test:` เพิ่มหรือแก้ test
- `chore:` งาน maintenance / config

ตัวอย่าง:
```
feat: add GeoJSON ingestion
fix: correct H3 resolution validation
docs: add Git workflow
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
เพื่อไม่ให้ database dump เข้า Git
## 12. ตรวจสอบก่อน Commit
ใช้ทุกครั้งก่อน commit:

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
ถ้า branch ทำงานนานและ `develop` มีการเปลี่ยนแปลง:

```bash
git switch develop
git pull origin develop
git switch feature/<ชื่อ-feature>
git merge develop
```

แก้ conflict ถ้ามี แล้ว test ใหม่ก่อน push

## 14. ลบ Branch หลัง Merge
เมื่อ merge สำเร็จ:

```bash
git branch -d feature/<ชื่อ-feature>
git push origin --delete feature/<ชื่อ-feature>
```

ไม่จำเป็นต้องลบ branch experiment หากต้องการเก็บผลการทดลอง

## 15. GitHub Remote
ตอนนี้ repository ยังไม่ได้ตั้งค่า remote

เมื่อสร้าง GitHub repository แล้ว:

```bash
git remote add origin <GITHUB_REPOSITORY_URL>
git push -u origin main
git push -u origin develop
```

ตรวจสอบ:
```bash
git remote -v
git branch -a
```

## 16. Workflow สั้น ๆ
งานใหม่ → `feature/*` → PR → `develop`
→ test → `release/*` → `main` → tag

Bug → `fix/*` → `develop`

ปัญหาเร่งด่วน → `hotfix/*` → `main` + `develop`

ทดลอง → `experiment-*`

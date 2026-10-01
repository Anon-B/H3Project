# Git Workflow — H3Project
เอกสาร workflow สำหรับพัฒนา H3Project ด้วย Git

> **กฎสำคัญ:** H3Project เป็นโปรเจกต์ที่ทำงานคนเดียว จึงใช้ branch เท่าที่จำเป็นและลบ branch ชั่วคราวหลัง merge

## 1. Branch ที่ใช้งานจริง

```text
main
  └── stable / production

develop
  └── integration / testing

feature/next
  └── active development

release/vX.Y.Z
  └── temporary release preparation
```

### Permanent / Active

- `main` — stable / production
- `develop` — integration และ testing ก่อน release
- `feature/next` — active development branch สำหรับงานรอบถัดไป

### Temporary

- `release/vX.Y.Z` — สร้างเฉพาะเมื่อจำเป็นต้องเตรียม release และลบได้หลัง release
- temporary `feature/*`, `fix/*`, `hotfix/*` — สร้างเฉพาะงานที่มีเหตุผลต้องแยกจริง และลบหลัง merge

### ไม่ใช้เป็น permanent branch

ไม่มี branch ถาวรสำหรับ:

```text
feature/api
feature/database
feature/h3
feature/ingestion
feature/map
experiment
experiment-performance
experiment-scale-100m
```

งาน API, Database, H3, Ingestion และ Map ให้ทำบน `feature/next` เว้นแต่มีเหตุผลชัดเจนที่จะสร้าง temporary branch เฉพาะงาน

## 2. Workflow หลัก

```text
feature/next
    ↓
develop
    ↓
release/vX.Y.Z   (เมื่อจำเป็น)
    ↓
main
```

หลักการ:

1. งานพัฒนารอบถัดไป → `feature/next`
2. รวมงานและ integration test → `develop`
3. เตรียม release → `release/vX.Y.Z` เมื่อจำเป็น
4. release ที่ stable → `main`
5. ห้ามพัฒนาโดยตรงบน `develop` หรือ `main`

## 3. เริ่มงาน

```bash
git switch feature/next
git pull origin feature/next
```

ตรวจสอบก่อนแก้ไข:

```bash
git status
git branch -vv
```

## 4. Temporary Feature Branch

สร้าง temporary branch เฉพาะเมื่อ scope ใหญ่พอที่จะต้องแยกจาก `feature/next` เช่น:

```bash
git switch feature/next
git pull origin feature/next
git switch -c feature/ingestion-geojson
```

ทำเสร็จแล้ว merge กลับ `feature/next` และลบ branch:

```bash
git switch feature/next
git merge feature/ingestion-geojson
git branch -d feature/ingestion-geojson
git push origin --delete feature/ingestion-geojson
```

ไม่ควรสร้าง branch กว้าง ๆ ที่ค้างถาวร เช่น `feature/api` หรือ `feature/map`

## 5. Develop

`develop` ใช้สำหรับ integration/testing เท่านั้น

```text
feature/next
     ↓
   merge
     ↓
 develop
     ↓
integration test
```

ห้ามใช้ `develop` เป็นพื้นที่พัฒนาโดยตรง

## 6. Main

`main` คือ stable / production branch

ห้ามพัฒนาโดยตรงบน `main`

## 7. Release

ไม่จำเป็นต้องสร้าง `release/*` ทุกครั้ง

เมื่อจำเป็น:

```text
develop
    ↓
release/v1.3.0
    ↓
main
```

หลัง release ให้สร้าง tag บน commit ที่ release จริง:

```bash
git switch main
git tag -a v1.3.0 -m "Release v1.3.0"
git push origin main
git push origin v1.3.0
```

release branch ที่ไม่ต้อง maintenance ต่อสามารถลบได้:

```bash
git branch -d release/v1.3.0
git push origin --delete release/v1.3.0
```

## 8. Bug Fix / Hotfix

Bug fix ของงานปัจจุบันให้ทำบน `feature/next` หาก scope เล็กและไม่ต้องแยก branch

ถ้าต้องแยกจริง ใช้ temporary:

```text
fix/*
hotfix/*
```

และลบหลัง merge

## 9. Commit / Push

```bash
git status
git diff
git add .
git commit -m "feat: <รายละเอียด>"
git push -u origin feature/next
```

Commit convention:

- `feat:` เพิ่ม feature
- `fix:` แก้ bug
- `docs:` แก้เอกสาร
- `refactor:` ปรับโครงสร้าง code
- `test:` เพิ่มหรือแก้ test
- `chore:` maintenance / config

## 10. ตรวจสอบก่อน Commit

```bash
git status
git diff
git diff --cached
git diff --check
```

หลัง commit:

```bash
git log --oneline -5
git status
```

## 11. Sync กับ Develop

ถ้า `develop` มีการเปลี่ยนแปลง:

```bash
git switch develop
git pull origin develop
git switch feature/next
git merge develop
```

แก้ conflict ถ้ามี แล้ว test ใหม่ก่อน push

## 12. Current Branch Policy

Branch ที่ควรเห็นในการทำงานปกติ:

```text
main
develop
feature/next
release/vX.Y.Z   # เฉพาะ release ที่กำลังเตรียม
```

release branch รุ่นเก่าที่มี release/tag history แล้วสามารถคงไว้เป็น historical reference ได้ตาม repository policy

ไม่ควรมี permanent domain feature branch หรือ experiment branch

## 13. สิ่งที่ไม่ควร Commit

ห้าม commit:

- `.env` และ secret/token
- Database dump ขนาดใหญ่
- generated data
- log
- local cache
- credentials

## 14. GitHub Remote

Repository:

`https://github.com/Anon-B/H3Project.git`

ตรวจสอบ:

```bash
git remote -v
git branch -a
```

## 15. สรุป Workflow

```text
งานใหม่
   ↓
feature/next
   ↓
test
   ↓
develop
   ↓
integration test
   ↓
release/vX.Y.Z  (ถ้าจำเป็น)
   ↓
main
```

> **Project rule:** ไม่ใช้ permanent branch แยก API / Database / H3 / Ingestion / Map และไม่ใช้ permanent experiment branch

Repository:
`https://github.com/Anon-B/H3Project.git`

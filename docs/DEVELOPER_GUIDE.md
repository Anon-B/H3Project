# Developer Guide

## 1. Prerequisites
- macOS Apple Silicon
- Colima
- Docker + docker-compose
- Git
- Node/npm only if running frontend outside Docker
- Python only if running backend/scripts outside Docker.

## 2. Start
```bash
cd /Users/anonpond/H3Project
colima start --cpu 10 --memory 20 --disk 80
docker-compose up -d --build
docker-compose ps
```

## 3. Verify
```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8080
docker-compose logs --tail=100 api
docker-compose logs --tail=100 frontend
```

## 4. Frontend development
Source is `frontend/src/App.tsx`, `styles.css`, `muiTheme.ts`.
Build: `npm --prefix frontend run build`.
Docker deploy: `docker-compose build frontend && docker-compose up -d --force-recreate frontend`.
Frontend container serves built assets with Nginx.

## 5. Backend development
Main API is a single module: `app/main.py`.
Fresh DB schema: `sql/schema.sql`.
Existing DB changes: use a migration under `sql/migrations/` and verify it against the live schema.

## 6. Tests
```bash
docker-compose exec -T api pytest -q
docker-compose exec -T api python scripts/test_ingestion_api.py
```
For GeoJSON work, verify Preview -> Execute -> Dataset Registry -> Map.

## 7. Manual acceptance
1. Open Ingestion.
2. Upload or draw Point/Line/Polygon.
3. Preview H3.
4. Execute.
5. Open Datasets and confirm counts.
6. Open Map and change display resolution.
7. Click H3/entity and inspect JSON.
8. Change analytics/style/3D and confirm immediate UI response.

## 8. Git
Current workflow: feature/* -> develop -> main.
For current project work use `feature/ingestion` unless the task belongs elsewhere.
Never develop directly on develop/main.

## 9. Safe change sequence
Read architecture -> read data model -> change backend/schema -> update API docs -> update frontend -> build -> test -> inspect git diff -> commit.

## 10. Do not do
- Reintroduce h3_features.
- Store every display cell as canonical data.
- Assume old spatial_entities benchmark scripts describe current GeoJSON storage.
- Change source H3 resolution silently in Dataset Edit.
- Claim exact polygon geometry when only Boundary H3 is available.


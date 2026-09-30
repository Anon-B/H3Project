# Troubleshooting

## 1. Frontend old UI still appears
Check container and asset build:
```bash
docker-compose ps
docker-compose build frontend
docker-compose up -d --force-recreate frontend
```
Then hard refresh the browser.
Nginx is configured to avoid caching index.html while hashed assets remain immutable.

## 2. API is down
```bash
docker-compose ps
docker-compose logs --tail=200 api
curl http://localhost:8000/health
```
If DB is unhealthy, inspect db logs and disk/Colima resources.

## 3. DB cannot start
Check Colima memory/disk and PostgreSQL logs.
The compose DB uses shm_size=2gb and tuned PostgreSQL settings for the benchmark environment.
Do not copy benchmark tuning blindly to production.

## 4. Map dataset does not load
Check /health, then call:
```bash
curl 'http://localhost:8000/ingestion/dataset/h3?dataset=<name>&resolution=11'
```
Confirm response contains boundary_parts and entity_h3.

## 5. Map shows no filled polygon
Confirm dataset has outer Boundary H3 cells.
Frontend reconstruction depends on boundary_parts/ring_type.
A dataset with only point/line parts will not produce polygon fill.

## 6. Style & 3D does not update
Check browser console and React state first.
Confirm Style & 3D changes localStorage keys and that DeckGLOverlay receives new layer props.
The current implementation force-remounts DeckGLOverlay using visual-state key inputs.
If still broken, inspect @deck.gl/maplibre lifecycle/version before inventing redraw APIs.

## 7. Draw ingestion does not preview
Confirm drawing is synchronized into the FeatureCollection.
Use browser console and verify POST /ingestion/geojson/preview returns 200.

## 8. Execute fails
Call Preview first. Inspect the feature error list.
Common causes: invalid coordinates, unsupported geometry, too many generated H3 cells, missing dataset name.

## 9. Redis warning
Redis is optional for correctness. Verify /ready and redis container health.
A cache miss is normal; API can rebuild summary from DB.

## 10. Wrong documentation
Use DOCUMENTATION_INDEX and current code/schema as source of truth.
If an old document mentions h3_features or describes spatial_entities as current GeoJSON storage, update it rather than following it.


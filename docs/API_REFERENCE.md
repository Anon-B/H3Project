# API Reference

Base URL: `http://localhost:8000`

## GET /summary
`res=5|8`, `cache=true|false`  
Returns H3 summary polygons as GeoJSON. `source` tells whether Redis or DB supplied the data. Cache TTL is 300 seconds.

Example:
```bash
curl 'http://localhost:8000/summary?res=8'
```

## GET /nearby
Required: `lat`, `lng`. Optional: `radius_m` (1–50000), `limit` (1–5000), `active_only`, `mode=h3|db`.

`mode=h3` = H3 candidate selection + exact PostGIS. `mode=db` = exact PostGIS without H3, intended for benchmark comparison.

Example:
```bash
curl 'http://localhost:8000/nearby?lat=13.7563&lng=100.5018&radius_m=1000&limit=500'
```

## GET /bbox
Parameters: `min_lat,min_lng,max_lat,max_lng`, plus `limit` and `active_only`.
Returns Point GeoJSON. H3 Res8 narrows candidates before the spatial envelope predicate.

Example:
```bash
curl 'http://localhost:8000/bbox?min_lat=13.70&min_lng=100.45&max_lat=13.80&max_lng=100.55'
```

## GET /health /ready /metrics
Health checks DB and Redis; readiness reports degraded when Redis is unavailable; metrics returns DB/table/index sizes.

## Authentication
Set `API_KEY` in the environment. Then send `X-API-Key: <value>` to protected endpoints. `/health` and `/ready` remain public for container health checks.

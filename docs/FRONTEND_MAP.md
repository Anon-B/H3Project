# Frontend & Map Guide

## Stack
React 19 + TypeScript + Vite 7 + MUI 9 + MapLibre GL 5 + react-map-gl 8 + deck.gl 9 + h3-js 4 + maplibre-gl-draw.

## Files
- App.tsx: application state, pages, API calls and Map components.
- styles.css: global layout/design system.
- muiTheme.ts: MUI theme.
- main.tsx: React bootstrap + ThemeProvider.
- Dockerfile: Vite build + Nginx runtime.
- nginx.conf: cache behavior.

## Pages
Map | Overview | Datasets | Ingestion | Analysis | Settings

## Map data flow
```text
dataset selection
 -> /ingestion/dataset/h3
 -> boundary_parts + entity_h3
 -> displayCellsFromBoundary()
 -> H3HexagonLayer
 -> click/hover -> Inspector JSON
```

## Display reconstruction
For polygon outer boundary, frontend derives approximate filled H3 cells from the boundary.
Hole rings are removed from the filled set.
Target resolution can differ from source resolution.
This is visualization reconstruction, not replacement of original geometry.

## Map layers
- H3HexagonLayer: display cells, analytics-aware fill, wireframe/extrusion.
- ScatterplotLayer: entity markers.
- GeoJsonLayer: query/result geometry when present.

## Style & 3D
Controls persist in localStorage: data style, entity/fill/border colors, opacity, extrusion and height.
Style presets update colors; custom colors update individual channels.
3D uses deck.gl H3HexagonLayer extrusion/elevation.

## Async loading
Map loading uses loadSeq request sequencing to prevent stale requests from overwriting current dataset state.
If adding new async map calls, preserve the sequence guard pattern.

## Basemap
Basemap selection is kept in localStorage and applied through MapLibre style configuration.
Do not assume changing a basemap requires rebuilding H3 data.

## Inspector
Results are intentionally JSON-only. Keep the object shape compact and flatten attributes where possible.
Example: `{hex, entity_id, A}`.

## Drawing
DrawBridge uses maplibre-gl-draw events and synchronizes FeatureCollection into ingestion state.
Supported tools: Point, Line, Polygon, Select/Move, Edit Vertices, Use Drawing, Clear.

## Build/cache
Run `npm --prefix frontend run build`.
Nginx serves `index.html` with no-cache and hashed assets with immutable caching.
If old UI persists, hard refresh after confirming the frontend container was recreated.


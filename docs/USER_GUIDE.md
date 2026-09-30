# H3Project — User Guide

## Start
```bash
cd /Users/anonpond/H3Project
colima start --cpu 10 --memory 20 --disk 80
docker-compose up -d --build
```
Open http://localhost:8080.

## Overview
Shows workspace KPIs and recent datasets. Click a recent dataset to open it on Map.

## Datasets
Use Datasets to search the registry, open detail, edit metadata/catalog, view on Map or delete.
Core H3 resolution is locked in normal edit because changing it requires rebuilding coverage.

## Ingestion
1. Open Ingestion.
2. Choose File/GeoJSON or Draw.
3. Enter dataset name.
4. Choose source H3 resolution.
5. Review attributes/JSON.
6. Preview H3.
7. Execute.
8. Open Dataset Registry.

## Map
Choose dataset, then choose H3 Display Resolution.
Res 5 = coarse city/province view; Res 8 = neighborhood; Res 11 = fine detail.
Entities and H3 Cells can be toggled independently.

## Analysis
Analysis follows the active dataset and display resolution.
Available metric: No metric / Entity count.

## Style & 3D
Choose color preset or custom colors.
Adjust opacity, enable 3D Extrusion and adjust Height.
Settings persist in browser localStorage.

## Query
Map Query supports attribute/entity/H3/resolution conditions and current spatial options.
Results appear in the Inspector as JSON.

## Inspector
Click a cell/entity to inspect its JSON. Copy JSON from the Inspector.
The Inspector intentionally does not render a separate attribute table.

## Basemap
Use Basemap panel to switch map style without rebuilding data.

## Settings
Contains map defaults, runtime information and architecture note.

## Common flow
```text
Ingestion -> Dataset -> Map -> Analysis/Query -> Inspector
```


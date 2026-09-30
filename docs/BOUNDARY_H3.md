# Boundary H3 Storage Model

## Core rule
Boundary H3 is the canonical spatial representation for the current application.
Original Polygon/MultiPolygon coordinates are not persisted in canonical storage.

## Structure
```text
entities
  -> entity_parts
       -> entity_part_h3

entities
  -> entity_attributes.properties
```

## Ring semantics
- outer: polygon exterior boundary
- hole: polygon interior ring boundary
- line: line coverage
- none: point

## Polygon conversion
1. Convert polygon ring to overlapping H3 cells.
2. Keep cells that touch the outside of the covered set as boundary.
3. Store outer boundary and each hole independently.
4. Preserve ring_id/ring_type.

## MultiPolygon
One source Feature becomes one Entity with multiple polygon parts.
Each part has its own Boundary H3 set.

## Display reconstruction
The API returns Boundary H3 and ring metadata through /ingestion/dataset/h3.
Frontend converts boundary H3 to an approximate filled region at the selected display resolution.
Hole-derived cells are subtracted.

## Important distinction
Stored = Boundary H3.
Displayed = reconstructed Display H3.
Display H3 is not a canonical database layer.

## Accuracy
This representation is approximate and resolution-dependent.
It must not be described as lossless recovery of source polygon geometry.

## Compatibility
`entity_h3` is a view over `entity_part_h3`.


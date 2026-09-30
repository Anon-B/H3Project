# Boundary H3 Storage Model

## Goal

Polygon and MultiPolygon data are stored without original geometry. Canonical spatial storage keeps only H3 cells around each boundary ring.

- Polygon: boundary H3 only.
- Polygon holes: stored as separate ring_type=hole.
- MultiPolygon: each polygon becomes a separate entity_parts row.
- Attributes: stored per polygon part in entity_parts.properties JSONB.
- LineString: stores H3 coverage along the line.
- Point: stores one H3 cell plus exact latitude/longitude.
- Dataset controls the canonical H3 resolution.

## Canonical structure

entities
  |
  +-- entity_parts
  |     +-- part_index
  |     +-- part_type
  |     +-- bbox
  |     +-- properties JSONB
  |
  +-- entity_part_h3
        +-- part_id
        +-- resolution
        +-- ring_id
        +-- ring_type
        +-- h3_index

ring_type values: outer, hole, line, none.

## Polygon ingestion

1. Convert the outer ring to H3 cells using overlap containment.
2. Detect boundary cells by checking H3 neighbors.
3. Store only those boundary cells.
4. Repeat the same process independently for every hole.
5. Keep ring_id so outer and holes remain distinguishable.

The original coordinates are not stored.

## MultiPolygon

A MultiPolygon is one entity with multiple parts:

entity 1001
  +-- part 0 -> polygon A
  +-- part 1 -> polygon B
  +-- part 2 -> polygon C

The source Feature properties are copied to every polygon part. If the source contains separate Features, each Feature remains a separate entity.

## Display / reconstruction

The API reconstructs display H3 cells from stored boundary H3:

1. Read boundary H3 for the requested part and ring.
2. Convert the boundary cells to an H3 outline.
3. Re-fill the reconstructed outer ring at the dataset resolution.
4. Reconstruct every hole and subtract its H3 cells.
5. Return the resulting H3 cells to the Map.

The Map therefore displays interior H3 cells even though the database stores only boundary H3.

## Accuracy

Boundary-only storage is an H3 approximation, not lossless geometry storage. Accuracy is tied to the dataset H3 resolution. The system intentionally does not promise reconstruction of the original polygon coordinates.

## Spatial query implications

Boundary-only storage changes polygon query semantics.

- Attribute queries remain direct JSONB queries.
- BBox uses stored part bounding boxes as candidates.
- Polygon intersection uses boundary H3 plus bbox candidates.
- Exact original-geometry intersection is not available because original geometry is not retained.
- Point nearby remains exact using entity_point latitude/longitude.
- Line spatial coverage uses stored line H3 cells.

## Storage principle

Stored: Boundary H3
Displayed: Reconstructed full H3 coverage

This keeps canonical polygon storage small while preserving a complete H3 visualization at runtime.

## Example

A polygon with a hole may be stored as:

part 0
  ring 0 / outer -> H3 A, B, C, ...
  ring 1 / hole  -> H3 X, Y, Z, ...

At display time:

outer fill
    MINUS
hole fill
    =
display H3 coverage

## Compatibility

entity_h3 remains available as a view over entity_part_h3 for simple H3 lookup compatibility.

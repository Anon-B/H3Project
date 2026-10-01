import os
import httpx
import psycopg

db=os.getenv("DATABASE_URL","postgresql://h3:h3@db:5432/h3project")
lat,lng,radius=13.7563,100.5018,1000
body=httpx.get(f"http://api:8000/nearby?lat={lat}&lng={lng}&radius_m={radius}&limit=500",timeout=30).json()
ids=[f["properties"]["id"] for f in body["features"]]
with psycopg.connect(db) as conn:
    with conn.cursor() as cur:
        cur.execute("""SELECT count(*) FROM spatial_entities
                       WHERE id = ANY(%s)
                         AND ST_DWithin(geom::geography,
                           ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography,%s)""",
                    (ids,lng,lat,radius))
        exact=cur.fetchone()[0]
print({"api_count":len(ids),"exact_within_radius":exact,"candidate_cells":body["meta"]["candidate_cells"]})
assert exact==len(ids)

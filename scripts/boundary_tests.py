import httpx,psycopg,h3,os
BASE="http://api:8000"; DB=os.getenv("DATABASE_URL","postgresql://h3:h3@db:5432/h3project")
c=h3.latlng_to_cell(13.7563,100.5018,11);b=h3.cell_to_boundary(c);lat=sum(x[0] for x in b)/6;lng=sum(x[1] for x in b)/6
cases=[("center",13.7563,100.5018,1000),("boundary_near",lat,lng,100),("cross_cell",13.7563,100.5018,5000),("empty",20,110,100),("large",13.7563,100.5018,50000),("small",13.7563,100.5018,10)]
for name,la,lo,r in cases:
 d=httpx.get(f"{BASE}/nearby?lat={la}&lng={lo}&radius_m={r}&limit=500",timeout=60).json(); ids=[x["properties"]["id"] for x in d["features"]]
 with psycopg.connect(DB) as c:
  with c.cursor() as cur:
   cur.execute("SELECT count(*) FROM spatial_entities WHERE is_active AND ST_DWithin(geom::geography,ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography,%s)",(lo,la,r)); exact=cur.fetchone()[0]
 assert len(ids)==min(exact,500)
 print(name,{"api_count":len(ids),"exact_count":exact,"candidate_cells":d["meta"]["candidate_cells"]})
print("boundary tests passed")

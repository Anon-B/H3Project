import os
import csv
import psycopg

DB=os.getenv("DATABASE_URL","postgresql://h3:h3@db:5432/h3project")
CSV_PATH=os.getenv("CSV_PATH","/app/data/entities.csv")
BATCH=int(os.getenv("BATCH_SIZE","10000"))

sql="""INSERT INTO spatial_entities
(id,dataset,lat,lng,h3_res11,h3_res8,h3_res5,is_active,updated_at,geom)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,ST_SetSRID(ST_MakePoint(%s,%s),4326))
ON CONFLICT (id) DO UPDATE SET dataset=EXCLUDED.dataset,lat=EXCLUDED.lat,lng=EXCLUDED.lng,
h3_res11=EXCLUDED.h3_res11,h3_res8=EXCLUDED.h3_res8,h3_res5=EXCLUDED.h3_res5,
is_active=EXCLUDED.is_active,updated_at=EXCLUDED.updated_at,geom=EXCLUDED.geom"""

with psycopg.connect(DB) as conn, open(CSV_PATH,newline="") as f:
    reader=csv.DictReader(f); batch=[]; n=0
    for r in reader:
        batch.append((int(r["id"]),r["dataset"],float(r["lat"]),float(r["lng"]),r["h3_res11"],r["h3_res8"],r["h3_res5"],r["is_active"].lower()=="true",r["updated_at"],float(r["lng"]),float(r["lat"])))
        if len(batch)>=BATCH:
            with conn.cursor() as cur: cur.executemany(sql,batch)
            conn.commit(); n+=len(batch); batch=[]
    if batch:
        with conn.cursor() as cur: cur.executemany(sql,batch)
        conn.commit(); n+=len(batch)
print({"upserted":n,"mode":"incremental-upsert"})

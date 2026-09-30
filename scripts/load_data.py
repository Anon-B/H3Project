import os
from pathlib import Path
import psycopg

root = Path("/app")
db = os.getenv("DATABASE_URL", "postgresql://h3:h3@db:5432/h3project")
schema = (root / "sql/schema.sql").read_text()

with psycopg.connect(db, autocommit=True) as conn:
    conn.execute(schema)
    with conn.cursor() as cur:
        with cur.copy(
            "COPY spatial_entities(id,dataset,lat,lng,h3_res11,h3_res8,h3_res5,is_active,updated_at) "
            "FROM STDIN WITH (FORMAT csv, HEADER true)"
        ) as cp:
            with open(root / "data/entities.csv", "rb") as f:
                while chunk := f.read(1024 * 1024):
                    cp.write(chunk)
        cur.execute("UPDATE spatial_entities SET geom=ST_SetSRID(ST_MakePoint(lng,lat),4326)")
        cur.execute("ALTER TABLE spatial_entities ALTER COLUMN geom SET NOT NULL")
        cur.execute("ANALYZE spatial_entities")
print("load complete")

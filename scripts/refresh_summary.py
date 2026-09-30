import os
import psycopg

DB=os.getenv("DATABASE_URL","postgresql://h3:h3@db:5432/h3project")

with psycopg.connect(DB) as conn:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE h3_summary")
        cur.execute("""
            INSERT INTO h3_summary(h3_res5,entity_count,active_count)
            SELECT h3_res5,count(*),count(*) FILTER (WHERE is_active)
            FROM spatial_entities GROUP BY h3_res5
        """)
    conn.commit()
print("res5 summary refreshed")

# Res8 is maintained in the same table shape for the POC.
# See scripts/refresh_summary_res8.py for the dedicated Res8 Gold table.

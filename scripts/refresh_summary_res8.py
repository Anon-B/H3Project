import os
import psycopg

DB=os.getenv("DATABASE_URL","postgresql://h3:h3@db:5432/h3project")
with psycopg.connect(DB) as conn:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE h3_summary_res8")
        cur.execute("""
          INSERT INTO h3_summary_res8(h3_res8,entity_count,active_count)
          SELECT h3_res8,count(*),count(*) FILTER (WHERE is_active)
          FROM spatial_entities GROUP BY h3_res8
        """)
    conn.commit()
print("res8 summary refreshed")

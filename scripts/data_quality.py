import os
import psycopg
import h3
DB=os.getenv("DATABASE_URL","postgresql://h3:h3@db:5432/h3project")
with psycopg.connect(DB) as conn:
  with conn.cursor() as cur:
    cur.execute("""SELECT count(*),count(*) FILTER(WHERE lat BETWEEN -90 AND 90 AND lng BETWEEN -180 AND 180),count(*) FILTER(WHERE geom IS NULL),count(*) FILTER(WHERE h3_res11 IS NULL OR h3_res8 IS NULL OR h3_res5 IS NULL),count(*) FILTER(WHERE is_active),count(*) FILTER(WHERE NOT is_active),count(DISTINCT id) FROM spatial_entities""")
    total,coords,null_geom,null_h3,active,inactive,distinct_ids=cur.fetchone()
    cur.execute("SELECT count(*),count(DISTINCT h3_res5) FROM h3_summary");s5,c5=cur.fetchone()
    cur.execute("SELECT count(*),count(DISTINCT h3_res8) FROM h3_summary_res8");s8,c8=cur.fetchone()
    cur.execute("SELECT h3_res11,h3_res8,h3_res5 FROM spatial_entities TABLESAMPLE SYSTEM (0.02) LIMIT 10000"); rows=cur.fetchall()
bad_parent=sum(h3.cell_to_parent(a,8)!=b or h3.cell_to_parent(b,5)!=c for a,b,c in rows)
print({"total":total,"valid_coordinates":coords,"null_geom":null_geom,"null_h3":null_h3,"active":active,"inactive":inactive,"distinct_ids":distinct_ids,"res5_summary":s5,"res8_summary":s8,"parent_check_sample":len(rows),"bad_h3_parents":bad_parent})
assert total==distinct_ids and coords==total and null_geom==0 and null_h3==0 and active+inactive==total
assert s5==c5 and s8==c8 and bad_parent==0

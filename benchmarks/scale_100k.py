import os,time,statistics,psycopg,h3
DB=os.getenv("DATABASE_URL","postgresql://h3:h3@db:5432/h3project")
center=h3.latlng_to_cell(13.7563,100.5018,11);cells=list(h3.grid_disk(center,100))
with psycopg.connect(DB) as c:
 with c.cursor() as q:
  q.execute("DROP TABLE IF EXISTS spatial_entities_100k");q.execute("CREATE TABLE spatial_entities_100k AS SELECT * FROM spatial_entities ORDER BY id LIMIT 100000")
  q.execute("CREATE INDEX x11 ON spatial_entities_100k(h3_res11)");q.execute("CREATE INDEX xg ON spatial_entities_100k USING GIST(geom)");q.execute("ANALYZE spatial_entities_100k");c.commit()
  vals=[]
  for _ in range(20):
   t=time.perf_counter();q.execute("SELECT count(*) FROM spatial_entities_100k WHERE h3_res11=ANY(%s) AND ST_DWithin(geom::geography,ST_SetSRID(ST_MakePoint(100.5018,13.7563),4326)::geography,1000)",[cells]);q.fetchone();vals.append((time.perf_counter()-t)*1000)
  vals.sort();print({"dataset":100000,"p50_ms":round(statistics.median(vals),2),"p95_ms":round(vals[18],2),"p99_ms":round(vals[19],2),"note":"100k subset of validated 10M dataset"})
  q.execute("DROP TABLE spatial_entities_100k");c.commit()

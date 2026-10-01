import os,time,statistics,psycopg,h3
DB=os.getenv('DATABASE_URL','postgresql://h3:h3@localhost:5432/h3project')
with psycopg.connect(DB) as c:
    with c.cursor() as q:
        q.execute('DROP TABLE IF EXISTS benchmark_boundary_h3')
        q.execute('CREATE TEMP TABLE benchmark_boundary_h3 AS SELECT generate_series(1,100000) id, h3_index FROM entity_part_h3 WHERE resolution=11 LIMIT 1')
        q.execute('UPDATE benchmark_boundary_h3 SET h3_index=(SELECT h3_index FROM entity_part_h3 WHERE resolution=11 LIMIT 1)')
        q.execute('CREATE INDEX benchmark_boundary_h3_idx ON benchmark_boundary_h3(h3_index)')
        q.execute('ANALYZE benchmark_boundary_h3')
        cell=q.execute('SELECT h3_index FROM entity_part_h3 WHERE resolution=11 LIMIT 1').fetchone()[0]
        vals=[]
        for _ in range(50):
            t=time.perf_counter(); q.execute('SELECT count(*) FROM benchmark_boundary_h3 WHERE h3_index=%s',(cell,)); q.fetchone(); vals.append((time.perf_counter()-t)*1000)
        vals.sort()
        print({'rows':100000,'p50_ms':round(statistics.median(vals),3),'p95_ms':round(vals[47],3),'p99_ms':round(vals[49],3),'architecture':'canonical Boundary H3'})

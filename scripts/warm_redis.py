import os
import psycopg
import redis

db=os.getenv("DATABASE_URL","postgresql://h3:h3@db:5432/h3project")
rd=redis.Redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"),decode_responses=True)

with psycopg.connect(db) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT h3_res5,entity_count,active_count FROM h3_summary")
        rows=cur.fetchall()

pipe=rd.pipeline()
for cell,total,active in rows:
    pipe.set(f"h3:summary:5:{cell}",f"{total}|{active}")
pipe.execute()
rd.set("h3:summary:5:count",len(rows))
print(f"redis warmed: {len(rows)} cells")

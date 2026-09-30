import os
import redis
r=redis.Redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"))
keys=["h3:summary:res5:geojson","h3:summary:res8:geojson"]
print({"deleted":r.delete(*keys),"keys":keys})

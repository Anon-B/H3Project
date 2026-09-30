import json
import statistics
import time
import urllib.request

BASE="http://127.0.0.1:8000"
CASES=[
 ("health","/health"),
 ("nearby_1km","/nearby?lat=13.7563&lng=100.5018&radius_m=1000&limit=500"),
 ("nearby_5km","/nearby?lat=13.7563&lng=100.5018&radius_m=5000&limit=500"),
 ("bbox","/bbox?min_lat=13.70&min_lng=100.45&max_lat=13.80&max_lng=100.55&limit=5000"),
]
def get(path):
    t=time.perf_counter()
    with urllib.request.urlopen(BASE+path,timeout=30) as r:
        body=r.read()
    return (time.perf_counter()-t)*1000,len(body)
out=[]
for name,path in CASES:
    vals=[]
    sizes=[]
    for _ in range(30):
        ms,size=get(path); vals.append(ms); sizes.append(size)
    vals.sort()
    out.append({
        "case":name,"n":len(vals),
        "p50_ms":round(statistics.median(vals),2),
        "p95_ms":round(vals[int(len(vals)*.95)-1],2),
        "p99_ms":round(vals[int(len(vals)*.99)-1],2),
        "min_ms":round(min(vals),2),"max_ms":round(max(vals),2),
        "avg_payload_bytes":round(statistics.mean(sizes))
    })
print(json.dumps(out,indent=2))

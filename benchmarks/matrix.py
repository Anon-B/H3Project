import json,statistics,time,urllib.request
BASE="http://127.0.0.1:8000"
CASES={"A_DB_ONLY":"/nearby?lat=13.7563&lng=100.5018&radius_m=1000&limit=500&mode=db","B_H3_DB":"/nearby?lat=13.7563&lng=100.5018&radius_m=1000&limit=500&mode=h3","C_REDIS":"/summary?res=5&cache=true","DB_SUMMARY":"/summary?res=5&cache=false"}
def run(path):
 t=time.perf_counter()
 with urllib.request.urlopen(BASE+path,timeout=60) as r:body=r.read()
 return (time.perf_counter()-t)*1000,len(body)
for name,path in CASES.items():
 vals=[];sizes=[]
 for _ in range(5):
  ms,size=run(path);vals.append(ms);sizes.append(size)
 vals.sort();print(json.dumps({"case":name,"n":5,"p50_ms":round(statistics.median(vals),2),"p95_ms":round(vals[3],2),"p99_ms":round(vals[4],2),"avg_payload_bytes":round(statistics.mean(sizes))}),flush=True)

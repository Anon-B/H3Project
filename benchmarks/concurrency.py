import concurrent.futures
import statistics
import time
import urllib.request

URL="http://127.0.0.1:8000/nearby?lat=13.7563&lng=100.5018&radius_m=1000&limit=100"

def one(_):
    t=time.perf_counter()
    with urllib.request.urlopen(URL,timeout=30) as r: r.read()
    return (time.perf_counter()-t)*1000

for users in (10,50,100):
    vals=[]
    t0=time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=users) as ex:
        vals=list(ex.map(one,range(users)))
    elapsed=time.perf_counter()-t0
    vals.sort()
    print(users,{"p50_ms":round(statistics.median(vals),2),
        "p95_ms":round(vals[int(.95*len(vals))-1],2),
        "max_ms":round(max(vals),2),"rps":round(users/elapsed,2)})

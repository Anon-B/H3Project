import json,urllib.request
p=json.load(open('data/ingest_test.json'))
for ep in ('preview','execute'):
 req=urllib.request.Request('http://127.0.0.1:8000/ingestion/geojson/'+ep,data=json.dumps(p).encode(),headers={'Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(req,timeout=60) as r: print(ep,r.read().decode())

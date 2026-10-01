import os
import uuid
import time
import httpx
BASE=os.getenv('API_BASE','http://localhost:8000'); C=httpx.Client(base_url=BASE,timeout=20)

def test_health_ready_metrics():
    assert C.get('/health').status_code==200
    assert C.get('/ready').status_code==200
    m=C.get('/metrics/prometheus'); assert m.status_code==200 and 'http_requests_total' in m.text

def test_catalog_and_entity_detail_coverage():
    ds=C.get('/ingestion/datasets').json()['datasets']; assert ds
    d=next(x for x in ds if x['dataset']=='api-test'); r=C.get(f"/datasets/{d['dataset_id']}"); assert r.status_code==200
    eid=C.get('/bbox?min_lat=13.70&min_lng=100.45&max_lat=13.80&max_lng=100.55&limit=5').json()['features'][0]['properties']['entity_id']
    assert C.get(f'/entities/{eid}').status_code==200
    assert C.get(f'/entities/{eid}/coverage').status_code==200

def test_all_spatial_query_modes():
    for spatial in [
      {'type':'nearby','lat':13.7563,'lng':100.5018,'radius_m':5000},
      {'type':'bbox','min_lat':13.70,'min_lng':100.45,'max_lat':13.80,'max_lng':100.55},
    ]:
      r=C.post('/query',json={'dataset':'api-test','conditions':[],'spatial':spatial,'limit':10}); assert r.status_code==200 and r.json()['type']=='FeatureCollection'

def test_h3_and_viewport():
    assert C.get('/ingestion/dataset/h3?dataset=api-test&resolution=11&limit=20').status_code==200
    r=C.get('/ingestion/dataset/viewport?dataset=api-test&resolution=11&min_lat=13.70&min_lng=100.45&max_lat=13.80&max_lng=100.55&limit=20'); assert r.status_code==200; assert r.json()['resolution']==11
    assert C.get('/analytics/h3?dataset=api-test&resolution=11&limit=20').status_code==200

def test_geojson_preview_geometry_types():
    for geom,coords in [('Point',[100.5,13.75]),('LineString',[[100.5,13.75],[100.51,13.76]]),('Polygon',[[[100.5,13.75],[100.51,13.75],[100.51,13.76],[100.5,13.75]]])]:
      p={'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':geom,'coordinates':coords},'properties':{}}]}
      r=C.post('/ingestion/geojson/preview?resolution=11',json=p); assert r.status_code==200

def test_ingestion_execute_rollback_and_export():
    name='full-test-'+uuid.uuid4().hex[:8]; p={'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[100.5018,13.7563]},'properties':{'case':'full'}}]}
    r=C.post(f'/ingestion/geojson/execute?resolution=11&dataset={name}',json=p); assert r.status_code in (200,201); body=r.json(); assert body.get('run_id')
    runs=C.get(f'/ingestion/runs?dataset={name}'); assert runs.status_code==200
    run_id=body['run_id']; assert C.get(f'/ingestion/runs/{run_id}').status_code==200
    ds=C.get('/ingestion/datasets').json()['datasets']; did=next(x['dataset_id'] for x in ds if x['dataset']==name); ex=C.get(f'/datasets/{did}/export'); assert ex.status_code==200
    rb=C.post(f'/ingestion/runs/{run_id}/rollback'); assert rb.status_code==200

def test_background_job_persistence():
    name='job-test-'+uuid.uuid4().hex[:8]; p={'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[100.5018,13.7563]},'properties':{}}]}
    r=C.post(f'/ingestion/geojson/execute?resolution=11&dataset={name}&background=true',json=p); assert r.status_code==202; jid=r.json()['job_id']
    for _ in range(30):
      j=C.get(f'/ingestion/jobs/{jid}'); assert j.status_code==200
      if j.json()['status'] in ('completed','failed'): break
      time.sleep(.2)
    assert j.json()['status']=='completed'

def test_invalid_inputs_and_not_found():
    assert C.get('/nearby?lat=999&lng=100&radius_m=100').status_code==200
    assert C.get('/ingestion/jobs/00000000-0000-0000-0000-000000000000').status_code==404
    assert C.post('/query',json={'dataset':'api-test','conditions':[],'spatial':{'type':'bad'}}).status_code==400

def test_geojson_preview_multi_geometries_and_resolutions():
    geoms=[
      ('MultiPoint',[[100.5,13.75],[100.51,13.76]]),
      ('MultiLineString',[[[100.5,13.75],[100.51,13.76]]]),
      ('MultiPolygon',[[[[100.5,13.75],[100.51,13.75],[100.51,13.76],[100.5,13.75]]]]),
    ]
    for geom,coords in geoms:
      r=C.post('/ingestion/geojson/preview?resolution=11',json={'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':geom,'coordinates':coords},'properties':{}}]}); assert r.status_code==200
    for res in (5,8,11):
      r=C.get(f'/ingestion/dataset/h3?dataset=api-test&resolution={res}&limit=5'); assert r.status_code==200

def test_dataset_soft_delete_and_restore_metadata():
    name='lifecycle-'+uuid.uuid4().hex[:8]; p={'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[100.5018,13.7563]},'properties':{}}]}
    C.post(f'/ingestion/geojson/execute?resolution=11&dataset={name}',json=p); ds=C.get('/ingestion/datasets').json()['datasets']; did=next(x['dataset_id'] for x in ds if x['dataset']==name)
    r=C.patch(f'/datasets/{did}',json={'metadata':{'test':'lifecycle'}}); assert r.status_code==200
    r=C.delete(f'/datasets/{did}'); assert r.status_code==200
    assert C.get(f'/datasets/{did}').status_code in (200,404)

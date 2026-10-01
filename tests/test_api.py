import os
import httpx

BASE=os.getenv("API_BASE","http://localhost:8000")

def test_health():
    r=httpx.get(BASE+"/health",timeout=10)
    assert r.status_code==200
    assert r.json()["status"]=="ok"
    assert r.json()["entities"]>0

def test_nearby_geojson():
    r=httpx.get(BASE+"/nearby?lat=13.7563&lng=100.5018&radius_m=1000&limit=50",timeout=10)
    assert r.status_code==200
    body=r.json()
    assert body["type"]=="FeatureCollection"
    assert body["meta"]["count"]<=50
    for f in body["features"]:
        assert f["geometry"]["type"]=="Point"

def test_bbox_geojson():
    r=httpx.get(BASE+"/bbox?min_lat=13.70&min_lng=100.45&max_lat=13.80&max_lng=100.55&limit=50",timeout=10)
    assert r.status_code==200
    assert r.json()["type"]=="FeatureCollection"

def test_h3_analytics():
    r=httpx.get(BASE+"/analytics/h3?dataset=api-test&resolution=11&limit=10",timeout=10)
    assert r.status_code==200
    body=r.json()
    assert body["meta"]["source"]=="entity_part_h3"
    assert len(body["rows"])<=10
    for row in body["rows"]:
        assert row["h3_index"]
        assert row["entity_count"]>=1

def test_dataset_catalog():
    catalog=httpx.get(BASE+"/ingestion/datasets",timeout=10)
    assert catalog.status_code==200
    item=next(x for x in catalog.json()["datasets"] if x["dataset"]=="api-test")
    r=httpx.get(BASE+"/datasets/"+str(item["dataset_id"]),timeout=10)
    assert r.status_code==200
    body=r.json()
    assert "source" in body and "version" in body and "schema" in body

def test_query_nearby_returns_geometry():
    r=httpx.post(BASE+"/query",json={"dataset":"api-test","conditions":[],"spatial":{"type":"nearby","lat":13.7563,"lng":100.5018,"radius_m":5000},"limit":10},timeout=10)
    assert r.status_code==200
    body=r.json()
    assert body["meta"]["spatial_type"]=="nearby"
    assert all(x["geometry"] for x in body["features"])

def test_query_rejects_unknown_spatial_type():
    r=httpx.post(BASE+"/query",json={"dataset":"api-test","conditions":[],"spatial":{"type":"unknown"},"limit":10},timeout=10)
    assert r.status_code==400

def test_geojson_preview_accepts_altitude_and_rejects_invalid_coordinate():
    payload={"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[100.5,13.75,15]},"properties":{}}]}
    r=httpx.post(BASE+"/ingestion/geojson/preview?resolution=11",json=payload,timeout=10)
    assert r.status_code==200
    assert "error" not in r.json()["features"][0]
    bad={"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[100.5,1300]},"properties":{}}]}
    r=httpx.post(BASE+"/ingestion/geojson/execute?resolution=11&dataset=invalid-coordinate-test",json=bad,timeout=10)
    assert r.status_code==400

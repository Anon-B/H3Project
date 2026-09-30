import os
import httpx

BASE=os.getenv("API_BASE","http://api:8000")

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
    assert body["meta"]["source"]=="h3_features"
    assert len(body["rows"])<=10
    for row in body["rows"]:
        assert row["h3_index"]
        assert row["entity_count"]>=1

def test_dataset_catalog():
    r=httpx.get(BASE+"/datasets/4",timeout=10)
    assert r.status_code==200
    body=r.json()
    assert "source" in body and "version" in body and "schema" in body

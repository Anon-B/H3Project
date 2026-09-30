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

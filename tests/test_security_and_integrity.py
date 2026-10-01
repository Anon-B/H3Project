import os
import time
import uuid

from fastapi.testclient import TestClient

os.environ.setdefault("AUTH_MODE", "optional")

from app import main


client=TestClient(main.app)


def _restore_auth():
    main.AUTH_MODE="optional"
    main.API_KEYS={}
    main.API_KEY=""
    main.RATE_LIMIT=120
def test_invalid_api_key_is_rejected():
    main.AUTH_MODE="optional"
    main.API_KEYS={"valid-key":"viewer"}
    r=client.get("/ingestion/datasets",headers={"x-api-key":"wrong-key"})
    assert r.status_code==401
    _restore_auth()


def test_required_auth_and_rbac_are_enforced():
    main.AUTH_MODE="required"
    main.API_KEYS={"viewer-key":"viewer","editor-key":"editor"}
    payload={"type":"FeatureCollection","features":[]}
    viewer=client.post("/ingestion/geojson/execute?resolution=11&dataset=rbac-test",json=payload,headers={"x-api-key":"viewer-key"})
    assert viewer.status_code==403
    editor=client.post("/ingestion/geojson/execute?resolution=11&dataset=rbac-test",json=payload,headers={"x-api-key":"editor-key"})
    assert editor.status_code != 403
    _restore_auth()
def test_rate_limit_behavior_via_asgi():
    main.AUTH_MODE="required"
    main.API_KEYS={"rate-key":"viewer"}
    main.RATE_LIMIT=1
    bucket=int(time.time()//60)
    main.rdb.delete(f"rate:api-key:{bucket}")
    headers={"x-api-key":"rate-key"}
    first=client.get("/ingestion/datasets",headers=headers)
    second=client.get("/ingestion/datasets",headers=headers)
    assert first.status_code==200
    assert second.status_code==429
    _restore_auth()
def test_soft_deleted_dataset_does_not_leak():
    main.AUTH_MODE="required"
    main.API_KEYS={"editor-key":"editor"}
    name="soft-delete-"+uuid.uuid4().hex[:8]
    payload={"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[100.5018,13.7563]},"properties":{}}]}
    headers={"x-api-key":"editor-key"}
    created=client.post(f"/ingestion/geojson/execute?resolution=11&dataset={name}",json=payload,headers=headers)
    assert created.status_code in (200,201)
    deleted=client.delete(f"/datasets/{created.json().get('dataset_id',-1)}",headers=headers)
    if deleted.status_code==404:
        datasets=client.get("/ingestion/datasets",headers=headers).json()["datasets"]
        target=next(x for x in datasets if x["dataset"]==name)
        deleted=client.delete(f"/datasets/{target['dataset_id']}",headers=headers)
    assert deleted.status_code==200
    datasets=client.get("/ingestion/datasets",headers=headers).json()["datasets"]
    assert all(x["dataset"]!=name for x in datasets)
    _restore_auth()
def test_export_uses_rfc5987_for_thai_filename():
    main.AUTH_MODE="required"
    main.API_KEYS={"editor-key":"editor"}
    name="ทดสอบ-"+uuid.uuid4().hex[:6]
    payload={"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[100.5018,13.7563]},"properties":{"ชื่อ":"กรุงเทพ"}}]}
    headers={"x-api-key":"editor-key"}
    created=client.post(f"/ingestion/geojson/execute?resolution=11&dataset={name}",json=payload,headers=headers)
    assert created.status_code in (200,201)
    datasets=client.get("/ingestion/datasets",headers=headers).json()["datasets"]
    target=next(x for x in datasets if x["dataset"]==name)
    exported=client.get(f"/datasets/{target['dataset_id']}/export",headers=headers)
    assert exported.status_code==200
    disposition=exported.headers["content-disposition"]
    assert "filename*=UTF-8''" in disposition
    client.delete(f"/datasets/{target['dataset_id']}",headers=headers)
    _restore_auth()
def test_health_aliases_are_available():
    assert client.get("/health").status_code==200
    assert client.get("/healthz").status_code==200
    assert client.get("/ready").status_code==200
    assert client.get("/readyz").status_code==200

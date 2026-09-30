import os,time,json,h3,orjson,redis
from psycopg_pool import ConnectionPool
from fastapi import FastAPI,Query,HTTPException,Request
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
DB=os.getenv("DATABASE_URL","postgresql://h3:h3@db:5432/h3project");REDIS=os.getenv("REDIS_URL","redis://redis:6379/0");API_KEY=os.getenv("API_KEY","")
app=FastAPI(title="H3Project API",version="0.3.0",default_response_class=ORJSONResponse);rdb=redis.Redis.from_url(REDIS,decode_responses=True);pool=ConnectionPool(DB,min_size=2,max_size=20,open=True)
@app.middleware("http")
async def auth(request:Request,call_next):
    if API_KEY and request.url.path not in {"/health","/ready"} and request.headers.get("x-api-key")!=API_KEY:return ORJSONResponse({"detail":"invalid api key"},status_code=401)
    return await call_next(request)
def db_conn():return pool.connection()
def feature(row):
    ident,dataset,lat,lng,active,h11,h8,h5=row;return {"type":"Feature","geometry":{"type":"Point","coordinates":[lng,lat]},"properties":{"id":ident,"dataset":dataset,"is_active":active,"h3_res11":h11,"h3_res8":h8,"h3_res5":h5}}
def redis_ok():
    try:return bool(rdb.ping())
    except Exception:return False
@app.get("/health")
def health():
    try:
        with db_conn() as c:
            with c.cursor() as cur:cur.execute("SELECT count(*) FROM spatial_entities");count=cur.fetchone()[0]
    except Exception as e:raise HTTPException(503,"database unavailable") from e
    return {"status":"ok","entities":count,"redis":redis_ok()}
@app.get("/ready")
def ready():
    h=health();return {"status":"ready" if h["redis"] else "degraded","database":True,"redis":h["redis"]}
@app.get("/metrics")
def metrics():
    with db_conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT pg_database_size(current_database()),pg_relation_size('spatial_entities')");db_size,table_size=cur.fetchone();cur.execute("SELECT COALESCE(sum(pg_relation_size(indexrelid)),0) FROM pg_stat_user_indexes WHERE relname='spatial_entities'");index_size=cur.fetchone()[0]
    return {"database_bytes":db_size,"spatial_entities_table_bytes":table_size,"spatial_entities_indexes_bytes":index_size,"redis":redis_ok()}
@app.get("/summary")
def summary(res:int=Query(5,ge=5,le=8),cache:bool=True):
    key=f"h3:summary:res{res}:geojson"
    if cache and redis_ok():
        cached=rdb.get(key)
        if cached:return {"source":"redis","data":orjson.loads(cached),"ttl_s":rdb.ttl(key)}
    table="h3_summary" if res==5 else "h3_summary_res8";col="h3_res5" if res==5 else "h3_res8"
    with db_conn() as c:
        with c.cursor() as cur:cur.execute(f"SELECT {col},entity_count,active_count FROM {table} ORDER BY {col}");rows=cur.fetchall()
    features=[]
    for cell,total,active in rows:
        b=h3.cell_to_boundary(cell);coords=[[lng,lat] for lat,lng in b];coords.append(coords[0]);features.append({"type":"Feature","geometry":{"type":"Polygon","coordinates":[coords]},"properties":{col:cell,"entity_count":total,"active_count":active}})
    data={"type":"FeatureCollection","features":features}
    if redis_ok():rdb.setex(key,300,orjson.dumps(data))
    return {"source":"db","data":data,"ttl_s":300}

@app.get("/nearby")
def nearby(lat:float,lng:float,radius_m:float=Query(1000,gt=0,le=50000),limit:int=Query(500,gt=0,le=5000),active_only:bool=True,mode:str=Query("h3",pattern="^(h3|db)$")):
    started=time.perf_counter();params=[lng,lat,radius_m];clauses=["ST_DWithin(geom::geography,ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography,%s)"];cells=[]
    if mode=="h3":
        center=h3.latlng_to_cell(lat,lng,11);edge=h3.average_hexagon_edge_length(11,unit="km");k=max(1,int(radius_m/(edge*1000*1.5))+1);cells=list(h3.grid_disk(center,k));cells=cells[:50000];clauses.insert(0,"h3_res11 = ANY(%s)");params.insert(0,cells)
    if active_only:clauses.append("is_active")
    params += [lng,lat,limit];sql=f"SELECT id,dataset,lat,lng,is_active,h3_res11,h3_res8,h3_res5 FROM spatial_entities WHERE {' AND '.join(clauses)} ORDER BY ST_Distance(geom::geography,ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography) LIMIT %s"
    with db_conn() as c:
        with c.cursor() as cur:cur.execute(sql,params);rows=cur.fetchall()
    return {"type":"FeatureCollection","features":[feature(x) for x in rows],"meta":{"candidate_cells":len(cells),"count":len(rows),"elapsed_ms":round((time.perf_counter()-started)*1000,2),"source":mode}}
@app.get("/bbox")
def bbox(min_lat:float,min_lng:float,max_lat:float,max_lng:float,limit:int=Query(5000,gt=0,le=20000),active_only:bool=True):
    started=time.perf_counter();poly=h3.LatLngPoly([(min_lat,min_lng),(min_lat,max_lng),(max_lat,max_lng),(max_lat,min_lng)]);cells=list(h3.geo_to_cells(poly,8));clauses=["h3_res8 = ANY(%s)","geom && ST_MakeEnvelope(%s,%s,%s,%s,4326)"];params=[cells,min_lng,min_lat,max_lng,max_lat]
    if active_only:clauses.append("is_active")
    params.append(limit);sql=f"SELECT id,dataset,lat,lng,is_active,h3_res11,h3_res8,h3_res5 FROM spatial_entities WHERE {' AND '.join(clauses)} LIMIT %s"
    with db_conn() as c:
        with c.cursor() as cur:cur.execute(sql,params);rows=cur.fetchall()
    return {"type":"FeatureCollection","features":[feature(x) for x in rows],"meta":{"candidate_cells":len(cells),"count":len(rows),"elapsed_ms":round((time.perf_counter()-started)*1000,2),"source":"h3+postgis"}}
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"]);app.add_middleware(GZipMiddleware,minimum_size=1000)

from fastapi import Body

def _coords_to_latlng_polygon(coords):
    return [[[float(lat),float(lng)] for lng,lat in ring] for ring in coords]

def _geojson_cells(geometry,res):
    gtype=geometry.get("type"); coords=geometry.get("coordinates")
    if gtype=="Point":
        lng,lat=coords; return [h3.latlng_to_cell(float(lat),float(lng),res)]
    if gtype=="MultiPoint":
        return list({h3.latlng_to_cell(float(lat),float(lng),res) for lng,lat in coords})
    if gtype in {"Polygon","MultiPolygon"}:
        return list(h3.geo_to_cells(geometry,res))
    if gtype=="GeometryCollection":
        out=[]
        for g in geometry.get("geometries",[]): out.extend(_geojson_cells(g,res))
        return list(dict.fromkeys(out))
    raise ValueError(f"unsupported geometry type: {gtype}")

def _normalize_geojson(payload):
    if payload.get("type")=="FeatureCollection": return payload.get("features",[])
    if payload.get("type")=="Feature": return [payload]
    if payload.get("type") in {"Point","MultiPoint","Polygon","MultiPolygon","GeometryCollection"}:
        return [{"type":"Feature","geometry":payload,"properties":{}}]
    raise ValueError("GeoJSON must be FeatureCollection, Feature, or supported Geometry")

@app.post("/ingestion/geojson/preview")
def ingestion_preview(payload:dict=Body(...), resolution:int=Query(11,ge=5,le=15)):
    try: features=_normalize_geojson(payload)
    except Exception as e: raise HTTPException(400,str(e))
    if not features: raise HTTPException(400,"GeoJSON has no features")
    if len(features)>10000: raise HTTPException(413,"maximum 10,000 features per preview")
    result=[]; total={resolution:0}; unique={resolution:set()}; max_cells=200000
    for i,f in enumerate(features):
        geom=f.get("geometry") or {}; row={"feature_index":i,"feature_id":str(f.get("id",i)),"geometry_type":geom.get("type"),"properties":f.get("properties") or {}}
        try:
            cells=_geojson_cells(geom,resolution); row[f"h3_res{resolution}"]=cells; total[resolution]+=len(cells);unique[resolution].update(cells)
            if total[resolution] > max_cells: raise ValueError(f"H3 Res{resolution} output exceeds {max_cells} cells; reduce geometry size or process as a batch")
        except Exception as e: row["error"]=str(e)
        result.append(row)
    return {"source_type":"geojson","resolution":resolution,"feature_count":len(features),"cell_counts":{f"res{resolution}":total[resolution]},"unique_cells":{f"res{resolution}":len(unique[resolution])},"features":result}

@app.get("/ingestion/datasets")
def ingestion_datasets(limit:int=Query(100,ge=1,le=500)):
    with db_conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT dataset,count(*) FROM spatial_entities GROUP BY dataset ORDER BY dataset LIMIT %s",(limit,))
            rows=cur.fetchall()
    return {"datasets":[{"dataset":x[0],"feature_count":x[1]} for x in rows]}

def _dataset_geojson(dataset:str, limit:int=10000):
    if not dataset or not dataset.strip():
        raise HTTPException(400,"dataset is required")
    with db_conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT id,dataset,lat,lng,is_active,h3_res11,h3_res8,h3_res5 FROM spatial_entities WHERE dataset=%s ORDER BY id LIMIT %s",(dataset.strip(),limit))
            rows=cur.fetchall()
    features=[]
    for row in rows:
        ident,ds,lat,lng,active,h11,h8,h5=row
        features.append({"type":"Feature","id":str(ident),"geometry":{"type":"Point","coordinates":[lng,lat]},"properties":{"id":ident,"dataset":ds,"is_active":active}})
    return {"type":"FeatureCollection","features":features}

@app.post("/ingestion/dataset/preview")
def ingestion_dataset_preview(body:dict=Body(...)):
    dataset=str(body.get("dataset","")).strip()
    limit=int(body.get("limit",10000))
    resolution=int(body.get("resolution",11))
    if resolution<5 or resolution>15: raise HTTPException(400,"resolution must be 5..15")
    if limit<1 or limit>10000: raise HTTPException(400,"limit must be 1..10000")
    payload=_dataset_geojson(dataset,limit)
    preview=ingestion_preview(payload, resolution)
    preview["source_type"]="dataset"
    preview["dataset"]=dataset
    return preview

@app.post("/ingestion/dataset/execute")
def ingestion_dataset_execute(body:dict=Body(...)):
    dataset=str(body.get("dataset","")).strip()
    limit=int(body.get("limit",10000))
    resolution=int(body.get("resolution",11))
    if resolution<5 or resolution>15: raise HTTPException(400,"resolution must be 5..15")
    if limit<1 or limit>10000: raise HTTPException(400,"limit must be 1..10000")
    payload=_dataset_geojson(dataset,limit)
    preview=ingestion_preview(payload, resolution)
    if any("error" in x for x in preview["features"]): raise HTTPException(400,"one or more dataset features failed H3 conversion")
    with db_conn() as c:
        with c.cursor() as cur:
            cur.execute("INSERT INTO ingestion_runs(source_type,input_feature_count,output_cell_count,status,metadata) VALUES (%s,%s,%s,%s,%s) RETURNING id",("dataset",preview["feature_count"],sum(preview["cell_counts"].values()),"running",json.dumps({"dataset":dataset,"limit":limit,"resolution":resolution,"cell_counts":preview["cell_counts"]})))
            run_id=cur.fetchone()[0]
            rows=[]
            for f in preview["features"]:
                for cell in f[f"h3_res{resolution}"]:
                    rows.append((run_id,f["feature_id"],f["feature_index"],f["geometry_type"],resolution,cell,json.dumps(f["properties"])))
            cur.executemany("INSERT INTO ingestion_h3_cells(run_id,feature_id,feature_index,source_type,resolution,h3_index,properties) VALUES (%s,%s,%s,%s,%s,%s,%s)",rows)
            cur.execute("UPDATE ingestion_runs SET status='completed' WHERE id=%s",(run_id,));c.commit()
    return {"run_id":run_id,"status":"completed","dataset":dataset,"limit":limit,**{k:preview[k] for k in ("feature_count","cell_counts","unique_cells")}}

@app.post("/ingestion/geojson/execute")
def ingestion_execute(payload:dict=Body(...), resolution:int=Query(11,ge=5,le=15)):
    preview=ingestion_preview(payload, resolution)
    if any("error" in x for x in preview["features"]): raise HTTPException(400,"one or more features failed H3 conversion")
    with db_conn() as c:
        with c.cursor() as cur:
            cur.execute("INSERT INTO ingestion_runs(source_type,input_feature_count,output_cell_count,status,metadata) VALUES (%s,%s,%s,%s,%s) RETURNING id",("geojson",preview["feature_count"],sum(preview["cell_counts"].values()),"running",json.dumps({"resolution":resolution,"cell_counts":preview["cell_counts"]})))
            run_id=cur.fetchone()[0]
            rows=[]
            for f in preview["features"]:
                for cell in f[f"h3_res{resolution}"]:
                    rows.append((run_id,f["feature_id"],f["feature_index"],f["geometry_type"],resolution,cell,json.dumps(f["properties"])))
            cur.executemany("INSERT INTO ingestion_h3_cells(run_id,feature_id,feature_index,source_type,resolution,h3_index,properties) VALUES (%s,%s,%s,%s,%s,%s,%s)",rows)
            cur.execute("UPDATE ingestion_runs SET status='completed' WHERE id=%s",(run_id,));c.commit()
    return {"run_id":run_id,"status":"completed",**{k:preview[k] for k in ("feature_count","cell_counts","unique_cells")}}

@app.get("/ingestion/runs")
def ingestion_runs(limit:int=Query(20,ge=1,le=100)):
    with db_conn() as c:
        with c.cursor() as cur: cur.execute("SELECT id,source_type,input_feature_count,output_cell_count,status,created_at FROM ingestion_runs ORDER BY id DESC LIMIT %s",(limit,));rows=cur.fetchall()
    return {"runs":[dict(zip(["id","source_type","input_feature_count","output_cell_count","status","created_at"],r)) for r in rows]}

@app.get("/ingestion/runs/{run_id}")
def ingestion_run(run_id:int):
    with db_conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT id,source_type,input_feature_count,output_cell_count,status,created_at,metadata FROM ingestion_runs WHERE id=%s",(run_id,));r=cur.fetchone()
            if not r: raise HTTPException(404,"run not found")
            cur.execute("SELECT resolution,count(*),count(DISTINCT h3_index) FROM ingestion_h3_cells WHERE run_id=%s GROUP BY resolution ORDER BY resolution",(run_id,));stats=cur.fetchall()
    return {"id":r[0],"source_type":r[1],"input_feature_count":r[2],"output_cell_count":r[3],"status":r[4],"created_at":r[5],"metadata":r[6],"resolutions":[{"resolution":x[0],"rows":x[1],"unique_cells":x[2]} for x in stats]}

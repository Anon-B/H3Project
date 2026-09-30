import os,time,json
import h3,orjson,redis
from psycopg_pool import ConnectionPool
from fastapi import FastAPI,Query,HTTPException,Body,Request
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

DB=os.getenv("DATABASE_URL","postgresql://h3:h3@db:5432/h3project")
REDIS=os.getenv("REDIS_URL","redis://redis:6379/0")
API_KEY=os.getenv("API_KEY","")
app=FastAPI(title="H3Project API",version="0.5.0",default_response_class=ORJSONResponse)
rdb=redis.Redis.from_url(REDIS,decode_responses=True)
pool=ConnectionPool(DB,min_size=2,max_size=20,open=True)

@app.middleware("http")
async def auth(request:Request,call_next):
    if API_KEY and request.url.path not in {"/health","/ready"} and request.headers.get("x-api-key")!=API_KEY:
        return ORJSONResponse({"detail":"invalid api key"},status_code=401)
    return await call_next(request)

app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])
app.add_middleware(GZipMiddleware,minimum_size=1000)

def db_conn(): return pool.connection()
def redis_ok():
    try:return bool(rdb.ping())
    except Exception:return False

def _normalize_geojson(payload):
    if payload.get("type")=="FeatureCollection": return payload.get("features",[])
    if payload.get("type")=="Feature": return [payload]
    if payload.get("type") in {"Point","MultiPoint","Polygon","MultiPolygon","GeometryCollection"}:
        return [{"type":"Feature","geometry":payload,"properties":{}}]
    raise ValueError("GeoJSON must be FeatureCollection, Feature, or supported Geometry")

def _geojson_cells(geometry,res):
    gtype=geometry.get("type");coords=geometry.get("coordinates")
    if gtype=="Point":
        lng,lat=coords;return [h3.latlng_to_cell(float(lat),float(lng),res)]
    if gtype=="MultiPoint":
        return list({h3.latlng_to_cell(float(lat),float(lng),res) for lng,lat in coords})
    if gtype in {"Polygon","MultiPolygon"}: return list(h3.geo_to_cells(geometry,res))
    if gtype=="GeometryCollection":
        out=[]
        for g in geometry.get("geometries",[]):out.extend(_geojson_cells(g,res))
        return list(dict.fromkeys(out))
    raise ValueError(f"unsupported geometry type: {gtype}")

def _point_from_geometry(g):
    if g.get("type")=="Point":
        lng,lat=g["coordinates"];return float(lat),float(lng)
    if g.get("type")=="MultiPoint" and g.get("coordinates"):
        lng,lat=g["coordinates"][0];return float(lat),float(lng)
    return None

def _data_type(features):
    types={str((f.get("geometry") or {}).get("type","")).lower() for f in features}
    mapping={"point":"point","multipoint":"multipoint","polygon":"polygon","multipolygon":"multipolygon","geometrycollection":"geometry_collection"}
    vals={mapping[x] for x in types if x in mapping}
    if not vals:return "mixed"
    return vals.pop() if len(vals)==1 else "mixed"

def _preview(payload,res):
    features=_normalize_geojson(payload)
    if not features:raise HTTPException(400,"GeoJSON has no features")
    if len(features)>10000:raise HTTPException(413,"maximum 10,000 features per preview")
    rows=[];total=0;unique=set()
    for i,f in enumerate(features):
        geom=f.get("geometry") or {}
        row={"feature_index":i,"feature_id":str(f.get("id",i)),"geometry_type":geom.get("type"),"properties":f.get("properties") or {}}
        try:
            cells=_geojson_cells(geom,res);row[f"h3_res{res}"]=cells;total+=len(cells);unique.update(cells)
            if total>200000:raise ValueError(f"H3 Res{res} output exceeds 200000 cells")
        except Exception as e:row["error"]=str(e)
        rows.append(row)
    return {"source_type":"geojson","resolution":res,"feature_count":len(features),"cell_counts":{f"res{res}":total},"unique_cells":{f"res{res}":len(unique)},"features":rows}

@app.get("/health")
def health():
    try:
        with db_conn() as c:
            with c.cursor() as cur:cur.execute("SELECT count(*) FROM entities");count=cur.fetchone()[0]
    except Exception as e:raise HTTPException(503,"database unavailable") from e
    return {"status":"ok","entities":count,"redis":redis_ok()}

@app.get("/ready")
def ready():
    h=health();return {"status":"ready" if h["redis"] else "degraded","database":True,"redis":h["redis"]}

@app.get("/metrics")
def metrics():
    with db_conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT pg_database_size(current_database())");db_size=cur.fetchone()[0]
            cur.execute("SELECT COALESCE(sum(pg_total_relation_size(relid)),0) FROM pg_catalog.pg_statio_user_tables");table_size=cur.fetchone()[0]
            cur.execute("SELECT COALESCE(sum(pg_indexes_size(relid)),0) FROM pg_catalog.pg_statio_user_tables");index_size=cur.fetchone()[0]
    return {"database_bytes":db_size,"user_tables_bytes":table_size,"user_indexes_bytes":index_size,"redis":redis_ok()}

@app.get("/ingestion/datasets")
def ingestion_datasets(limit:int=Query(100,ge=1,le=500)):
    with db_conn() as c:
        with c.cursor() as cur:
            cur.execute("""SELECT d.dataset_id,d.name,d.data_type,d.h3_resolution,d.metadata,d.created_at,d.updated_at,count(e.entity_id)
                           FROM datasets d LEFT JOIN entities e ON e.dataset_id=d.dataset_id
                           GROUP BY d.dataset_id ORDER BY d.name LIMIT %s""",(limit,))
            rows=cur.fetchall()
    return {"datasets":[{"dataset_id":x[0],"dataset":x[1],"data_type":x[2],"h3_resolution":x[3],"metadata":x[4] or {},"created_at":x[5],"updated_at":x[6],"feature_count":x[7]} for x in rows]}

@app.get("/datasets/{dataset_id}")
def dataset_detail(dataset_id:int):
    with db_conn() as c:
        with c.cursor() as cur:
            cur.execute("""SELECT d.dataset_id,d.name,d.data_type,d.h3_resolution,d.metadata,d.created_at,d.updated_at,
                                  count(DISTINCT e.entity_id),count(DISTINCT h.h3_index)
                           FROM datasets d LEFT JOIN entities e ON e.dataset_id=d.dataset_id
                           LEFT JOIN entity_h3 h ON h.entity_id=e.entity_id
                           WHERE d.dataset_id=%s GROUP BY d.dataset_id""",(dataset_id,))
            x=cur.fetchone()
            if not x:raise HTTPException(404,"dataset not found")
    return {"dataset_id":x[0],"name":x[1],"data_type":x[2],"h3_resolution":x[3],"metadata":x[4] or {},"created_at":x[5],"updated_at":x[6],"entity_count":x[7],"h3_row_count":x[8]}

@app.patch("/datasets/{dataset_id}")
def update_dataset(dataset_id:int,body:dict=Body(...)):
    allowed={"name","metadata","h3_resolution"}
    changes={k:v for k,v in body.items() if k in allowed}
    if not changes:raise HTTPException(400,"nothing to update")
    if "h3_resolution" in changes and not 5<=int(changes["h3_resolution"])<=15:raise HTTPException(400,"resolution must be 5..15")
    with db_conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT 1 FROM datasets WHERE dataset_id=%s",(dataset_id,))
            if not cur.fetchone():raise HTTPException(404,"dataset not found")
            sets=[];vals=[]
            if "name" in changes:sets.append("name=%s");vals.append(str(changes["name"]).strip())
            if "metadata" in changes:sets.append("metadata=%s");vals.append(json.dumps(changes["metadata"] or {}))
            if "h3_resolution" in changes:sets.append("h3_resolution=%s");vals.append(int(changes["h3_resolution"]))
            vals.append(dataset_id)
            cur.execute("UPDATE datasets SET "+",".join(sets)+",updated_at=now() WHERE dataset_id=%s RETURNING dataset_id,name,data_type,h3_resolution,metadata,updated_at",vals)
            x=cur.fetchone();c.commit()
    return {"dataset_id":x[0],"name":x[1],"data_type":x[2],"h3_resolution":x[3],"metadata":x[4] or {},"updated_at":x[5]}

@app.delete("/datasets/{dataset_id}")
def delete_dataset(dataset_id:int):
    with db_conn() as c:
        with c.cursor() as cur:
            cur.execute("DELETE FROM datasets WHERE dataset_id=%s RETURNING dataset_id,name",(dataset_id,));x=cur.fetchone()
            if not x:raise HTTPException(404,"dataset not found")
            c.commit()
    if redis_ok():rdb.flushdb()
    return {"deleted":True,"dataset_id":x[0],"dataset":x[1]}

def _dataset_rows(name,limit=10000,res=None):
    sql="""SELECT e.entity_id,d.name,d.data_type,d.h3_resolution,p.latitude,p.longitude,a.properties,
                  COALESCE(array_agg(h.h3_index) FILTER (WHERE h.h3_index IS NOT NULL),'{}')
           FROM entities e JOIN datasets d ON d.dataset_id=e.dataset_id
           LEFT JOIN entity_point p ON p.entity_id=e.entity_id
           LEFT JOIN entity_attributes a ON a.entity_id=e.entity_id
           LEFT JOIN entity_h3 h ON h.entity_id=e.entity_id
           WHERE d.name=%s"""
    params=[name]
    if res is not None:sql+=" AND (h.resolution=%s OR h.resolution IS NULL)";params.append(res)
    sql+=" GROUP BY e.entity_id,d.name,d.data_type,d.h3_resolution,p.latitude,p.longitude,a.properties ORDER BY e.entity_id LIMIT %s";params.append(limit)
    with db_conn() as c:
        with c.cursor() as cur:cur.execute(sql,params);return cur.fetchall()

@app.post("/ingestion/dataset/preview")
def ingestion_dataset_preview(body:dict=Body(...)):
    name=str(body.get("dataset","")).strip();limit=int(body.get("limit",10000));res=int(body.get("resolution",11))
    if not name:raise HTTPException(400,"dataset is required")
    if not 5<=res<=15:raise HTTPException(400,"resolution must be 5..15")
    rows=_dataset_rows(name,min(limit,10000),res)
    if not rows:raise HTTPException(404,"dataset not found or empty")
    features=[];cells=set()
    for eid,ds,dt,default_res,lat,lng,props,hcells in rows:
        cells.update(hcells)
        if lat is not None and lng is not None:
            features.append({"type":"Feature","id":str(eid),"geometry":{"type":"Point","coordinates":[lng,lat]},"properties":{"entity_id":eid,"dataset":ds,"properties":props or {},f"h3_res{res}":hcells}})
    return {"source_type":"dataset","dataset":name,"resolution":res,"feature_count":len(rows),"unique_cells":{f"res{res}":len(cells)},"features":features}

@app.post("/query")
def advanced_query(body:dict=Body(...)):
    dataset=str(body.get("dataset") or "").strip() or None
    conditions=body.get("conditions") or []
    spatial=body.get("spatial") or {}
    limit=max(1,min(int(body.get("limit",5000)),20000))
    where=[];params=[]
    if dataset:where.append("d.name=%s");params.append(dataset)
    for cond in conditions:
        field=str(cond.get("field","")).strip();op=str(cond.get("operator","="));value=cond.get("value")
        if field=="entity_id":
            try:v=int(value)
            except:raise HTTPException(400,"entity_id must be numeric")
            if op not in {"=","!=","<",">","<=",">="}:raise HTTPException(400,"unsupported entity_id operator")
            where.append("e.entity_id "+op+" %s");params.append(v)
        elif field in {"h3_index","resolution"}:
            if field=="resolution":
                try:value=int(value)
                except:raise HTTPException(400,"resolution must be numeric")
            if op not in {"=","!=","<",">","<=",">="}:raise HTTPException(400,"unsupported H3 operator")
            where.append("h.resolution "+op+" %s" if field=="resolution" else "h.h3_index "+op+" %s");params.append(value)
        elif field.startswith("properties."):
            key=field.split(".",1)[1]
            if not key or op not in {"=","!=","contains"}:raise HTTPException(400,"unsupported attribute operator")
            if op=="contains":where.append("a.properties->>%s ILIKE %s");params.extend([key,"%"+str(value)+"%"])
            else:where.append("(a.properties->>%s) "+op+" %s");params.extend([key,str(value)])
        elif field=="attribute":
            if not isinstance(value,dict):raise HTTPException(400,"attribute filter value must be JSON object")
            where.append("a.properties @> %s::jsonb");params.append(json.dumps(value))
        elif field:raise HTTPException(400,"unsupported query field: "+field)
    stype=str(spatial.get("type","none"))
    if stype=="bbox":
        min_lat=float(spatial["min_lat"]);max_lat=float(spatial["max_lat"]);min_lng=float(spatial["min_lng"]);max_lng=float(spatial["max_lng"])
        where += ["p.latitude BETWEEN %s AND %s","p.longitude BETWEEN %s AND %s"];params += [min_lat,max_lat,min_lng,max_lng]
    elif stype=="nearby":
        lat=float(spatial["lat"]);lng=float(spatial["lng"]);radius=float(spatial.get("radius_m",1000))
        where.append("ST_DWithin(ST_SetSRID(ST_MakePoint(p.longitude,p.latitude),4326)::geography,ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography,%s)")
        params += [lng,lat,radius]
    elif stype=="polygon":
        geom=spatial.get("geojson")
        if not geom:raise HTTPException(400,"polygon geojson required")
        cells=_geojson_cells(geom,int(spatial.get("resolution",11)))
        if not cells:return {"type":"FeatureCollection","features":[],"meta":{"count":0}}
        where.append("h.h3_index = ANY(%s)");params.append(cells)
    if not where:where.append("TRUE")
    sql="""SELECT DISTINCT e.entity_id,d.name,d.data_type,d.h3_resolution,p.latitude,p.longitude,a.properties,h.h3_index,h.resolution
           FROM entities e JOIN datasets d ON d.dataset_id=e.dataset_id
           LEFT JOIN entity_point p ON p.entity_id=e.entity_id
           LEFT JOIN entity_attributes a ON a.entity_id=e.entity_id
           LEFT JOIN entity_h3 h ON h.entity_id=e.entity_id
           WHERE """+" AND ".join(where)+""" ORDER BY e.entity_id LIMIT %s"""
    params.append(limit)
    with db_conn() as c:
        with c.cursor() as cur:cur.execute(sql,params);rows=cur.fetchall()
    features=[]
    for x in rows:
        props={"entity_id":x[0],"dataset":x[1],"data_type":x[2],"h3_resolution":x[3],"properties":x[6] or {}}
        if x[7]:props.update({"h3_index":x[7],"resolution":x[8]})
        geom={"type":"Point","coordinates":[x[5],x[4]]} if x[4] is not None else None
        features.append({"type":"Feature","id":str(x[0]),"geometry":geom,"properties":props})
    return {"type":"FeatureCollection","features":features,"meta":{"count":len(features),"limit":limit,"spatial_type":stype}}

@app.get("/summary")
def summary(res:int=Query(5,ge=5,le=15),dataset:str|None=None):
    key=f"h3:summary:{dataset or '*'}:{res}"
    if redis_ok():
        cached=rdb.get(key)
        if cached:return {"source":"redis","data":orjson.loads(cached)}
    sql="""SELECT h.h3_index,count(*) FROM entity_h3 h JOIN entities e ON e.entity_id=h.entity_id
           JOIN datasets d ON d.dataset_id=e.dataset_id WHERE h.resolution=%s"""
    params=[res]
    if dataset:sql+=" AND d.name=%s";params.append(dataset)
    sql+=" GROUP BY h.h3_index ORDER BY h.h3_index"
    with db_conn() as c:
        with c.cursor() as cur:cur.execute(sql,params);rows=cur.fetchall()
    features=[]
    for cell,count in rows:
        ring=h3.cell_to_boundary(cell,geo_json=True);ring.append(ring[0])
        features.append({"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[lng,lat] for lat,lng in ring]]},"properties":{"h3_index":cell,"resolution":res,"entity_count":count}})
    data={"type":"FeatureCollection","features":features}
    if redis_ok():rdb.setex(key,300,orjson.dumps(data))
    return {"source":"db","data":data}

@app.get("/nearby")
def nearby(lat:float,lng:float,radius_m:float=Query(1000,gt=0,le=50000),limit:int=Query(500,gt=0,le=5000),dataset:str|None=None):
    clauses=["ST_DWithin(ST_SetSRID(ST_MakePoint(p.longitude,p.latitude),4326)::geography,ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography,%s)"];params=[lng,lat,radius_m]
    if dataset:clauses.append("d.name=%s");params.append(dataset)
    sql="""SELECT e.entity_id,d.name,p.latitude,p.longitude,a.properties FROM entity_point p JOIN entities e ON e.entity_id=p.entity_id JOIN datasets d ON d.dataset_id=e.dataset_id LEFT JOIN entity_attributes a ON a.entity_id=e.entity_id WHERE """+" AND ".join(clauses)+""" ORDER BY ST_Distance(ST_SetSRID(ST_MakePoint(p.longitude,p.latitude),4326)::geography,ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography) LIMIT %s"""
    params += [lng,lat,limit]
    with db_conn() as c:
        with c.cursor() as cur:cur.execute(sql,params);rows=cur.fetchall()
    return {"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[x[3],x[2]]},"properties":{"entity_id":x[0],"dataset":x[1],"properties":x[4] or {}}} for x in rows],"meta":{"count":len(rows),"source":"entity_point"}}

@app.get("/bbox")
def bbox(min_lat:float,min_lng:float,max_lat:float,max_lng:float,limit:int=Query(5000,gt=0,le=20000),dataset:str|None=None):
    clauses=["p.latitude BETWEEN %s AND %s","p.longitude BETWEEN %s AND %s"];params=[min_lat,max_lat,min_lng,max_lng]
    if dataset:clauses.append("d.name=%s");params.append(dataset)
    params.append(limit)
    sql="""SELECT e.entity_id,d.name,p.latitude,p.longitude,a.properties FROM entity_point p JOIN entities e ON e.entity_id=p.entity_id JOIN datasets d ON d.dataset_id=e.dataset_id LEFT JOIN entity_attributes a ON a.entity_id=e.entity_id WHERE """+" AND ".join(clauses)+""" LIMIT %s"""
    with db_conn() as c:
        with c.cursor() as cur:cur.execute(sql,params);rows=cur.fetchall()
    return {"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[x[3],x[2]]},"properties":{"entity_id":x[0],"dataset":x[1],"properties":x[4] or {}}} for x in rows],"meta":{"count":len(rows),"source":"bbox"}}

@app.post("/ingestion/geojson/preview")
def ingestion_preview(payload:dict=Body(...),resolution:int=Query(11,ge=5,le=15)):
    try:return _preview(payload,resolution)
    except HTTPException:raise
    except Exception as e:raise HTTPException(400,str(e))

def _next_entity_id(cur):
    cur.execute("SELECT COALESCE(max(entity_id),0)+1 FROM entities");return int(cur.fetchone()[0])

def _execute_ingestion(payload,res,dataset_name=None):
    preview=_preview(payload,res)
    if any("error" in x for x in preview["features"]):raise HTTPException(400,"one or more features failed H3 conversion")
    features=_normalize_geojson(payload);name=(dataset_name or "").strip()
    if not name:raise HTTPException(400,"dataset name is required")
    dtype=_data_type(features)
    with db_conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT dataset_id FROM datasets WHERE name=%s",(name,));existing=cur.fetchone()
            if existing:dataset_id=existing[0]
            else:
                cur.execute("INSERT INTO datasets(name,data_type,h3_resolution,metadata) VALUES (%s,%s,%s,%s) RETURNING dataset_id",(name,dtype,res,json.dumps({})));dataset_id=cur.fetchone()[0]
            cur.execute("INSERT INTO ingestion_runs(dataset_id,source_type,input_feature_count,output_cell_count,status,metadata) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",(dataset_id,"geojson",preview["feature_count"],sum(preview["cell_counts"].values()),"running",json.dumps({"resolution":res})));run_id=cur.fetchone()[0]
            for i,(f,pr) in enumerate(zip(features,preview["features"])):
                eid=_next_entity_id(cur);cur.execute("INSERT INTO entities(entity_id,dataset_id) VALUES (%s,%s)",(eid,dataset_id))
                point=_point_from_geometry(f.get("geometry") or {})
                if point:cur.execute("INSERT INTO entity_point(entity_id,latitude,longitude) VALUES (%s,%s,%s)",(eid,point[0],point[1]))
                cur.execute("INSERT INTO entity_attributes(entity_id,properties) VALUES (%s,%s)",(eid,json.dumps(f.get("properties") or {})))
                for cell in pr.get(f"h3_res{res}",[]):cur.execute("INSERT INTO entity_h3(entity_id,resolution,h3_index) VALUES (%s,%s,%s)",(eid,res,cell))
                for cell in pr.get(f"h3_res{res}",[]):cur.execute("INSERT INTO ingestion_h3_cells(run_id,feature_id,feature_index,source_type,resolution,h3_index,properties) VALUES (%s,%s,%s,%s,%s,%s,%s)",(run_id,str(f.get("id",i)),i,"geojson",res,cell,json.dumps(f.get("properties") or {})))
            cur.execute("UPDATE ingestion_runs SET status='completed' WHERE id=%s",(run_id,));c.commit()
    if redis_ok():rdb.flushdb()
    return {"run_id":run_id,"status":"completed","dataset":name,"resolution":res,"feature_count":preview["feature_count"],"cell_counts":preview["cell_counts"],"unique_cells":preview["unique_cells"]}

@app.post("/ingestion/geojson/execute")
def ingestion_execute(payload:dict=Body(...),resolution:int=Query(11,ge=5,le=15),dataset:str|None=None):
    return _execute_ingestion(payload,resolution,dataset)

@app.post("/ingestion/dataset/execute")
def ingestion_dataset_execute(body:dict=Body(...)):
    name=str(body.get("dataset","")).strip();res=int(body.get("resolution",11));limit=int(body.get("limit",10000))
    rows=_dataset_rows(name,min(limit,10000),res)
    if not rows:raise HTTPException(404,"dataset not found or empty")
    features=[{"type":"Feature","id":str(x[0]),"geometry":{"type":"Point","coordinates":[x[5],x[4]]} if x[4] is not None else None,"properties":x[6] or {}} for x in rows]
    return _execute_ingestion({"type":"FeatureCollection","features":[f for f in features if f["geometry"]]},res,name)

@app.get("/ingestion/runs")
def ingestion_runs(limit:int=Query(20,ge=1,le=100)):
    with db_conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT id,source_type,input_feature_count,output_cell_count,status,created_at FROM ingestion_runs ORDER BY id DESC LIMIT %s",(limit,));rows=cur.fetchall()
    return {"runs":[dict(zip(["id","source_type","input_feature_count","output_cell_count","status","created_at"],x)) for x in rows]}

@app.get("/ingestion/runs/{run_id}")
def ingestion_run(run_id:int):
    with db_conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT id,source_type,input_feature_count,output_cell_count,status,created_at,metadata FROM ingestion_runs WHERE id=%s",(run_id,));x=cur.fetchone()
            if not x:raise HTTPException(404,"run not found")
            cur.execute("SELECT resolution,count(*),count(DISTINCT h3_index) FROM ingestion_h3_cells WHERE run_id=%s GROUP BY resolution ORDER BY resolution",(run_id,));stats=cur.fetchall()
    return {"id":x[0],"source_type":x[1],"input_feature_count":x[2],"output_cell_count":x[3],"status":x[4],"created_at":x[5],"metadata":x[6],"resolutions":[{"resolution":a,"rows":b,"unique_cells":c} for a,b,c in stats]}

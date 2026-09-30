import os,time,json
import h3,orjson,redis
from pyproj import Geod
from shapely.geometry import shape,Polygon,MultiPolygon,mapping
from shapely.ops import unary_union
from psycopg_pool import ConnectionPool
from fastapi import FastAPI,Query,HTTPException,Body,Request
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

DB=os.getenv("DATABASE_URL","postgresql://h3:h3@db:5432/h3project")
REDIS=os.getenv("REDIS_URL","redis://redis:6379/0")
API_KEY=os.getenv("API_KEY","")
GEOD=Geod(ellps="WGS84")
app=FastAPI(title="H3Project API",version="0.7.0",default_response_class=ORJSONResponse)
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
    t=payload.get("type")
    if t=="FeatureCollection": return payload.get("features",[])
    if t=="Feature": return [payload]
    if t in {"Point","MultiPoint","LineString","MultiLineString","Polygon","MultiPolygon","GeometryCollection"}:
        return [{"type":"Feature","geometry":payload,"properties":{}}]
    raise ValueError("GeoJSON must be FeatureCollection, Feature, or supported Geometry")

def _poly_shape(outer,holes=None):
    return {"type":"Polygon","coordinates":[outer]+(holes or [])}

def _overlap_cells(geometry,res):
    return set(h3.polygon_to_cells_experimental(h3.geo_to_h3shape(geometry),res,"overlap"))

def _boundary_from_cells(cells):
    cells=set(cells)
    if not cells:return set()
    return {c for c in cells if any(n not in cells for n in h3.grid_disk(c,1))}

def _ring_boundary(ring,res):
    return _boundary_from_cells(_overlap_cells(_poly_shape(ring),res))

def _line_cells(coords,res):
    cells=set()
    if len(coords)<2:return cells
    for a,b in zip(coords,coords[1:]):
        sa=h3.latlng_to_cell(float(a[1]),float(a[0]),res)
        sb=h3.latlng_to_cell(float(b[1]),float(b[0]),res)
        try:cells.update(h3.grid_path_cells(sa,sb))
        except Exception:cells.update({sa,sb})
    return cells

def _geometry_parts(geometry,res):
    t=geometry.get("type")
    if t=="Point":
        lng,lat=geometry["coordinates"]
        return [{"part_index":0,"part_type":"point","rings":[(0,"none",[geometry["coordinates"]])],
                 "cells":[(0,"none",h3.latlng_to_cell(float(lat),float(lng),res))]}]
    if t=="MultiPoint":
        parts=[]
        for i,p in enumerate(geometry.get("coordinates",[])):
            lng,lat=p
            parts.append({"part_index":i,"part_type":"point","rings":[(0,"none",[p])],
                          "cells":[(0,"none",h3.latlng_to_cell(float(lat),float(lng),res))]})
        return parts
    if t=="LineString":
        return [{"part_index":0,"part_type":"line","rings":[(0,"line",geometry["coordinates"])],
                 "cells":[(0,"line",c) for c in _line_cells(geometry["coordinates"],res)]}]
    if t=="MultiLineString":
        return [{"part_index":i,"part_type":"line","rings":[(0,"line",line)],
                 "cells":[(0,"line",c) for c in _line_cells(line,res)]}
                for i,line in enumerate(geometry.get("coordinates",[]))]
    if t=="Polygon":
        coords=geometry.get("coordinates") or []
        if not coords:return []
        cells=[]
        outer=_ring_boundary(coords[0],res)
        cells.extend((0,"outer",c) for c in outer)
        for rid,hole in enumerate(coords[1:],1):
            cells.extend((rid,"hole",c) for c in _ring_boundary(hole,res))
        return [{"part_index":0,"part_type":"polygon",
                 "rings":[(i,"outer" if i==0 else "hole",r) for i,r in enumerate(coords)],
                 "cells":cells}]
    if t=="MultiPolygon":
        parts=[]
        for i,poly in enumerate(geometry.get("coordinates",[])):
            if not poly:continue
            cells=[(0,"outer",c) for c in _ring_boundary(poly[0],res)]
            for rid,hole in enumerate(poly[1:],1):
                cells.extend((rid,"hole",c) for c in _ring_boundary(hole,res))
            parts.append({"part_index":i,"part_type":"polygon",
                          "rings":[(j,"outer" if j==0 else "hole",r) for j,r in enumerate(poly)],
                          "cells":cells})
        return parts
    if t=="GeometryCollection":
        out=[];idx=0
        for g in geometry.get("geometries",[]):
            for part in _geometry_parts(g,res):
                part["part_index"]=idx;idx+=1;out.append(part)
        return out
    raise ValueError(f"unsupported geometry type: {t}")

def _geodesic_area(geom):
    if geom is None or geom.is_empty:return 0.0
    gt=geom.geom_type
    if gt=="Polygon":
        x,y=geom.exterior.xy;area=abs(GEOD.polygon_area_perimeter(x,y)[0])
        for hole in geom.interiors:
            x,y=hole.xy;area-=abs(GEOD.polygon_area_perimeter(x,y)[0])
        return max(0.0,area)
    if gt=="MultiPolygon":return sum(_geodesic_area(g) for g in geom.geoms)
    if hasattr(geom,"geoms"):return sum(_geodesic_area(g) for g in geom.geoms)
    return 0.0

def _analytics_for_part(part,res):
    out=[];ptype=part["part_type"]
    if ptype=="point":
        for _,_,cell in part["cells"]:out.append((cell,1.0,1.0,True,None))
        return out
    if ptype=="line":
        coords=part["rings"][0][2]
        geom=shape({"type":"LineString","coordinates":coords})
        centroid=geom.centroid
        centroid_cell=h3.latlng_to_cell(float(centroid.y),float(centroid.x),res)
        for _,_,cell in part["cells"]:out.append((cell,None,None,cell==centroid_cell,None))
        return out
    rings=part["rings"]
    holes=[[(float(x),float(y)) for x,y in r[2]] for _,_,r in rings[1:]]
    geom=Polygon([(float(x),float(y)) for x,y in rings[0][2]],holes)
    part_area=_geodesic_area(geom)
    centroid=geom.centroid
    centroid_cell=h3.latlng_to_cell(float(centroid.y),float(centroid.x),res)
    cells=_overlap_cells({"type":"Polygon","coordinates":[ring for _,_,ring in rings]},res)
    for cell in cells:
        cell_ring=[(float(lng),float(lat)) for lat,lng in h3.cell_to_boundary(cell)]
        cell_geom=Polygon(cell_ring)
        overlap=_geodesic_area(geom.intersection(cell_geom))
        cell_area=h3.cell_area(cell,unit="m^2")
        cell_cov=min(1.0,max(0.0,overlap/cell_area if cell_area else 0.0))
        poly_cov=min(1.0,max(0.0,overlap/part_area if part_area else 0.0))
        out.append((cell,cell_cov,poly_cov,cell==centroid_cell,None))
    return out

def _part_bbox(part):
    pts=[]
    for _,_,ring in part["rings"]:
        for p in ring:
            if p and isinstance(p[0],(int,float)):pts.append((float(p[1]),float(p[0])))
    if not pts:return None
    lats=[x[0] for x in pts];lngs=[x[1] for x in pts]
    return min(lats),min(lngs),max(lats),max(lngs)

def _ring_display_cells(boundary_cells,res):
    if not boundary_cells:return set()
    try:geo=h3.cells_to_geo(list(boundary_cells))
    except Exception:return set(boundary_cells)
    geom=shape(geo)
    polys=[geom] if isinstance(geom,Polygon) else list(geom.geoms) if isinstance(geom,MultiPolygon) else []
    result=set()
    for p in polys:
        shell=[[float(x),float(y)] for x,y in p.exterior.coords]
        try:
            result.update(_overlap_cells({"type":"Polygon","coordinates":[shell]},res))
        except Exception:
            result.update(boundary_cells)
    return result

def _display_cells_for_part_rows(rows,res):
    outer=set();holes=set();line=set();point=set()
    for ring_id,ring_type,cell in rows:
        if ring_type=="outer":outer.add(cell)
        elif ring_type=="hole":holes.add(cell)
        elif ring_type=="line":line.add(cell)
        else:point.add(cell)
    if outer:
        cells=_ring_display_cells(outer,res)
        for h in _group_ring_cells(rows,"hole"):
            cells-= _ring_display_cells(h,res)
        return cells
    if line:return line
    return point

def _group_ring_cells(rows,ring_type):
    ids=sorted({r[0] for r in rows if r[1]==ring_type})
    return [_cells_for_ring(rows,i,ring_type) for i in ids]

def _cells_for_ring(rows,ring_id,ring_type):
    return {r[2] for r in rows if r[0]==ring_id and r[1]==ring_type}

def _data_type(features):
    types={str((f.get("geometry") or {}).get("type","")).lower() for f in features}
    mapping={"point":"point","multipoint":"multipoint","linestring":"line",
             "multilinestring":"multiline","polygon":"polygon",
             "multipolygon":"multipolygon","geometrycollection":"geometry_collection"}
    vals={mapping[x] for x in types if x in mapping}
    if not vals:return "mixed"
    return vals.pop() if len(vals)==1 else "mixed"

def _preview(payload,res):
    features=_normalize_geojson(payload)
    if not features:raise HTTPException(400,"GeoJSON has no features")
    if len(features)>10000:raise HTTPException(413,"maximum 10,000 features per preview")
    rows=[];boundary_total=0;display_total=0;unique_boundary=set();unique_display=set()
    for i,f in enumerate(features):
        geom=f.get("geometry") or {}
        row={"feature_index":i,"feature_id":str(f.get("id",i)),
             "geometry_type":geom.get("type"),"properties":f.get("properties") or {},"parts":[]}
        try:
            parts=_geometry_parts(geom,res)
            for part in parts:
                b=[{"ring_id":r,"ring_type":rt,"h3_index":c} for r,rt,c in part["cells"]]
                display=_display_cells_for_part_rows(part["cells"],res)
                row["parts"].append({"part_index":part["part_index"],"part_type":part["part_type"],
                                     "boundary_h3":b,"display_h3":sorted(display)})
                boundary_total+=len(b);display_total+=len(display);unique_boundary.update(x["h3_index"] for x in b);unique_display.update(display)
            if boundary_total>200000 or display_total>500000:
                raise ValueError("H3 output exceeds preview limit")
        except Exception as e:row["error"]=str(e)
        rows.append(row)
    return {"source_type":"geojson","resolution":res,"feature_count":len(features),
            "boundary_cells":boundary_total,"display_cells":display_total,
            "unique_boundary_cells":len(unique_boundary),"unique_display_cells":len(unique_display),
            "features":rows}

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
    sql="""SELECT d.dataset_id,d.name,d.data_type,d.h3_resolution,d.metadata,d.created_at,d.updated_at,
                  d.source,d.owner,d.version,d.source_format,d.geographic_coverage,d.tags,d.license,d.update_frequency,
                  d.schema_definition,d.lineage,
                  count(DISTINCT e.entity_id),count(DISTINCT p.part_id),count(DISTINCT h.h3_index)
           FROM datasets d LEFT JOIN entities e ON e.dataset_id=d.dataset_id
           LEFT JOIN entity_parts p ON p.entity_id=e.entity_id
           LEFT JOIN entity_part_h3 h ON h.part_id=p.part_id
           GROUP BY d.dataset_id ORDER BY d.name LIMIT %s"""
    with db_conn() as c:
        with c.cursor() as cur:cur.execute(sql,(limit,));rows=cur.fetchall()
    return {"datasets":[{"dataset_id":x[0],"dataset":x[1],"data_type":x[2],"h3_resolution":x[3],
                         "metadata":x[4] or {},"created_at":x[5],"updated_at":x[6],
                         "source":x[7],"owner":x[8],"version":x[9],"source_format":x[10],
                         "geographic_coverage":x[11] or {},"tags":x[12] or [],"license":x[13],
                         "update_frequency":x[14],"schema":x[15] or {},"lineage":x[16] or {},
                         "feature_count":x[17],"part_count":x[18],"boundary_h3_count":x[19]} for x in rows]}

@app.get("/datasets/{dataset_id}")
def dataset_detail(dataset_id:int):
    sql="""SELECT d.dataset_id,d.name,d.data_type,d.h3_resolution,d.metadata,d.created_at,d.updated_at,
                  d.source,d.owner,d.version,d.source_format,d.geographic_coverage,d.tags,d.license,d.update_frequency,
                  d.schema_definition,d.lineage,
                  count(DISTINCT e.entity_id),count(DISTINCT p.part_id),count(DISTINCT h.h3_index)
           FROM datasets d LEFT JOIN entities e ON e.dataset_id=d.dataset_id
           LEFT JOIN entity_parts p ON p.entity_id=e.entity_id
           LEFT JOIN entity_part_h3 h ON h.part_id=p.part_id
           WHERE d.dataset_id=%s GROUP BY d.dataset_id"""
    with db_conn() as c:
        with c.cursor() as cur:cur.execute(sql,(dataset_id,));x=cur.fetchone()
    if not x:raise HTTPException(404,"dataset not found")
    return {"dataset_id":x[0],"name":x[1],"data_type":x[2],"h3_resolution":x[3],"metadata":x[4] or {},
            "created_at":x[5],"updated_at":x[6],"source":x[7],"owner":x[8],"version":x[9],"source_format":x[10],
            "geographic_coverage":x[11] or {},"tags":x[12] or [],"license":x[13],"update_frequency":x[14],
            "schema":x[15] or {},"lineage":x[16] or {},"entity_count":x[17],"part_count":x[18],
            "boundary_h3_count":x[19],"storage_mode":"boundary_h3"}

@app.patch("/datasets/{dataset_id}")
def update_dataset(dataset_id:int,body:dict=Body(...)):
    allowed={"name","metadata","h3_resolution","source","owner","version","source_format","geographic_coverage","tags","license","update_frequency","schema","lineage"};changes={k:v for k,v in body.items() if k in allowed}
    if not changes:raise HTTPException(400,"nothing to update")
    if "h3_resolution" in changes and not 5<=int(changes["h3_resolution"])<=15:
        raise HTTPException(400,"resolution must be 5..15")
    sets=[];vals=[]
    if "name" in changes:sets.append("name=%s");vals.append(str(changes["name"]).strip())
    if "metadata" in changes:sets.append("metadata=%s");vals.append(json.dumps(changes["metadata"] or {}))
    for key in ["source","owner","version","source_format","license","update_frequency"]:
        if key in changes:sets.append(key+"=%s");vals.append(str(changes[key] or ""))
    for key in ["geographic_coverage","schema_definition","lineage"]:
        body_key="schema" if key=="schema_definition" else key
        if body_key in changes:sets.append(key+"=%s");vals.append(json.dumps(changes[body_key] or {}))
    if "tags" in changes:sets.append("tags=%s");vals.append(list(changes["tags"] or []))
    if "h3_resolution" in changes:sets.append("h3_resolution=%s");vals.append(int(changes["h3_resolution"]))
    with db_conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT 1 FROM datasets WHERE dataset_id=%s",(dataset_id,))
            if not cur.fetchone():raise HTTPException(404,"dataset not found")
            vals.append(dataset_id)
            cur.execute("UPDATE datasets SET "+",".join(sets)+",updated_at=now() WHERE dataset_id=%s RETURNING dataset_id,name,data_type,h3_resolution,metadata,updated_at,source,owner,version,source_format,geographic_coverage,tags,license,update_frequency,schema_definition,lineage",vals)
            x=cur.fetchone();c.commit()
    return {"dataset_id":x[0],"name":x[1],"data_type":x[2],"h3_resolution":x[3],"metadata":x[4] or {},"updated_at":x[5],
            "source":x[6],"owner":x[7],"version":x[8],"source_format":x[9],"geographic_coverage":x[10] or {},
            "tags":x[11] or [],"license":x[12],"update_frequency":x[13],"schema":x[14] or {},"lineage":x[15] or {}}

@app.delete("/datasets/{dataset_id}")
def delete_dataset(dataset_id:int):
    with db_conn() as c:
        with c.cursor() as cur:
            cur.execute("DELETE FROM datasets WHERE dataset_id=%s RETURNING dataset_id,name",(dataset_id,));x=cur.fetchone()
            if not x:raise HTTPException(404,"dataset not found")
            c.commit()
    if redis_ok():rdb.flushdb()
    return {"deleted":True,"dataset_id":x[0],"dataset":x[1]}

def _next_entity_id(cur):
    cur.execute("SELECT COALESCE(max(entity_id),0)+1 FROM entities");return int(cur.fetchone()[0])

def _insert_feature(cur,entity_id,dataset_id,feature,res,run_id=None):
    geom=feature.get("geometry") or {}
    props=feature.get("properties") or {}
    parts=_geometry_parts(geom,res)
    for part in parts:
        bb=_part_bbox(part)
        cur.execute("""INSERT INTO entity_parts(
                       entity_id,part_index,part_type,min_lat,min_lng,max_lat,max_lng,properties,metadata)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING part_id""",
                    (entity_id,part["part_index"],part["part_type"],
                     *(bb or (None,None,None,None)),json.dumps(props),
                     json.dumps({"boundary_only":part["part_type"]=="polygon",
                                 "source_geometry":geom.get("type"),"resolution":res})))
        part_id=cur.fetchone()[0]
        ingestion_part_id=None
        if run_id is not None:
            cur.execute("""INSERT INTO ingestion_parts(
                           run_id,feature_id,feature_index,part_index,part_type,ring_count,properties)
                           VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                        (run_id,str(feature.get("id","")),feature.get("_index",0),
                         part["part_index"],part["part_type"],len(part["rings"]),json.dumps(props)))
            ingestion_part_id=cur.fetchone()[0]
        if part["part_type"]=="point" and part["part_index"]==0:
            p=part["rings"][0][2][0]
            cur.execute("""INSERT INTO entity_point(entity_id,latitude,longitude)
                           VALUES (%s,%s,%s) ON CONFLICT(entity_id) DO NOTHING""",
                        (entity_id,float(p[1]),float(p[0])))
        analytics=_analytics_for_part(part,res)
        for cell,cell_cov,poly_cov,is_centroid,pixel_cov in analytics:
            cur.execute("""INSERT INTO h3_features(
                           dataset_id,entity_id,part_id,resolution,h3_index,feature_type,
                           cell_coverage,polygon_coverage,centroid_cell,pixel_coverage,properties)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                           ON CONFLICT DO NOTHING""",
                        (dataset_id,entity_id,part_id,res,cell,part["part_type"],cell_cov,poly_cov,
                         is_centroid,pixel_cov,json.dumps(props)))
        for ring_id,ring_type,cell in part["cells"]:
            cur.execute("""INSERT INTO entity_part_h3(
                           part_id,resolution,ring_id,ring_type,h3_index)
                           VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                        (part_id,res,ring_id,ring_type,cell))
            if run_id is not None:
                cur.execute("""INSERT INTO ingestion_h3_cells(
                               run_id,part_id,feature_id,feature_index,part_index,ring_id,
                               ring_type,source_type,resolution,h3_index,properties)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (run_id,ingestion_part_id,str(feature.get("id","")),
                             feature.get("_index",0),part["part_index"],ring_id,ring_type,
                             "geojson",res,cell,json.dumps(props)))

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
                cur.execute("""INSERT INTO datasets(
                           name,data_type,h3_resolution,metadata,source,source_format)
                           VALUES (%s,%s,%s,%s,%s,%s) RETURNING dataset_id""",
                            (name,dtype,res,json.dumps({"storage_mode":"boundary_h3"}),"geojson","GeoJSON"));dataset_id=cur.fetchone()[0]
            cur.execute("""INSERT INTO ingestion_runs(dataset_id,source_type,input_feature_count,output_cell_count,status,metadata)
                           VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
                        (dataset_id,"geojson",preview["feature_count"],preview["boundary_cells"],"running",
                         json.dumps({"resolution":res,"storage_mode":"boundary_h3",
                         "display_reconstruction":"h3_boundary_fill"})));run_id=cur.fetchone()[0]
            for i,f in enumerate(features):
                f=dict(f);f["_index"]=i;eid=_next_entity_id(cur)
                cur.execute("INSERT INTO entities(entity_id,dataset_id) VALUES (%s,%s)",(eid,dataset_id))
                _insert_feature(cur,eid,dataset_id,f,res,run_id)
            cur.execute("UPDATE ingestion_runs SET status='completed' WHERE id=%s",(run_id,));c.commit()
    if redis_ok():rdb.flushdb()
    return {"run_id":run_id,"status":"completed","dataset":name,"resolution":res,
            "feature_count":preview["feature_count"],"stored_boundary_cells":preview["boundary_cells"],
            "display_cells":preview["display_cells"],"storage_mode":"boundary_h3"}

@app.post("/ingestion/geojson/preview")
def ingestion_preview(payload:dict=Body(...),resolution:int=Query(11,ge=5,le=15)):
    try:return _preview(payload,resolution)
    except HTTPException:raise
    except Exception as e:raise HTTPException(400,str(e))

@app.post("/ingestion/geojson/execute")
def ingestion_execute(payload:dict=Body(...),resolution:int=Query(11,ge=5,le=15),dataset:str|None=None):
    return _execute_ingestion(payload,resolution,dataset)

def _entity_parts(entity_id,res=None):
    sql="""SELECT p.part_id,p.part_index,p.part_type,p.min_lat,p.min_lng,p.max_lat,p.max_lng,p.properties,
                  h.ring_id,h.ring_type,h.h3_index,h.resolution
           FROM entity_parts p LEFT JOIN entity_part_h3 h ON h.part_id=p.part_id
           WHERE p.entity_id=%s"""
    params=[entity_id]
    if res is not None:sql+=" AND (h.resolution=%s OR h.resolution IS NULL)";params.append(res)
    sql+=" ORDER BY p.part_index,h.ring_id,h.h3_index"
    with db_conn() as c:
        with c.cursor() as cur:cur.execute(sql,params);return cur.fetchall()

def _h3_feature(cell,res,props):
    ring=list(h3.cell_to_boundary(cell));ring.append(ring[0])
    return {"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[lng,lat] for lat,lng in ring]]},
            "properties":{"h3_index":cell,"resolution":res,**props}}

@app.get("/entities/{entity_id}")
def entity_detail(entity_id:int):
    rows=_entity_parts(entity_id)
    if not rows:raise HTTPException(404,"entity not found")
    parts={}
    for x in rows:
        p=parts.setdefault(x[1],{"part_id":x[0],"part_index":x[1],"part_type":x[2],
                                  "bbox":[x[3],x[4],x[5],x[6]],"properties":x[7] or {},"boundary_h3":[]})
        if x[10]:p["boundary_h3"].append({"ring_id":x[8],"ring_type":x[9],"h3_index":x[10],"resolution":x[11]})
    return {"entity_id":entity_id,"parts":list(parts.values()),"storage_mode":"boundary_h3"}

@app.get("/entities/{entity_id}/coverage")
def entity_coverage(entity_id:int,resolution:int|None=None):
    rows=_entity_parts(entity_id,resolution)
    if not rows:raise HTTPException(404,"entity not found")
    groups={}
    for x in rows:
        groups.setdefault(x[1],{"part_type":x[2],"res":x[11] or resolution,"rows":[]})["rows"].append((x[8],x[9],x[10]))
    features=[]
    for idx,g in groups.items():
        cells=_display_cells_for_part_rows(g["rows"],g["res"])
        for c in cells:features.append(_h3_feature(c,g["res"],{"entity_id":entity_id,"part_index":idx,"part_type":g["part_type"]}))
    return {"type":"FeatureCollection","features":features,
            "meta":{"entity_id":entity_id,"resolution":resolution,"storage_mode":"boundary_h3","display_mode":"reconstructed_fill"}}

def _dataset_rows(name,limit=10000,res=None):
    sql="""SELECT e.entity_id,d.name,d.data_type,d.h3_resolution,p.part_id,p.part_index,p.part_type,
                  p.min_lat,p.min_lng,p.max_lat,p.max_lng,p.properties,
                  h.ring_id,h.ring_type,h.h3_index,h.resolution
           FROM entities e JOIN datasets d ON d.dataset_id=e.dataset_id
           JOIN entity_parts p ON p.entity_id=e.entity_id
           LEFT JOIN entity_part_h3 h ON h.part_id=p.part_id
           WHERE d.name=%s"""
    params=[name]
    if res is not None:sql+=" AND (h.resolution=%s OR h.resolution IS NULL)";params.append(res)
    sql+=" ORDER BY e.entity_id,p.part_index,h.ring_id,h.h3_index"
    if limit>0:
        sql+=" LIMIT %s";params.append(limit*100)
    with db_conn() as c:
        with c.cursor() as cur:cur.execute(sql,params);return cur.fetchall()

@app.post("/ingestion/dataset/preview")
def ingestion_dataset_preview(body:dict=Body(...)):
    name=str(body.get("dataset","")).strip();limit=int(body.get("limit",0))
    res=int(body.get("resolution",11))
    if not name:raise HTTPException(400,"dataset is required")
    if not 5<=res<=15:raise HTTPException(400,"resolution must be 5..15")
    rows=_dataset_rows(name,max(0,limit),res)
    if not rows:raise HTTPException(404,"dataset not found or empty")
    entities={};features=[]
    for x in rows:
        entities.setdefault(x[0],{"dataset":x[1],"data_type":x[2],"res":x[3],"parts":{}})
        p=entities[x[0]]["parts"].setdefault(x[5],{"part_type":x[6],"rows":[],"properties":x[11] or {},"res":x[15] or res})
        if x[14]:p["rows"].append((x[12],x[13],x[14]))
    for eid,e in entities.items():
        for idx,p in e["parts"].items():
            cells=_display_cells_for_part_rows(p["rows"],p["res"])
            for c in cells:features.append(_h3_feature(c,p["res"],{"entity_id":eid,"dataset":e["dataset"],"part_index":idx,"properties":p["properties"]}))
    return {"type":"FeatureCollection","features":features,
            "meta":{"dataset":name,"resolution":res,"entity_count":len(entities),"display_mode":"reconstructed_fill"}}

@app.post("/query")
def advanced_query(body:dict=Body(...)):
    dataset=str(body.get("dataset") or "").strip() or None
    conditions=body.get("conditions") or [];spatial=body.get("spatial") or {}
    limit=max(1,min(int(body.get("limit",5000)),20000));where=[];params=[]
    if dataset:where.append("d.name=%s");params.append(dataset)
    for cond in conditions:
        field=str(cond.get("field","")).strip();op=str(cond.get("operator","="));value=cond.get("value")
        if field=="entity_id":
            if op not in {"=","!=","<",">","<=",">="}:raise HTTPException(400,"unsupported entity_id operator")
            where.append("e.entity_id "+op+" %s");params.append(int(value))
        elif field.startswith("properties."):
            key=field.split(".",1)[1]
            if op not in {"=","!=","contains"}:raise HTTPException(400,"unsupported attribute operator")
            if op=="contains":where.append("p.properties->>%s ILIKE %s");params.extend([key,"%"+str(value)+"%"])
            else:where.append("(p.properties->>%s) "+op+" %s");params.extend([key,str(value)])
        elif field=="attribute":
            if not isinstance(value,dict):raise HTTPException(400,"attribute filter value must be JSON object")
            where.append("p.properties @> %s::jsonb");params.append(json.dumps(value))
        elif field=="h3_index":
            if op not in {"=","!="}:raise HTTPException(400,"unsupported h3_index operator")
            where.append("h.h3_index "+op+" %s");params.append(value)
        elif field=="resolution":
            if op not in {"=","!=","<",">","<=",">="}:raise HTTPException(400,"unsupported resolution operator")
            where.append("h.resolution "+op+" %s");params.append(int(value))
        elif field:raise HTTPException(400,"unsupported query field: "+field)
    stype=str(spatial.get("type","none"))
    if stype=="bbox":
        where.append("p.min_lat <= %s AND p.max_lat >= %s AND p.min_lng <= %s AND p.max_lng >= %s")
        params += [float(spatial["max_lat"]),float(spatial["min_lat"]),float(spatial["max_lng"]),float(spatial["min_lng"])]
    elif stype=="polygon":
        geom=spatial.get("geojson")
        if not geom:raise HTTPException(400,"polygon geojson required")
        qcells=_overlap_cells(geom,int(spatial.get("resolution",11)))
        if qcells:
            where.append("(h.h3_index = ANY(%s) OR (p.min_lat <= %s AND p.max_lat >= %s AND p.min_lng <= %s AND p.max_lng >= %s))")
            params += [list(qcells),float(spatial.get("max_lat",90)),float(spatial.get("min_lat",-90)),
                       float(spatial.get("max_lng",180)),float(spatial.get("min_lng",-180))]
    if not where:where.append("TRUE")
    sql="""SELECT DISTINCT e.entity_id,d.name,d.data_type,d.h3_resolution,p.part_id,p.part_index,p.part_type,
                  p.min_lat,p.min_lng,p.max_lat,p.max_lng,p.properties
           FROM entities e JOIN datasets d ON d.dataset_id=e.dataset_id
           JOIN entity_parts p ON p.entity_id=e.entity_id
           LEFT JOIN entity_part_h3 h ON h.part_id=p.part_id
           WHERE """+" AND ".join(where)+""" ORDER BY e.entity_id,p.part_index LIMIT %s"""
    params.append(limit)
    with db_conn() as c:
        with c.cursor() as cur:cur.execute(sql,params);rows=cur.fetchall()
    features=[]
    for x in rows:
        props={"entity_id":x[0],"dataset":x[1],"data_type":x[2],"h3_resolution":x[3],
               "part_index":x[5],"part_type":x[6],"properties":x[11] or {}}
        features.append({"type":"Feature","geometry":None,"properties":props})
    return {"type":"FeatureCollection","features":features,
            "meta":{"count":len(features),"limit":limit,"spatial_type":stype,"storage_mode":"boundary_h3"}}

@app.get("/analytics/h3")
def h3_analytics(dataset:str|None=None,resolution:int=Query(11,ge=5,le=15),limit:int=Query(50000,ge=1,le=200000)):
    sql="""SELECT h.h3_index,
                  count(DISTINCT h.entity_id) AS entity_count,
                  count(*) AS feature_count,
                  avg(h.cell_coverage) AS avg_cell_coverage,
                  max(h.polygon_coverage) AS polygon_coverage,
                  bool_or(h.centroid_cell) AS centroid_cell
           FROM h3_features h
           WHERE h.resolution=%s"""
    params=[resolution]
    if dataset:
        sql+=" AND EXISTS (SELECT 1 FROM datasets d WHERE d.dataset_id=h.dataset_id AND d.name=%s)"
        params.append(dataset)
    sql+=" GROUP BY h.h3_index ORDER BY entity_count DESC,h.h3_index LIMIT %s";params.append(limit)
    with db_conn() as c:
        with c.cursor() as cur:cur.execute(sql,params);rows=cur.fetchall()
    return {"rows":[{"h3_index":x[0],"entity_count":x[1],"feature_count":x[2],
                     "avg_cell_coverage":x[3],"polygon_coverage":x[4],"centroid_cell":bool(x[5])} for x in rows],
            "meta":{"dataset":dataset,"resolution":resolution,"count":len(rows),"source":"h3_features"}}

@app.get("/summary")
def summary(res:int=Query(5,ge=5,le=15),dataset:str|None=None):
    key=f"h3:summary:{dataset or '*'}:{res}"
    if redis_ok():
        cached=rdb.get(key)
        if cached:return {"source":"redis","data":orjson.loads(cached)}
    sql="""SELECT h.h3_index,count(DISTINCT p.entity_id) FROM entity_part_h3 h
           JOIN entity_parts p ON p.part_id=h.part_id JOIN entities e ON e.entity_id=p.entity_id
           JOIN datasets d ON d.dataset_id=e.dataset_id WHERE h.resolution=%s"""
    params=[res]
    if dataset:sql+=" AND d.name=%s";params.append(dataset)
    sql+=" GROUP BY h.h3_index ORDER BY h.h3_index"
    with db_conn() as c:
        with c.cursor() as cur:cur.execute(sql,params);rows=cur.fetchall()
    features=[_h3_feature(cell,res,{"entity_count":count,"storage_role":"boundary"}) for cell,count in rows]
    data={"type":"FeatureCollection","features":features}
    if redis_ok():rdb.setex(key,300,orjson.dumps(data))
    return {"source":"db","data":data}

@app.get("/nearby")
def nearby(lat:float,lng:float,radius_m:float=Query(1000,gt=0,le=50000),limit:int=Query(500,gt=0,le=5000),dataset:str|None=None):
    clauses=["ST_DWithin(ST_SetSRID(ST_MakePoint(p.longitude,p.latitude),4326)::geography,ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography,%s)"]
    params=[lng,lat,radius_m]
    if dataset:clauses.append("d.name=%s");params.append(dataset)
    sql="""SELECT e.entity_id,d.name,p.latitude,p.longitude,ep.properties
           FROM entity_point p JOIN entities e ON e.entity_id=p.entity_id JOIN datasets d ON d.dataset_id=e.dataset_id
           LEFT JOIN entity_parts ep ON ep.entity_id=e.entity_id AND ep.part_index=0
           WHERE """+" AND ".join(clauses)+""" ORDER BY ST_Distance(ST_SetSRID(ST_MakePoint(p.longitude,p.latitude),4326)::geography,
           ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography) LIMIT %s"""
    params += [lng,lat,limit]
    with db_conn() as c:
        with c.cursor() as cur:cur.execute(sql,params);rows=cur.fetchall()
    return {"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[x[3],x[2]]},
            "properties":{"entity_id":x[0],"dataset":x[1],"properties":x[4] or {}}} for x in rows],
            "meta":{"count":len(rows),"source":"entity_point"}}

@app.get("/bbox")
def bbox(min_lat:float,min_lng:float,max_lat:float,max_lng:float,limit:int=Query(5000,gt=0,le=20000),dataset:str|None=None):
    clauses=["p.latitude BETWEEN %s AND %s","p.longitude BETWEEN %s AND %s"];params=[min_lat,max_lat,min_lng,max_lng]
    if dataset:clauses.append("d.name=%s");params.append(dataset)
    params.append(limit)
    sql="""SELECT e.entity_id,d.name,p.latitude,p.longitude,ep.properties
           FROM entity_point p JOIN entities e ON e.entity_id=p.entity_id JOIN datasets d ON d.dataset_id=e.dataset_id
           LEFT JOIN entity_parts ep ON ep.entity_id=e.entity_id AND ep.part_index=0
           WHERE """+" AND ".join(clauses)+""" LIMIT %s"""
    with db_conn() as c:
        with c.cursor() as cur:cur.execute(sql,params);rows=cur.fetchall()
    return {"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[x[3],x[2]]},
            "properties":{"entity_id":x[0],"dataset":x[1],"properties":x[4] or {}}} for x in rows],
            "meta":{"count":len(rows),"source":"bbox"}}

@app.post("/ingestion/dataset/execute")
def ingestion_dataset_execute(body:dict=Body(...)):
    name=str(body.get("dataset","")).strip();res=int(body.get("resolution",11))
    rows=_dataset_rows(name,min(int(body.get("limit",10000)),10000),res)
    if not rows:raise HTTPException(404,"dataset not found or empty")
    features=[]
    seen=set()
    for x in rows:
        if x[0] in seen:continue
        seen.add(x[0])
        if x[6]!="point":continue
        features.append({"type":"Feature","id":str(x[0]),"geometry":None,"properties":x[11] or {}})
    if not features:return {"status":"noop","reason":"dataset contains no point parts"}
    return {"status":"noop","reason":"dataset execute is retained for compatibility; use GeoJSON execute for boundary ingestion"}

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
            cur.execute("""SELECT resolution,ring_type,count(*),count(DISTINCT h3_index)
                           FROM ingestion_h3_cells WHERE run_id=%s GROUP BY resolution,ring_type ORDER BY resolution,ring_type""",(run_id,));stats=cur.fetchall()
    return {"id":x[0],"source_type":x[1],"input_feature_count":x[2],"output_cell_count":x[3],
            "status":x[4],"created_at":x[5],"metadata":x[6],
            "h3_storage":[{"resolution":a,"ring_type":b,"rows":c,"unique_cells":d} for a,b,c,d in stats],
            "storage_mode":"boundary_h3"}

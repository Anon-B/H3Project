import { Tooltip, IconButton, Chip, Slider, FormControlLabel, Switch, Accordion, AccordionSummary, AccordionDetails, TextField, MenuItem, FormControl, InputLabel, Select, Button, Autocomplete, Stack, Paper, Divider, Alert, LinearProgress, Stepper, Step, StepLabel, Table, TableHead, TableBody, TableRow, TableCell, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SearchIcon from '@mui/icons-material/Search';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import LightModeIcon from '@mui/icons-material/LightMode';
import BarChartIcon from '@mui/icons-material/BarChart';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';
import HomeIcon from '@mui/icons-material/Home';
import ExploreIcon from '@mui/icons-material/Explore';
import LayersIcon from '@mui/icons-material/Layers';
import TuneIcon from '@mui/icons-material/Tune';
import CloseIcon from '@mui/icons-material/Close';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import MapOutlinedIcon from '@mui/icons-material/MapOutlined';
import StorageIcon from '@mui/icons-material/Storage';
import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import AnalyticsOutlinedIcon from '@mui/icons-material/AnalyticsOutlined';
import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined';
import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined';
import RefreshIcon from '@mui/icons-material/Refresh';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import DeleteIcon from '@mui/icons-material/Delete';
import SaveOutlinedIcon from '@mui/icons-material/SaveOutlined';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircle';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import {lazy,Suspense,useCallback,useEffect,useMemo,useRef,useState} from 'react';
import {H3HexagonLayer} from '@deck.gl/geo-layers';
import {GeoJsonLayer,ScatterplotLayer} from '@deck.gl/layers';
import {PageHeader,Metric,SectionCard,Results} from './components/ui';
import {API,apiFetch} from './lib/api';
import DatasetsPage from './components/DatasetsPage';
import type {FeatureCollection} from 'geojson';
import * as h3 from 'h3-js';
const LazyMapShell=lazy(()=>import('./components/MapShell').then(m=>({default:m.MapShell})));
const LazyDrawMap=lazy(()=>import('./components/DrawMap'));
const LazySystemHealth=lazy(()=>import('./components/SystemHealth'));
const BASEMAPS:any={liberty:{name:'Liberty',url:'https://tiles.openfreemap.org/styles/liberty'},bright:{name:'Bright',url:'https://tiles.openfreemap.org/styles/bright'},positron:{name:'Positron',url:'https://tiles.openfreemap.org/styles/positron'},dark:{name:'Dark',url:'https://tiles.openfreemap.org/styles/dark'},fiord:{name:'Fiord',url:'https://tiles.openfreemap.org/styles/fiord'},colorful:{name:'Colorful',url:'https://tiles.versatiles.org/assets/styles/colorful/style.json'}};
const DATA_COLOR_STYLES:any={default:{name:'Default Blue',entity:'#2563eb',fill:'#2563eb',line:'#1d4ed8',opacity:.13},emerald:{name:'Emerald',entity:'#059669',fill:'#10b981',line:'#047857',opacity:.15},amber:{name:'Amber',entity:'#d97706',fill:'#f59e0b',line:'#b45309',opacity:.16},violet:{name:'Violet',entity:'#7c3aed',fill:'#8b5cf6',line:'#6d28d9',opacity:.15},mono:{name:'Monochrome',entity:'#374151',fill:'#6b7280',line:'#1f2937',opacity:.14}};
export type Dataset={dataset_id:number;dataset:string;data_type:string;h3_resolution:number;feature_count:number;part_count:number;boundary_h3_count:number;metadata?:Record<string,any>;created_at?:string;updated_at?:string;source?:string;owner?:string;version?:string;source_format?:string;geographic_coverage?:Record<string,any>;tags?:string[];license?:string;update_frequency?:string;schema?:Record<string,any>;lineage?:Record<string,any>};
type Entity={entity_id:any;latitude:number;longitude:number;[key:string]:any};
function rgb(hex:string){const n=parseInt(hex.replace('#',''),16);return[(n>>16)&255,(n>>8)&255,n&255]}
function uniq<T>(a:T[]){return[...new Set(a)]}
function h3Bounds(cells:string[]){let a=[Infinity,Infinity],b=[-Infinity,-Infinity];for(const cell of cells){try{const [lat,lng]=h3.cellToLatLng(cell);a=[Math.min(a[0],lng),Math.min(a[1],lat)];b=[Math.max(b[0],lng),Math.max(b[1],lat)]}catch{}}return a[0]===Infinity?null:[a,b]}
function displayCellsFromBoundary(parts:any[],targetRes:number,entityMeta:Map<number,any>){
 const out=new globalThis.Map<string,any>();
 const add=(entity_id:number,properties:any,cell:string)=>out.set(entity_id+'|'+cell,{hex:cell,entity_id,...(properties||{})});
 const convert=(cells:string[],sourceRes:number,entity_id:number,properties:any)=>{
  for(const cell of cells){
   try{
    if(targetRes===sourceRes)add(entity_id,properties,cell);
    else if(targetRes<sourceRes)add(entity_id,properties,h3.cellToParent(cell,targetRes));
    else h3.cellToChildren(cell,targetRes).forEach((x:string)=>add(entity_id,properties,x));
   }catch{}
  }
 };
 const fillRing=(cells:string[],sourceRes:number,entity_id:number,properties:any)=>{
  if(!cells.length)return new Set<string>();
  const filled=new Set<string>();
  try{
   const polygons=h3.cellsToMultiPolygon(cells,true) as any[];
   for(const poly of polygons){
    try{
     const outerLoop=Array.isArray(poly?.[0])?[poly[0]]:poly;
     h3.polygonToCells(outerLoop,targetRes,true).forEach((x:string)=>filled.add(x));
    }catch{}
   }
  }catch{}
  if(!filled.size){
   convert(cells,sourceRes,entity_id,properties);
  }
  return filled;
 };
 for(const part of parts||[]){
  const sourceRes=Number(part.resolution)||targetRes;
  const entity_id=Number(part.entity_id);
  const properties=entityMeta.get(entity_id)||{};
  const rings=Object.values(part.rings||{}) as any[];
  const outer=rings.filter((r:any)=>r.ring_type==='outer').flatMap((r:any)=>r.h3||[]);
  const holes=rings.filter((r:any)=>r.ring_type==='hole').map((r:any)=>r.h3||[]);
  const lines=rings.filter((r:any)=>r.ring_type==='line').flatMap((r:any)=>r.h3||[]);
  const points=rings.filter((r:any)=>r.ring_type==='none').flatMap((r:any)=>r.h3||[]);
  if(outer.length){
   const filled=fillRing(outer,sourceRes,entity_id,properties);
   holes.forEach((h:string[])=>fillRing(h,sourceRes,entity_id,properties).forEach((x:string)=>filled.delete(x)));
   filled.forEach(x=>add(entity_id,properties,x));
  }else if(lines.length)convert(lines,sourceRes,entity_id,properties);
  else if(points.length)convert(points,sourceRes,entity_id,properties);
 }
 return Array.from(out.values());
}
export default function App(){
 const mapRef=useRef<any>(null),drawRef=useRef<any|null>(null),loadSeq=useRef(0);
 const [page,setPage]=useState('map'),[datasets,setDatasets]=useState<Dataset[]>([]),[dataset,setDataset]=useState<Dataset|null>(null);
 const [entities,setEntities]=useState<Entity[]>([]),[cells,setCells]=useState<string[]>([]),[boundaryParts,setBoundaryParts]=useState<any[]>([]),[resolution,setResolution]=useState(Number(localStorage.getItem('h3-default-resolution')||11));
 const [h3Visible,setH3Visible]=useState(true),[entityVisible,setEntityVisible]=useState(true),[resultOpen,setResultOpen]=useState(false),[results,setResults]=useState<any[]>([]);
 const [height3d,setHeight3d]=useState(Number(localStorage.getItem('h3-height-3d')||120)),[extruded3d,setExtruded3d]=useState(localStorage.getItem('h3-extruded-3d')==='true');
 const [analyticsMode,setAnalyticsMode]=useState(localStorage.getItem('h3-analytics-mode')||'off'),[analyticsRows,setAnalyticsRows]=useState<any[]>([]);
 const [dark,setDark]=useState(localStorage.getItem('h3-theme')==='dark'),[basemap,setBasemap]=useState(localStorage.getItem('h3-basemap')||'liberty');
 const [accent,setAccent]=useState(localStorage.getItem('h3-accent')||'#4264fb');
 const [compact,setCompact]=useState(localStorage.getItem('h3-compact')==='true');
 const [animations,setAnimations]=useState(localStorage.getItem('h3-animations')!=='false');
 const [projection,setProjection]=useState(localStorage.getItem('h3-projection')||'flat');
 const [mapControls,setMapControls]=useState(localStorage.getItem('h3-map-controls')!=='false');
 const [h3Grid,setH3Grid]=useState(localStorage.getItem('h3-grid')!=='false');
 const [healthRefresh,setHealthRefresh]=useState(Number(localStorage.getItem('h3-health-refresh')||30));
 const [confirmDelete,setConfirmDelete]=useState(localStorage.getItem('h3-confirm-delete')!=='false');
 const [stats,setStats]=useState(false),[toast,setToast]=useState(''),[hoverInfo,setHoverInfo]=useState<any>(null),[workerDisplay,setWorkerDisplay]=useState<any[]>([]);
 const h3Worker=useRef<Worker|null>(null);
 const [colors,setColors]=useState(()=>({entity:localStorage.getItem('h3-entity-color')||'#2563eb',fill:localStorage.getItem('h3-h3-color')||'#2563eb',line:localStorage.getItem('h3-h3-line-color')||'#1d4ed8',opacity:Number(localStorage.getItem('h3-h3-opacity')||13)/100}));
 const [dataStyle,setDataStyle]=useState(localStorage.getItem('h3-data-style')||'default');
 const applyDataStyle=(key:string)=>{const s=DATA_COLOR_STYLES[key];if(!s)return;setDataStyle(key);setColors({entity:s.entity,fill:s.fill,line:s.line,opacity:s.opacity});localStorage.setItem('h3-data-style',key);localStorage.setItem('h3-entity-color',s.entity);localStorage.setItem('h3-h3-color',s.fill);localStorage.setItem('h3-h3-line-color',s.line);localStorage.setItem('h3-h3-opacity',String(Math.round(s.opacity*100)))};
 const updateDataColor=(key:string,value:any)=>{setDataStyle('custom');localStorage.setItem('h3-data-style','custom');setColors((c:any)=>{const next={...c,[key]:value};localStorage.setItem(key==='entity'?'h3-entity-color':key==='fill'?'h3-h3-color':key==='line'?'h3-h3-line-color':'h3-h3-opacity',key==='opacity'?String(Math.round(value*100)):value);return next})};
 const [ingMode,setIngMode]=useState<'file'|'draw'>('file'),[ingName,setIngName]=useState(''),[ingRes,setIngRes]=useState(Number(localStorage.getItem('h3-ingestion-resolution')||11)),[autoValidate,setAutoValidate]=useState(localStorage.getItem('h3-auto-validation')!=='false'),[ingData,setIngData]=useState<FeatureCollection|null>(null),[preview,setPreview]=useState<any>(null);
 const [attrRows,setAttrRows]=useState<Array<{key:string;type:string;value:string}>>([]);
 const attrObject=()=>{const o:any={};for(const a of attrRows){const k=a.key.trim();if(!k)continue;try{if(a.type==='number')o[k]=Number(a.value);else if(a.type==='boolean')o[k]=a.value==='true';else if(a.type==='array'||a.type==='object')o[k]=JSON.parse(a.value);else o[k]=a.value}catch{throw Error('Attribute '+k+' มีค่าไม่ถูกต้อง')}}return o};
 const addAttr=()=>setAttrRows(a=>[...a,{key:'',type:'string',value:''}]);
 const updateAttr=(i:number,k:string,v:string)=>{setPreview(null);setAttrRows(a=>a.map((x,n)=>n===i?{...x,[k]:v}:x))};
 const toastTimer=useRef<number|null>(null);
 const notify=(x:string)=>{setToast(x);if(toastTimer.current)window.clearTimeout(toastTimer.current);toastTimer.current=window.setTimeout(()=>setToast(''),4000)};
 const refresh=useCallback(async()=>{try{const r=await apiFetch(API+'/ingestion/datasets');const d=await r.json();if(!r.ok)throw Error(d.detail||'Dataset load failed');setDatasets(Array.isArray(d.datasets)?d.datasets:[])}catch(e){notify(e instanceof Error?e.message:'API unavailable')}},[]);
 useEffect(()=>{refresh()},[refresh]);
 useEffect(()=>{if(page==='datasets'||page==='dashboard')refresh()},[page,refresh]);
 const load=useCallback(async(name:string)=>{
  const seq=++loadSeq.current;
  const target=String(name||'').trim();
  if(!target)return;
  let m:Dataset|undefined=datasets.find(x=>x.dataset===target);
  if(!m){try{const rr=await apiFetch(API+'/ingestion/datasets');const dd=await rr.json();const list:Dataset[]=Array.isArray(dd.datasets)?dd.datasets:[];if(seq!==loadSeq.current)return;setDatasets(list);m=list.find(x=>x.dataset===target)}catch{m=undefined}}
  if(seq!==loadSeq.current)return;
  if(!m){notify('ไม่พบ Dataset: '+target);return}
  setDataset(m);setResolution(Number(localStorage.getItem('h3-default-resolution')||m.h3_resolution));setResultOpen(false);setResults([]);
  try{
   const r=await apiFetch(API+'/ingestion/dataset/h3?dataset='+encodeURIComponent(target)+'&resolution='+m.h3_resolution);const d=await r.json();if(!r.ok)throw Error(d.detail||'H3 load failed');
   if(seq!==loadSeq.current)return;
   const hs:string[]=uniq(((d.h3||[]) as unknown[]).filter((x):x is string=>typeof x==='string'&&x.length>0));
   const es=(d.entity_h3||[]).map((x:any)=>{try{const [lat,lng]=h3.cellToLatLng(x.h3_index);return {entity_id:x.entity_id,latitude:lat,longitude:lng,h3_index:x.h3_index,properties:x.properties||{}}}catch{return null}}).filter((x:any):x is Entity=>x!==null);
   setEntities(es);setCells(hs);setBoundaryParts((d.boundary_parts||[]));
   try{const ar=await apiFetch(API+'/analytics/h3?dataset='+encodeURIComponent(target)+'&resolution='+m.h3_resolution+'&limit=50000').then(x=>x.json());if(seq===loadSeq.current)setAnalyticsRows(ar.rows||[])}catch{if(seq===loadSeq.current)setAnalyticsRows([])}
   const b=h3Bounds(hs);if(b&&seq===loadSeq.current)mapRef.current?.fitBounds(b as any,{padding:{top:90,bottom:90,left:360,right:60},maxZoom:15,duration:700});
   if(seq===loadSeq.current)notify('โหลด H3 '+hs.length.toLocaleString()+' cells ของ '+target);
  }catch(e){if(seq===loadSeq.current)notify(e instanceof Error?e.message:'H3 load failed')}
 },[datasets]);
 useEffect(()=>{if(page==='map'&&dataset&&cells.length===0)load(dataset.dataset)},[page,dataset,cells.length,load]);
 const entityMeta=useMemo(()=>new globalThis.Map(entities.map((e:any)=>[Number(e.entity_id),e.properties||{}])),[entities]);
 useEffect(()=>{const worker=new Worker(new URL('./workers/h3.worker.ts',import.meta.url),{type:'module'});h3Worker.current=worker;worker.onmessage=(e)=>setWorkerDisplay((e.data||[]).map((x:any)=>({...x,properties:entityMeta.get(Number(x.entity_id))||{}})));return()=>{worker.terminate();h3Worker.current=null}},[entityMeta]);
 useEffect(()=>{if(!h3Worker.current||!boundaryParts.length){setWorkerDisplay([]);return}h3Worker.current.postMessage({parts:boundaryParts,targetRes:resolution})},[boundaryParts,resolution]);
 const display=useMemo(()=>workerDisplay.length?workerDisplay:boundaryParts.length?displayCellsFromBoundary(boundaryParts,resolution,entityMeta):uniq(cells.flatMap(c=>{try{const r=h3.getResolution(c);return resolution===r?[{hex:c,entity_id:undefined,properties:{}}]:resolution<r?[{hex:h3.cellToParent(c,resolution),entity_id:undefined,properties:{}}]:h3.cellToChildren(c,resolution).map((x:string)=>({hex:x,entity_id:undefined,properties:{}}))}catch{return[]}})),[workerDisplay,boundaryParts,cells,resolution,entityMeta]);
 const analyticsMap=useMemo(()=>new globalThis.Map<string,any>(analyticsRows.map(x=>[x.h3_index,x])),[analyticsRows]);
 const analyticsMax=useMemo(()=>{if(analyticsMode==='entity_count')return Math.max(0,...analyticsRows.map(x=>Number(x.entity_count)||0));if(analyticsMode==='coverage')return Math.max(0,...analyticsRows.map(x=>Number(x.polygon_coverage??x.avg_cell_coverage)||0));return 0},[analyticsRows,analyticsMode]);
 const layers=useMemo(()=>[
  new H3HexagonLayer({id:'h3-gpu',data:display,pickable:true,highPrecision:'auto',filled:true,wireframe:extruded3d,extruded:extruded3d,elevationScale:1,
   getHexagon:(d:any)=>d.hex,getElevation:()=>height3d,getFillColor:(d:any)=>{const a=analyticsMap.get(d.hex);const value=analyticsMode==='entity_count'?Number(a?.entity_count)||0:Number(a?.polygon_coverage??a?.avg_cell_coverage)||0;const factor=analyticsMode==='off'||analyticsMax<=0?1:.35+.65*Math.min(1,value/analyticsMax);const c=rgb(colors.fill);return[Math.round(c[0]*factor),Math.round(c[1]*factor),Math.round(c[2]*factor),Math.round(colors.opacity*255)] as any},getLineColor:()=>[...rgb(colors.line),255] as any,lineWidthMinPixels:1,visible:h3Visible,
   onHover:(i:any)=>setHoverInfo(i.object?{object:i.object,x:i.x,y:i.y}:null),onClick:(i:any)=>i.object&&(setResults([{...i.object,source:'H3HexagonLayer'}]),setResultOpen(true))}),
  new ScatterplotLayer({id:'entity-gpu',data:entities,pickable:true,getPosition:(d:any)=>[d.longitude,d.latitude],getRadius:45,radiusMinPixels:4,radiusMaxPixels:9,getFillColor:()=>[...rgb(colors.entity),230] as any,visible:entityVisible,
   onClick:(i:any)=>i.object&&(setResults([{...i.object,source:'EntityMarker'}]),setResultOpen(true))}),
  new GeoJsonLayer({id:'query-result',data:results.length?{type:'FeatureCollection',features:results.filter(x=>x.geometry)}:undefined,filled:true,stroked:true,getFillColor:[37,99,235,45],getLineColor:[37,99,235,220],getLineWidth:2})
 ],[display,entities,colors,h3Visible,entityVisible,results,extruded3d,height3d,analyticsMap,analyticsMode,analyticsMax]);
 const loadViewport=useCallback(async()=>{if(!dataset||!mapRef.current)return;const b=mapRef.current.getBounds();try{const qs=new URLSearchParams({dataset:dataset.dataset,resolution:String(dataset.h3_resolution),min_lat:String(b.getSouth()),min_lng:String(b.getWest()),max_lat:String(b.getNorth()),max_lng:String(b.getEast()),limit:'100000'});const r=await apiFetch(API+'/ingestion/dataset/viewport?'+qs);if(!r.ok)return;const d=await r.json();setCells(d.h3||[]);setBoundaryParts(d.boundary_parts||[]);const es=(d.entity_h3||[]).map((x:any)=>{try{const [lat,lng]=h3.cellToLatLng(x.h3_index);return {entity_id:x.entity_id,latitude:lat,longitude:lng,h3_index:x.h3_index,properties:x.properties||{}}}catch{return null}}).filter(Boolean);setEntities(es as Entity[])}catch{}},[dataset]);
 const runQuery=async()=>{if(!dataset)return notify('เลือก Dataset ก่อน');const field=(document.getElementById('qField') as HTMLSelectElement).value,op=(document.getElementById('qOp') as HTMLSelectElement).value,value=(document.getElementById('qValue') as HTMLInputElement).value;
  const spatialType=(document.getElementById('qSpatial') as HTMLSelectElement).value,spatial:any={type:spatialType};if(spatialType==='nearby'){const c=mapRef.current?.getCenter();spatial.lat=c?.lat;spatial.lng=c?.lng;spatial.radius_m=Number((document.getElementById('qDistance') as HTMLInputElement).value||1000)}
  if(spatialType==='bbox'){const b=mapRef.current?.getBounds();spatial.min_lat=b?.getSouth();spatial.max_lat=b?.getNorth();spatial.min_lng=b?.getWest();spatial.max_lng=b?.getEast()}
  try{const r=await apiFetch(API+'/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({dataset:dataset.dataset,conditions:value?[{field,operator:op,value:field==='attribute'?JSON.parse(value):value}]:[],spatial,limit:5000})});const d=await r.json();if(!r.ok)throw Error(d.detail||'Query failed');setResults(d.features||[]);setResultOpen(true);notify('Query สำเร็จ '+(d.features||[]).length.toLocaleString())}catch(e){notify(e instanceof Error?e.message:'Query failed')}};
 const execute=async()=>{if(!ingData||!ingName)return notify('ใส่ Dataset Name และ source ก่อน');try{const attrs=attrObject();const payload={...ingData,features:ingData.features.map((f:any)=>({...f,properties:{...(f.properties||{}),...attrs}}))};const r=await apiFetch(API+'/ingestion/geojson/execute?resolution='+ingRes+'&dataset='+encodeURIComponent(ingName),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const d=await r.json();if(!r.ok)return notify(d.detail||'Execute failed');notify('Ingestion completed: '+d.dataset);await refresh();setPage('map')}catch(e){notify(e instanceof Error?e.message:'Attribute ไม่ถูกต้อง')}};
 const file=async(f:File)=>{try{setIngData(JSON.parse(await f.text()));setPreview(null);notify('โหลด GeoJSON แล้ว')}catch{setIngData(null);setPreview(null);notify('GeoJSON ไม่ถูกต้อง')}};
 const ready=useCallback((d:MapboxDraw|null)=>{drawRef.current=d},[]);
 const onDrawChange=useCallback((fc:FeatureCollection)=>{setIngData(fc);setPreview(null)},[]);
 const useDraw=()=>{const d=drawRef.current?.getAll();if(d?.features.length){setIngData(d);notify('รับข้อมูลจากแผนที่ '+d.features.length+' feature(s)')}else notify('ยังไม่มีข้อมูลที่วาด')};
 const style=BASEMAPS[basemap]?.url||BASEMAPS.liberty.url;
 const dataStyleOptions=Object.entries(DATA_COLOR_STYLES);
 return <div className={(dark?'app dark':'app')+(compact?' compact':'')+(animations?'':' noAnimations')} style={{'--accent':accent} as React.CSSProperties}><aside className="sidebar"><div className="brand"><b>H3</b><small>SPATIAL PLATFORM</small></div>
 <Nav id="map" p={page} set={setPage} icon={<MapOutlinedIcon/>} label="Map"/><Nav id="dashboard" p={page} set={setPage} icon={<DashboardOutlinedIcon/>} label="Overview"/><Nav id="datasets" p={page} set={setPage} icon={<StorageIcon/>} label="Datasets"/><Nav id="ingestion" p={page} set={setPage} icon={<CloudUploadOutlinedIcon/>} label="Ingestion"/><Nav id="analysis" p={page} set={setPage} icon={<AnalyticsOutlinedIcon/>} label="Analysis"/><div className="sideSpacer"/><Nav id="settings" p={page} set={setPage} icon={<SettingsOutlinedIcon/>} label="Settings"/><Nav id="health" p={page} set={setPage} icon={<CheckCircleOutlineIcon/>} label="System Health"/><div className="sideFoot">MapLibre<br/>deck.gl · H3</div></aside>
 <main className="workspace"><header className="topbar">
 <div className="topbarTitle"><span className="topbarKicker">H3 PLATFORM</span><b>{page==='map'?'Explore':page}</b></div>
 <div className="searchWrap"><SearchIcon fontSize="small"/><input list="datasetSearch" placeholder="Search dataset, H3 index or attribute…" onKeyDown={e=>{if(e.key==='Enter'){const q=e.currentTarget.value.trim();const m=datasets.find(x=>x.dataset.toLowerCase()===q.toLowerCase());if(m){setPage('map');load(m.dataset)}else if(q)notify('ไม่พบ Dataset: '+q)}}}/><datalist id="datasetSearch">{datasets.map(d=><option key={d.dataset} value={d.dataset}/>)}</datalist></div>
 <div className="topbarActions">
  <Tooltip title="Map statistics"><IconButton className="iconBtn" aria-label="Map statistics" onClick={()=>setStats(!stats)}><BarChartIcon fontSize="small"/></IconButton></Tooltip>
  <Tooltip title={dark?'Light map':'Dark map'}><IconButton className="iconBtn" aria-label="Toggle theme" onClick={()=>{setDark(!dark);localStorage.setItem('h3-theme',String(!dark))}}>{dark?<LightModeIcon fontSize="small"/>:<DarkModeIcon fontSize="small"/>}</IconButton></Tooltip>
 </div>
 </header>
 {page==='health'&&<Suspense fallback={<section className="page"><LinearProgress/></section>}><LazySystemHealth api={API} basemaps={BASEMAPS} refreshSeconds={healthRefresh}/></Suspense>}
 {page==='map'&&<Suspense fallback={<section className="mapPage"><LinearProgress/></section>}><LazyMapShell ref={mapRef} loadViewport={loadViewport} style={style} layers={layers} projection={projection} setProjection={(v)=>{setProjection(v);localStorage.setItem('h3-projection',v)}} mapControls={mapControls} visualKey={'visual-'+dataStyle+'-'+colors.entity+'-'+colors.fill+'-'+colors.line+'-'+colors.opacity+'-'+extruded3d+'-'+height3d+'-'+analyticsMode} dataset={dataset} resolution={resolution} displayCount={display.length} cells={cells} datasets={datasets} fitBounds={(m:any)=>{const b=h3Bounds(cells);if(b)m?.fitBounds(b as any,{padding:{top:100,bottom:80,left:340,right:40},maxZoom:15,duration:700})}} panel={<MapPanel {...{datasets,dataset,load,resolution,setResolution,h3Visible,setH3Visible,entityVisible,setEntityVisible,colors,setColors,dataStyle,applyDataStyle,updateDataColor,dataStyleOptions,basemap,setBasemap,height3d,setHeight3d,extruded3d,setExtruded3d,analyticsMode,setAnalyticsMode,analyticsRows,runQuery}}/>} hoverInfo={hoverInfo} stats={stats} mapStats={<div className="stats"><b>{dataset?.dataset||'—'}<small>Dataset</small></b><b>{dataset?.feature_count?.toLocaleString()||'—'}<small>Entities</small></b><b>Res {resolution}<small>Display</small></b><b>{display.length.toLocaleString()}<small>Visible cells</small></b></div>} results={results} resultOpen={resultOpen} setResultOpen={setResultOpen}/></Suspense>}
 {page==='ingestion'&&<section className="page ingestionPage">
  <PageHeader eyebrow="INGESTION" title="Ingestion Pipeline" description="GeoJSON / Draw → validate → preview H3 → execute into the spatial data model" actions={<Chip icon={<CheckCircleOutlineIcon/>} label="GeoJSON / Draw" variant="outlined"/>}/>
  <Stepper activeStep={preview?3:ingData?1:0} alternativeLabel className="pipelineStepper"><Step><StepLabel>Source</StepLabel></Step><Step><StepLabel>Validate</StepLabel></Step><Step><StepLabel>Preview H3</StepLabel></Step><Step><StepLabel>Execute</StepLabel></Step></Stepper>
  <div className="ingestionLayout">
   <SectionCard title="1 · Source" subtitle="Choose a source and define the dataset"><div className="sourceTabs"><Button variant={ingMode==='file'?'contained':'outlined'} startIcon={<CloudUploadOutlinedIcon/>} onClick={()=>setIngMode('file')}>File / GeoJSON</Button><Button variant={ingMode==='draw'?'contained':'outlined'} startIcon={<MapOutlinedIcon/>} onClick={()=>setIngMode('draw')}>Draw on map</Button></div>
    <div className="formGrid"><TextField size="small" label="Dataset name" placeholder="e.g. Bangkok_POI" value={ingName} onChange={e=>{setIngName(e.target.value);setPreview(null)}}/><FormControl size="small"><InputLabel>H3 source resolution</InputLabel><Select label="H3 source resolution" value={ingRes} onChange={e=>{const v=Number(e.target.value);setIngRes(v);setPreview(null);localStorage.setItem('h3-ingestion-resolution',String(v))}}>{Array.from({length:11},(_,i)=><MenuItem key={i} value={i+5}>Res {i+5}</MenuItem>)}</Select></FormControl></div>
    {ingMode==='file'?<div className="dropZone"><CloudUploadOutlinedIcon/><b>Drop GeoJSON here</b><span>GeoJSON / JSON · FeatureCollection</span><Button component="label" variant="outlined">Choose file<input hidden type="file" accept=".geojson,.json" onChange={e=>e.target.files?.[0]&&file(e.target.files[0])}/></Button>{ingData&&<Chip label={ingData.features.length+' feature(s) loaded'} color="success" size="small"/>}</div>:<><Suspense fallback={<LinearProgress/>}><LazyDrawMap style={style} ready={ready} onChange={onDrawChange}/></Suspense><div className="drawTools"><Button size="small" onClick={()=>drawRef.current?.changeMode('draw_point')}>Point</Button><Button size="small" onClick={()=>drawRef.current?.changeMode('draw_line_string')}>Line</Button><Button size="small" onClick={()=>drawRef.current?.changeMode('draw_polygon')}>Polygon</Button><Button size="small" onClick={()=>drawRef.current?.changeMode('simple_select')}>Select / Move</Button><Button size="small" onClick={()=>{const id=drawRef.current?.getSelectedIds?.()[0];if(id)drawRef.current?.changeMode('direct_select',{featureId:id});else notify('เลือก Feature ก่อน Edit vertices')}}>Edit vertices</Button><Button size="small" variant="contained" onClick={useDraw}>Use drawing</Button><Button size="small" color="error" onClick={()=>{drawRef.current?.deleteAll();setIngData({type:'FeatureCollection',features:[]});setPreview(null)}}>Clear</Button></div><div className="drawStatus">{ingData?.features.length||0} feature(s) · drawing is synced to the pipeline</div></>}
   </SectionCard>
   <SectionCard title="2 · Attributes" subtitle="Merge these properties into every source feature"><div className="attributeList">{attrRows.map((a,i)=><div className="attributeRow" key={i}><TextField size="small" label="Field" value={a.key} onChange={e=>updateAttr(i,'key',e.target.value)}/><FormControl size="small"><InputLabel>Type</InputLabel><Select label="Type" value={a.type} onChange={e=>updateAttr(i,'type',String(e.target.value))}><MenuItem value="string">String</MenuItem><MenuItem value="number">Number</MenuItem><MenuItem value="boolean">Boolean</MenuItem><MenuItem value="array">Array</MenuItem><MenuItem value="object">Object</MenuItem></Select></FormControl><TextField size="small" label="Value" value={a.value} onChange={e=>updateAttr(i,'value',e.target.value)} placeholder={a.type==='array'||a.type==='object'?'JSON value':'value'}/><IconButton color="error" onClick={()=>setAttrRows(x=>x.filter((_,n)=>n!==i))}>×</IconButton></div>)}</div><div className="buttonRow"><Button onClick={addAttr}>＋ Add attribute</Button><Button onClick={()=>setAttrRows([])}>Clear</Button></div>{attrRows.length>0&&<pre className="jsonBox">{(()=>{try{return JSON.stringify(attrObject(),null,2)}catch{return 'ตรวจสอบ Attribute value'}})()}</pre>}</SectionCard>
   <SectionCard title="3 · Preview & execute" subtitle="Validate the source before committing H3 coverage" actions={<div className="buttonRow"><Button startIcon={<PlayArrowIcon/>} onClick={async()=>{if(!ingData)return notify('เลือก source ก่อน');try{const attrs=attrObject();const payload={...ingData,features:ingData.features.map((f:any)=>({...f,properties:{...(f.properties||{}),...attrs}}))};const r=await apiFetch(API+'/ingestion/geojson/preview?resolution='+ingRes,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const d=await r.json();const hasErrors=!r.ok||Array.isArray(d.features)&&d.features.some((x:any)=>x.error);if(hasErrors){setPreview(null);notify(d.detail||'Preview failed: ตรวจสอบ geometry และ H3 workload')}else{setPreview(d);notify('Preview ready')}}catch(e){notify(e instanceof Error?e.message:'Attribute ไม่ถูกต้อง')}}}>Preview H3</Button><Button variant="contained" disabled={!ingData|| (autoValidate&&!preview)} startIcon={<CloudUploadOutlinedIcon/>} onClick={execute}>Execute pipeline</Button></div>}><div className="previewSummary">{preview?<Alert severity="success">Preview generated successfully. ตรวจสอบจำนวน Feature / H3 ก่อน Execute</Alert>:<Alert severity="info">ยังไม่มี Preview — โหลด source แล้วกด Preview H3</Alert>}</div><pre className="jsonBox large">{preview?JSON.stringify(preview,null,2):'Waiting for source'}</pre></SectionCard>
  </div>
 </section>}
 {page==='dashboard'&&<section className="page">
  <PageHeader eyebrow="OVERVIEW" title="Workspace overview" description="ภาพรวมของ spatial data platform และ dataset inventory" actions={<Button startIcon={<RefreshIcon/>} onClick={refresh}>Refresh</Button>}/>
  <div className="metricGrid"><Metric label="Datasets" value={datasets.length} detail="registered" icon={<StorageIcon/>}/><Metric label="Entities" value={datasets.reduce((n,d)=>n+Number(d.feature_count||0),0).toLocaleString()} detail="across datasets"/><Metric label="Boundary H3" value={datasets.reduce((n,d)=>n+Number(d.boundary_h3_count||0),0).toLocaleString()} detail="canonical cells"/><Metric label="Source resolutions" value={uniq(datasets.map(d=>d.h3_resolution)).length} detail="distinct levels"/></div>
  <div className="contentGrid"><SectionCard title="Recent datasets" subtitle="ล่าสุด · เปิดต่อได้จาก Map หรือ Datasets">{datasets.length?<Table size="small"><TableHead><TableRow><TableCell>Dataset</TableCell><TableCell>Type</TableCell><TableCell>Resolution</TableCell><TableCell>Entities</TableCell><TableCell>H3</TableCell></TableRow></TableHead><TableBody>{datasets.slice(0,5).map(d=><TableRow hover key={d.dataset_id} onClick={()=>{setPage('map');load(d.dataset)}} className="clickableRow"><TableCell><b>{d.dataset}</b></TableCell><TableCell>{d.data_type}</TableCell><TableCell>Res {d.h3_resolution}</TableCell><TableCell>{Number(d.feature_count||0).toLocaleString()}</TableCell><TableCell>{Number(d.boundary_h3_count||0).toLocaleString()}</TableCell></TableRow>)}</TableBody></Table>:<div className="emptyState"><StorageIcon/><span>No datasets yet</span></div>}</SectionCard>
   <SectionCard title="Spatial workflow" subtitle="Recommended path"><div className="workflow"><div><b>01</b><span>Ingest GeoJSON</span><small>Validate source geometry</small></div><div><b>02</b><span>Generate Boundary H3</span><small>Store canonical spatial index</small></div><div><b>03</b><span>Explore Res 5–15</span><small>Frontend fills display cells</small></div><div><b>04</b><span>Inspect JSON</span><small>Entity attributes stay attached</small></div></div></SectionCard>
  </div>
 </section>}
 {page==='datasets'&&<DatasetsPage datasets={datasets} refresh={refresh} onViewMap={(name)=>{setPage('map');load(name)}} onNew={()=>setPage('ingestion')} onNotify={notify} confirmDelete={confirmDelete}/>}
 {page==='analysis'&&<section className="page">
  <PageHeader eyebrow="ANALYSIS" title="Spatial analysis" description="วิเคราะห์ dataset ที่เลือกด้วย H3 resolution และ entity-count aggregation" actions={<Button startIcon={<MapOutlinedIcon/>} onClick={()=>setPage('map')}>Back to Map</Button>}/>
  <div className="metricGrid"><Metric label="Active dataset" value={dataset?.dataset||'—'} detail={dataset?'Res '+dataset.h3_resolution:'Select from Map'}/><Metric label="Display resolution" value={'Res '+resolution}/><Metric label="Visible H3 cells" value={display.length.toLocaleString()}/><Metric label="Analytics rows" value={analyticsRows.length.toLocaleString()}/></div>
  <SectionCard title="Analysis controls" subtitle="Keep analytical state aligned with the Map"><div className="analysisControls"><FormControl size="small"><InputLabel>Metric</InputLabel><Select label="Metric" value={analyticsMode} onChange={e=>{setAnalyticsMode(String(e.target.value));localStorage.setItem('h3-analytics-mode',String(e.target.value))}}><MenuItem value="off">No metric</MenuItem><MenuItem value="entity_count">Entity count</MenuItem></Select></FormControl><Button variant="contained" startIcon={<AnalyticsOutlinedIcon/>} onClick={async()=>{if(!dataset)return notify('เลือก Dataset บน Map ก่อน');await runQuery();notify('Analysis refreshed')}}>Refresh analysis</Button></div><div className="analysisNote"><InfoOutlinedIcon/><span>Analysis uses the same active dataset and H3 resolution as the Map. Change resolution on Map, then return here to keep context synchronized.</span></div></SectionCard>
  <SectionCard title="H3 results" subtitle="First 500 rows from the analytics API">{analyticsRows.length?<Table size="small"><TableHead><TableRow><TableCell>H3</TableCell><TableCell>Entity count</TableCell></TableRow></TableHead><TableBody>{analyticsRows.slice(0,500).map((r:any,i:number)=><TableRow key={i}><TableCell><code>{r.h3_index||'—'}</code></TableCell><TableCell>{Number(r.entity_count??r.count??0).toLocaleString()}</TableCell></TableRow>)}</TableBody></Table>:<div className="emptyState"><AnalyticsOutlinedIcon/><b>No analysis result</b><span>เลือก Entity count แล้ว refresh analysis</span></div>}</SectionCard>
 </section>}
 {page==='settings'&&<section className="page settingsPage">
  <PageHeader eyebrow="SYSTEM SETTINGS" title="System Settings" description="ปรับธีม แผนที่ H3 พฤติกรรม และค่าเริ่มต้นของ H3 Spatial Platform"/>
  <div className="settingsHero"><div><b>Workspace preferences</b><span>ค่าที่เปลี่ยนที่นี่จะถูกบันทึกไว้ในเครื่องนี้ และมีผลกับการใช้งานรอบถัดไป</span></div><Button variant="outlined" onClick={()=>{localStorage.clear();window.location.reload()}}>Reset to defaults</Button></div>
  <div className="settingsLayout">
   <div className="settingsMain">
    <SectionCard title="Appearance" subtitle="Theme, colors and workspace density"><div className="settingRows">
     <div className="settingRow"><div><b>Theme</b><small>Workspace color scheme</small></div><FormControl size="small" sx={{minWidth:160}}><Select value={dark?'dark':'light'} onChange={e=>{const v=String(e.target.value);const isDark=v==='dark';setDark(isDark);localStorage.setItem('h3-theme',v)}}><MenuItem value="light">Light</MenuItem><MenuItem value="dark">Dark</MenuItem></Select></FormControl></div>
     <div className="settingRow"><div><b>Accent color</b><small>Primary interface color</small></div><div className="accentChoices">{['#4264fb','#2563eb','#059669','#d97706','#7c3aed','#db2777'].map(c=><button key={c} className={accent===c?'selected':''} style={{background:c}} onClick={()=>{setAccent(c);localStorage.setItem('h3-accent',c)}} aria-label={c}/>)}</div></div>
     <div className="settingRow"><div><b>Compact mode</b><small>Reduce spacing in controls and tables</small></div><Switch checked={compact} onChange={e=>{setCompact(e.target.checked);localStorage.setItem('h3-compact',String(e.target.checked))}}/></div>
     <div className="settingRow"><div><b>Animations</b><small>Enable interface transitions</small></div><Switch checked={animations} onChange={e=>{setAnimations(e.target.checked);localStorage.setItem('h3-animations',String(e.target.checked))}}/></div>
    </div></SectionCard>
    <SectionCard title="Map defaults" subtitle="Default behavior for Map workspace"><div className="settingRows">
     <div className="settingRow"><div><b>Basemap</b><small>Initial map style</small></div><FormControl size="small" sx={{minWidth:180}}><Select value={basemap} onChange={e=>{const v=String(e.target.value);setBasemap(v);localStorage.setItem('h3-basemap',v)}}>{Object.entries(BASEMAPS).map(([k,v]:any)=><MenuItem key={k} value={k}>{v.name}</MenuItem>)}</Select></FormControl></div>
     <div className="settingRow"><div><b>Projection</b><small>Map camera projection</small></div><FormControl size="small" sx={{minWidth:180}}><Select value={projection} onChange={e=>{const v=String(e.target.value);setProjection(v);localStorage.setItem('h3-projection',v)}}><MenuItem value="flat">Flat · Mercator</MenuItem><MenuItem value="globe">Globe</MenuItem></Select></FormControl></div>
     <div className="settingRow"><div><b>Default H3 resolution</b><small>Initial display resolution</small></div><FormControl size="small" sx={{minWidth:180}}><Select value={resolution} onChange={e=>{const v=Number(e.target.value);setResolution(v);localStorage.setItem('h3-default-resolution',String(v))}}>{[5,8,11,12,13,14,15].map(v=><MenuItem key={v} value={v}>Res {v}</MenuItem>)}</Select></FormControl></div>
     <div className="settingRow"><div><b>Map controls</b><small>Navigation and location controls</small></div><Switch checked={mapControls} onChange={e=>{setMapControls(e.target.checked);localStorage.setItem('h3-map-controls',String(e.target.checked))}}/></div>
    </div></SectionCard>
    <SectionCard title="H3 visualization" subtitle="Default spatial display"><div className="settingRows">
     <div className="settingRow"><div><b>H3 grid</b><small>Show H3 cells by default</small></div><Switch checked={h3Grid} onChange={e=>{setH3Grid(e.target.checked);setH3Visible(e.target.checked);localStorage.setItem('h3-grid',String(e.target.checked))}}/></div>
     <div className="settingRow"><div><b>3D extrusion</b><small>Default vertical H3 rendering</small></div><Switch checked={extruded3d} onChange={e=>{setExtruded3d(e.target.checked);localStorage.setItem('h3-extruded-3d',String(e.target.checked))}}/></div>
     <div className="settingRow"><div><b>Default 3D height</b><small>Extrusion height in meters</small></div><div className="settingValue">{height3d.toLocaleString()} m</div></div>
    </div><Slider min={0} max={2000} step={10} value={height3d} onChange={(_,v)=>{const n=v as number;setHeight3d(n);localStorage.setItem('h3-height-3d',String(n))}}/></SectionCard>
    <SectionCard title="Ingestion defaults" subtitle="Defaults used when creating a new dataset"><div className="settingRows">
     <div className="settingRow"><div><b>Source format</b><small>First supported pipeline source</small></div><Chip label="GeoJSON" color="primary" variant="outlined"/></div>
     <div className="settingRow"><div><b>Default source resolution</b><small>H3 resolution for ingestion</small></div><FormControl size="small" sx={{minWidth:180}}><Select value={ingRes} onChange={e=>{const v=Number(e.target.value);setIngRes(v);setPreview(null);localStorage.setItem('h3-ingestion-resolution',String(v))}}>{[5,8,11,12,13,14,15].map(v=><MenuItem key={v} value={v}>Res {v}</MenuItem>)}</Select></FormControl></div>
     <div className="settingRow"><div><b>Auto validation</b><small>Require Preview H3 before Execute</small></div><Switch checked={autoValidate} onChange={e=>{setAutoValidate(e.target.checked);localStorage.setItem('h3-auto-validation',String(e.target.checked))}}/></div>
    </div></SectionCard>
   </div>
   <aside className="settingsSide">
    <SectionCard title="System behavior" subtitle="Runtime preferences"><div className="settingRows">
     <div className="settingRow"><div><b>Health refresh</b><small>Auto refresh interval</small></div><FormControl size="small" sx={{minWidth:110}}><Select value={healthRefresh} onChange={e=>{const v=Number(e.target.value);setHealthRefresh(v);localStorage.setItem('h3-health-refresh',String(v))}}><MenuItem value={0}>Off</MenuItem><MenuItem value={15}>15 sec</MenuItem><MenuItem value={30}>30 sec</MenuItem><MenuItem value={60}>60 sec</MenuItem></Select></FormControl></div>
     <div className="settingRow"><div><b>Confirm delete</b><small>Ask before deleting datasets</small></div><Switch checked={confirmDelete} onChange={e=>{setConfirmDelete(e.target.checked);localStorage.setItem('h3-confirm-delete',String(e.target.checked))}}/></div>
    </div></SectionCard>
    <SectionCard title="Platform" subtitle="Current application stack"><div className="runtimeList"><div><span>Version</span><b>1.2.0</b></div><div><span>Frontend</span><b>React + TypeScript + Vite</b></div><div><span>Map</span><b>MapLibre GL 6.11.2</b></div><div><span>Visualization</span><b>deck.gl 9.4 · H3</b></div><div><span>API</span><b>{API}</b></div></div></SectionCard>
    <SectionCard title="Reset" subtitle="Clear local workspace preferences"><Alert severity="warning" icon={<InfoOutlinedIcon/>}>Reset จะคืนค่า Theme, Basemap, H3 resolution และ UI preferences เป็นค่าเริ่มต้น</Alert><Button fullWidth sx={{mt:1}} variant="outlined" color="error" onClick={()=>{localStorage.clear();window.location.reload()}}>Clear all local settings</Button></SectionCard>
   </aside>
  </div>
 </section>}
 {toast&&<div className="toast" role="status" aria-live="polite">{toast}</div>}</main></div>
}
function Nav({id,p,set,icon,label}:{id:string;p:string;set:(x:string)=>void;icon:React.ReactNode;label:string}){return <Tooltip title={label} placement="right"><IconButton className={'nav '+(p===id?'active':'')} aria-label={label} onClick={()=>set(id)}>{icon}</IconButton></Tooltip>}
function MapPanel(p:any){
 const [tab,setTab]=useState(0);
 const resLabel=p.resolution<=5?'City':p.resolution<=8?'Neighborhood':p.resolution<=11?'Fine':'Detail';
 return <aside className="panel left">
  <div className="panelBrand"><div><b>MAP CONTROLS</b><small>Explore · analyze · style</small></div><LayersIcon fontSize="small"/></div>
  <div className="panelTabs"><button className={tab===0?'active':''} onClick={()=>setTab(0)}>Explore</button><button className={tab===1?'active':''} onClick={()=>setTab(1)}>Layers</button></div>
  {tab===0&&<>
   <div className="section primarySection"><div className="sectionTitle"><span>DATASET</span><em>{p.dataset?'ACTIVE':'SELECT'}</em></div>
    <Autocomplete size="small" options={p.datasets} value={p.dataset} onChange={(_,v)=>v&&p.load(v.dataset)} getOptionLabel={(x:any)=>x?.dataset||''} isOptionEqualToValue={(a:any,b:any)=>a.dataset===b.dataset} renderInput={(params)=><TextField {...params} placeholder="Choose dataset" />}/>
    {p.dataset&&<div className="datasetMeta"><strong>{p.dataset.dataset}</strong><span>{p.dataset.data_type||'Spatial dataset'} · source Res {p.dataset.h3_resolution}</span><div><i>{Number(p.dataset.feature_count||0).toLocaleString()} entities</i><i>{Number(p.dataset.boundary_h3_count||0).toLocaleString()} H3</i></div></div>}
   </div>
   <div className="section"><div className="sectionTitle"><span>H3 DISPLAY</span><em>RES {p.resolution}</em></div>
    <label className="sliderLabel"><span>Resolution</span><b>Res {p.resolution}</b></label>
    <Slider min={5} max={15} step={1} value={p.resolution} onChange={(_,v)=>p.setResolution(v as number)} valueLabelDisplay="auto" size="small"/>
    <div className="rangeScale"><span>5</span><span>8</span><span>11</span><span>15</span></div>
    <div className="resMeaning"><b>{resLabel}</b> · {p.resolution<=5?'coarse city overview':p.resolution<=8?'subdistrict / neighborhood':p.resolution<=11?'fine spatial analysis':'high-detail cells'}</div>
    <div className="visibilityRow"><FormControlLabel label="Entities" control={<Switch size="small" checked={p.entityVisible} onChange={e=>p.setEntityVisible(e.target.checked)} />} /><FormControlLabel label="H3 Cells" control={<Switch size="small" checked={p.h3Visible} onChange={e=>p.setH3Visible(e.target.checked)} />} /></div>
   </div>
   <Accordion className="muiAccordion"><AccordionSummary expandIcon={<ExpandMoreIcon fontSize="small"/>}><TuneIcon fontSize="small"/><span>Analysis</span><Chip size="small" label={p.analyticsRows.length.toLocaleString()+' cells'}/></AccordionSummary><AccordionDetails>
    <FormControl fullWidth size="small"><InputLabel>Metric</InputLabel><Select label="Metric" value={p.analyticsMode} onChange={e=>{p.setAnalyticsMode(e.target.value);localStorage.setItem('h3-analytics-mode',e.target.value)}}><MenuItem value="off">No metric</MenuItem><MenuItem value="entity_count">Entity count</MenuItem></Select></FormControl>
   </AccordionDetails></Accordion>
   <Accordion className="muiAccordion style3dAccordion"><AccordionSummary className="style3dSummary" expandIcon={<ExpandMoreIcon fontSize="small"/>}><div className="style3dTitle"><span className="style3dIcon"><TuneIcon fontSize="small"/></span><span><b>Style & 3D</b><small>Appearance & extrusion</small></span></div></AccordionSummary><AccordionDetails className="style3dDetails">
    <FormControl fullWidth size="small"><InputLabel>Color style</InputLabel><Select label="Color style" value={p.dataStyle} onChange={e=>p.applyDataStyle(e.target.value)}><MenuItem value="custom">Custom</MenuItem>{p.dataStyleOptions.map(([k,v]:any)=><MenuItem key={k} value={k}>{v.name}</MenuItem>)}</Select></FormControl>
    <div className="colorGrid"><label>Entity<input type="color" value={p.colors.entity} onChange={e=>p.updateDataColor('entity',e.target.value)}/></label><label>H3 Fill<input type="color" value={p.colors.fill} onChange={e=>p.updateDataColor('fill',e.target.value)}/></label><label>Border<input type="color" value={p.colors.line} onChange={e=>p.updateDataColor('line',e.target.value)}/></label></div>
    <label className="muiRange">Opacity <b>{Math.round(p.colors.opacity*100)}%</b><input type="range" min="0" max="1" step=".01" value={p.colors.opacity} onChange={e=>p.updateDataColor('opacity',+e.target.value)}/></label>
    <FormControlLabel label="3D Extrusion" control={<Switch size="small" checked={p.extruded3d} onChange={e=>{p.setExtruded3d(e.target.checked);localStorage.setItem('h3-extruded-3d',String(e.target.checked))}}/>}/>
    <label className="muiRange">Height <b>{p.height3d.toLocaleString()} m</b><input type="range" min="0" max="2000" step="10" value={p.height3d} onChange={e=>{const v=+e.target.value;p.setHeight3d(v);localStorage.setItem('h3-height-3d',String(v))}}/></label>
   </AccordionDetails></Accordion>
   <Accordion className="muiAccordion"><AccordionSummary expandIcon={<ExpandMoreIcon fontSize="small"/>}><SearchIcon fontSize="small"/><span>Query</span></AccordionSummary><AccordionDetails>
    <div className="queryStack">
     <FormControl fullWidth size="small"><InputLabel>Field</InputLabel><Select id="qField" label="Field" defaultValue="attribute"><MenuItem value="attribute">Attribute</MenuItem><MenuItem value="properties.category">Category</MenuItem><MenuItem value="properties.name">Name</MenuItem><MenuItem value="entity_id">Entity ID</MenuItem><MenuItem value="h3_index">H3 Index</MenuItem><MenuItem value="resolution">Resolution</MenuItem></Select></FormControl>
     <div className="queryInline"><FormControl size="small" sx={{minWidth:72}}><InputLabel>Op</InputLabel><Select id="qOp" label="Op" defaultValue="="><MenuItem value="=">=</MenuItem><MenuItem value="!=">!=</MenuItem><MenuItem value="contains">contains</MenuItem></Select></FormControl><TextField id="qValue" size="small" fullWidth placeholder="Value"/></div>
     <FormControl fullWidth size="small"><InputLabel>Spatial</InputLabel><Select id="qSpatial" label="Spatial" defaultValue="none"><MenuItem value="none">Current view</MenuItem><MenuItem value="nearby">Nearby</MenuItem><MenuItem value="bbox">Viewport BBox</MenuItem></Select></FormControl>
     <TextField id="qDistance" size="small" type="number" defaultValue="1000" label="Nearby radius (m)"/>
     <Button variant="contained" fullWidth onClick={p.runQuery}>Run Query</Button>
    </div>
   </AccordionDetails></Accordion>
   <Accordion className="muiAccordion"><AccordionSummary expandIcon={<ExpandMoreIcon fontSize="small"/>}><LayersIcon fontSize="small"/><span>Basemap</span></AccordionSummary><AccordionDetails>
    <FormControl fullWidth size="small"><InputLabel>Map style</InputLabel><Select label="Map style" value={p.basemap} onChange={e=>{p.setBasemap(e.target.value);localStorage.setItem('h3-basemap',e.target.value)}}>{Object.entries(BASEMAPS).map(([k,v]:any)=><MenuItem key={k} value={k}>{v.name}</MenuItem>)}</Select></FormControl>
   </AccordionDetails></Accordion>
  </>}
  {tab===1&&<div className="section layerList"><div className="layerItem"><span><span className="layerDot h3dot"/>H3 Cells</span><Switch size="small" checked={p.h3Visible} onChange={e=>p.setH3Visible(e.target.checked)}/></div><div className="layerItem"><span><span className="layerDot entitydot"/>Entities</span><Switch size="small" checked={p.entityVisible} onChange={e=>p.setEntityVisible(e.target.checked)}/></div><div className="layerItem muted"><span>Query result</span><Chip size="small" label="dynamic"/></div><div className="layerHint">Layer order follows the map rendering stack. Keep labels visible above dense H3 fills.</div></div>}
 </aside>
}function Check({t,v,s}:{t:string;v:boolean;s:(v:boolean)=>void}){return <label className="check"><input type="checkbox" checked={v} onChange={e=>s(e.target.checked)}/>{t}</label>}

import {useEffect,useRef,useState} from 'react';
import * as maplibregl from 'maplibre-gl';
import {Alert,Button,Chip,Paper} from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircle';
import 'maplibre-gl/dist/maplibre-gl.css';

maplibregl.setWorkerUrl('/maplibre-gl-worker.mjs');
const STYLES=[
 {id:'liberty',name:'Liberty',url:'https://tiles.openfreemap.org/styles/liberty'},
 {id:'bright',name:'Bright',url:'https://tiles.openfreemap.org/styles/bright'},
 {id:'positron',name:'Positron',url:'https://tiles.openfreemap.org/styles/positron'},
 {id:'dark',name:'Dark',url:'https://tiles.openfreemap.org/styles/dark'}
];
function StatusCard({label,ok,detail}:{label:string;ok:boolean;detail:string}){
 return <Paper variant="outlined" sx={{p:1.5,minWidth:180,flex:1}}><div style={{display:'flex',alignItems:'center',gap:8}}>{ok?<CheckCircleOutlineIcon color="success" fontSize="small"/>:<span style={{color:'crimson',fontWeight:800}}>×</span>}<b>{label}</b></div><small style={{color:'var(--muted)'}}>{detail}</small></Paper>;
}
export default function MapLibreV6Test(){
 const container=useRef<HTMLDivElement|null>(null);const map=useRef<maplibregl.Map|null>(null);
 const [style,setStyle]=useState(STYLES[0]);const [webgl2,setWebgl2]=useState(false);const [rendered,setRendered]=useState(false);const [worker,setWorker]=useState(true);const [shared,setShared]=useState(false);const [error,setError]=useState('');
 useEffect(()=>{
  if(!container.current)return;
  try{const canvas=document.createElement('canvas');setWebgl2(!!canvas.getContext('webgl2'))}catch{setWebgl2(false)}
  fetch('/maplibre-gl-worker.mjs').then(r=>{if(!r.ok)throw Error('Worker HTTP '+r.status);return r.text()}).then(t=>{setWorker(t.includes('maplibre-gl-shared.mjs'))}).catch(()=>setWorker(false));
  fetch('/maplibre-gl-shared.mjs').then(r=>setShared(r.ok)).catch(()=>setShared(false))
  try{const m=new maplibregl.Map({container:container.current,style:style.url,center:[100.5018,13.7563],zoom:10});map.current=m;
   m.addControl(new maplibregl.NavigationControl({showZoom:true,showCompass:true,visualizePitch:true}),'top-right');
   m.on('load',()=>setRendered(true));m.on('error',e=>{const msg=String(e?.error?.message||'MapLibre runtime error');setError(msg);if(msg.toLowerCase().includes('worker'))setWorker(false)});
   return()=>{m.remove();map.current=null};
  }catch(e){setError(e instanceof Error?e.message:String(e))}
 },[]);
 useEffect(()=>{if(!map.current)return;setRendered(false);setError('');map.current.setStyle(style.url);map.current.once('load',()=>setRendered(true))},[style]);
 return <section className="page" style={{height:'calc(100vh - 64px)',display:'flex',flexDirection:'column',gap:12}}>
  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:16,flexWrap:'wrap'}}><div><div style={{fontSize:12,fontWeight:700,letterSpacing:1}}>MAPLIBRE V6 TEST</div><h2 style={{margin:'4px 0'}}>MapLibre 6.11.2 Test</h2><div style={{fontSize:13,color:'var(--muted)'}}>Standalone runtime test for WebGL2, Worker, Basemap and rendering.</div></div><div style={{display:'flex',gap:6,flexWrap:'wrap'}}>{STYLES.map(s=><Button key={s.id} size="small" variant={style.id===s.id?'contained':'outlined'} onClick={()=>setStyle(s)}>{s.name}</Button>)}</div></div>
  <div style={{display:'flex',gap:8,flexWrap:'wrap'}}><StatusCard label="WebGL2" ok={webgl2} detail={webgl2?'Available':'Unavailable'}/><StatusCard label="MapLibre 6" ok={true} detail="6.11.2"/><StatusCard label="Worker" ok={worker} detail={worker?'/maplibre-gl-worker.mjs + shared import':'Worker dependency error'}/><StatusCard label="Shared Module" ok={shared} detail={shared?'/maplibre-gl-shared.mjs HTTP 200':'HTTP error'}/><StatusCard label="Basemap / Render" ok={rendered} detail={rendered?'Loaded and rendered':'Waiting for map load'}/></div>
  {error&&<Alert severity="error">{error}</Alert>}
  <Paper variant="outlined" sx={{position:'relative',flex:1,minHeight:360,overflow:'hidden',borderRadius:2}}><div ref={container} style={{position:'absolute',inset:0}}/><Chip label={'MapLibre 6.11.2 · '+style.name} size="small" sx={{position:'absolute',top:12,left:12,zIndex:2}}/></Paper>
 </section>;
}

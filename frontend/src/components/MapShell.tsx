import {forwardRef,ReactNode,useEffect,useImperativeHandle,useRef,useState} from 'react';
import * as maplibregl from 'maplibre-gl';
import {MapLibreOverlay} from '@deck.gl/maplibre';
import {Tooltip,IconButton,Chip} from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import PublicIcon from '@mui/icons-material/Public';
import {Results} from './ui';
import * as h3 from 'h3-js';
import 'maplibre-gl/dist/maplibre-gl.css';

maplibregl.setWorkerUrl('/maplibre-gl-worker.mjs');

export type MapShellProps={
 style:any;loadViewport:()=>void;layers:any[];visualKey:string;dataset:any;resolution:number;projection?:string;setProjection?:(v:string)=>void;mapControls?:boolean;
 displayCount:number;cells:string[];datasets:any[];panel:ReactNode;hoverInfo:any;stats:boolean;
 results:any[];resultOpen:boolean;setResultOpen:(v:boolean)=>void;mapStats:ReactNode;
 fitBounds:(map:any)=>void
};

export const MapShell=forwardRef<any,MapShellProps>(function MapShell(p,ref){
 const container=useRef<HTMLDivElement|null>(null);
 const map=useRef<maplibregl.Map|null>(null);
 const overlay=useRef<MapLibreOverlay|null>(null);
 const globe=p.projection==='globe';

 useImperativeHandle(ref,()=>({
  zoomIn:()=>map.current?.zoomIn(),
  zoomOut:()=>map.current?.zoomOut(),
  resetNorthPitch:()=>map.current?.resetNorthPitch(),
  fitBounds:(bounds:any,options?:any)=>map.current?.fitBounds(bounds,options),
  getCenter:()=>map.current?.getCenter(),
  getZoom:()=>map.current?.getZoom()
 }),[]);
 useEffect(()=>{
  if(!container.current)return;

  const m=new maplibregl.Map({
   container:container.current,
   style:p.style,
   center:[100.5018,13.7563],
   zoom:10
  });
  map.current=m;

  if(p.mapControls!==false){
   m.addControl(new maplibregl.NavigationControl({showZoom:true,showCompass:true,visualizePitch:true}),'top-right');
   m.addControl(new maplibregl.GeolocateControl({
    positionOptions:{enableHighAccuracy:true,timeout:6000},
    trackUserLocation:false,
    showUserLocation:true,
    showAccuracyCircle:true
   }),'top-right');
   m.addControl(new maplibregl.FullscreenControl(),'top-right');
   m.addControl(new maplibregl.ScaleControl({unit:'metric',maxWidth:110}),'bottom-left');
  }

  const o=new MapLibreOverlay({interleaved:false,layers:p.layers});
  overlay.current=o;
  m.addControl(o);

  const onMoveEnd=()=>p.loadViewport();
  m.on('moveend',onMoveEnd);

  return()=>{
   m.off('moveend',onMoveEnd);
   overlay.current=null;
   m.remove();
   map.current=null;
  };
 },[]);

 useEffect(()=>{
  const m=map.current;
  if(!m)return;
  const apply=()=>m.setProjection({type:globe?'globe':'mercator'});
  if(m.isStyleLoaded())apply();
  else m.once('load',apply);
  return()=>{m.off('load',apply)};
 },[globe]);

 useEffect(()=>{
  if(map.current&&p.style)map.current.setStyle(p.style);
 },[p.style]);

 useEffect(()=>{
  if(!map.current||!overlay.current)return;
  overlay.current.setProps({layers:p.layers,interleaved:false});
  map.current.triggerRepaint();
 },[p.layers,p.visualKey]);

 return <section className="mapPage">
  <div ref={container} style={{position:'absolute',inset:0}}/>
  <div className="mapContext"><div><strong>{p.dataset?.dataset||'No dataset selected'}</strong><span>{p.dataset?('Res '+p.dataset.h3_resolution+' · '+Number(p.dataset.feature_count||0).toLocaleString()+' entities'):'Select a dataset to explore'}</span></div><div className="contextChips">{p.dataset&&<><Chip size="small" label={'H3 Res '+p.resolution}/><Chip size="small" label={p.displayCount.toLocaleString()+' cells'}/></>}</div></div>
  <div className="mapToolbar">
   <Tooltip title={globe?'Flat map':'Globe view'} placement="left"><IconButton onClick={()=>p.setProjection?.(globe?'flat':'globe')}><PublicIcon fontSize="small"/></IconButton></Tooltip>
   <Tooltip title="Fit dataset" placement="left"><IconButton onClick={()=>p.fitBounds(map.current)}><HomeIcon fontSize="small"/></IconButton></Tooltip>
  </div>
  {p.panel}
  {p.hoverInfo&&<div className="mapHover" style={{left:p.hoverInfo.x+14,top:p.hoverInfo.y+14}}><b>H3 CELL</b><code>{p.hoverInfo.object.hex}</code><span>Res {h3.getResolution(p.hoverInfo.object.hex)} · Entity {p.hoverInfo.object.entity_id??'—'}</span></div>}
  {p.stats&&p.mapStats}
  {p.resultOpen&&<Results data={p.results} close={()=>p.setResultOpen(false)}/>}
 </section>;
});

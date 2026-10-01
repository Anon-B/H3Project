import {forwardRef,ReactNode,useEffect} from 'react';
import {Map,useMap,useControl,NavigationControl,GeolocateControl,FullscreenControl,ScaleControl} from 'react-map-gl/maplibre';
import type {MapRef} from 'react-map-gl/maplibre';
import {MapLibreOverlay} from '@deck.gl/maplibre';
import {Tooltip,IconButton,Chip} from '@mui/material';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';
import HomeIcon from '@mui/icons-material/Home';
import ExploreIcon from '@mui/icons-material/Explore';
import {Results} from './ui';
import * as h3 from 'h3-js';
import 'maplibre-gl/dist/maplibre-gl.css';

function DeckGLOverlay({layers}:{layers:any[]}){const {current:map}=useMap();const overlay=useControl<MapLibreOverlay>(()=>new MapLibreOverlay({interleaved:true,layers}));useEffect(()=>{overlay.setProps({layers,interleaved:true});map?.triggerRepaint()},[overlay,layers,map]);return null}

export type MapShellProps={style:any;loadViewport:()=>void;layers:any[];visualKey:string;dataset:any;resolution:number;displayCount:number;cells:string[];datasets:any[];panel:ReactNode;hoverInfo:any;stats:boolean;results:any[];resultOpen:boolean;setResultOpen:(v:boolean)=>void;mapStats:ReactNode;fitBounds:(map:MapRef)=>void};
export const MapShell=forwardRef<MapRef,MapShellProps>(function MapShell(p,ref){
 return <section className="mapPage"><Map ref={ref} onMoveEnd={p.loadViewport} mapStyle={p.style} dragRotate touchZoomRotate touchPitch><NavigationControl position="top-right" showZoom showCompass visualizePitch/><GeolocateControl position="top-right" positionOptions={{enableHighAccuracy:true,timeout:6000}} trackUserLocation={false} showUserLocation showAccuracyCircle/><FullscreenControl position="top-right"/><ScaleControl position="bottom-left" unit="metric" maxWidth={110}/><DeckGLOverlay key={p.visualKey} layers={p.layers}/></Map>
 <div className="mapContext"><div><strong>{p.dataset?.dataset||'No dataset selected'}</strong><span>{p.dataset?('Res '+p.dataset.h3_resolution+' · '+Number(p.dataset.feature_count||0).toLocaleString()+' entities'):'Select a dataset to explore'}</span></div><div className="contextChips">{p.dataset&&<><Chip size="small" label={'H3 Res '+p.resolution}/><Chip size="small" label={p.displayCount.toLocaleString()+' cells'}/></>}</div></div>
 <div className="mapToolbar"><Tooltip title="Zoom in" placement="left"><IconButton onClick={()=>pRef(ref)?.zoomIn()}><ZoomInIcon fontSize="small"/></IconButton></Tooltip><Tooltip title="Zoom out" placement="left"><IconButton onClick={()=>pRef(ref)?.zoomOut()}><ZoomOutIcon fontSize="small"/></IconButton></Tooltip><Tooltip title="Reset north" placement="left"><IconButton onClick={()=>pRef(ref)?.resetNorthPitch()}><ExploreIcon fontSize="small"/></IconButton></Tooltip><Tooltip title="Fit dataset" placement="left"><IconButton onClick={()=>p.fitBounds(pRef(ref))}><HomeIcon fontSize="small"/></IconButton></Tooltip></div>
 {p.panel}{p.hoverInfo&&<div className="mapHover" style={{left:p.hoverInfo.x+14,top:p.hoverInfo.y+14}}><b>H3 CELL</b><code>{p.hoverInfo.object.hex}</code><span>Res {h3.getResolution(p.hoverInfo.object.hex)} · Entity {p.hoverInfo.object.entity_id??'—'}</span></div>}{p.stats&&p.mapStats}{p.resultOpen&&<Results data={p.results} close={()=>p.setResultOpen(false)}/>}</section>;
});
function pRef(ref:any){return ref?.current||null}

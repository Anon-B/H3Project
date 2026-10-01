import {lazy,Suspense} from 'react';
import {Map} from 'react-map-gl/maplibre';
import type {FeatureCollection} from 'geojson';
import {LinearProgress} from '@mui/material';
import 'maplibre-gl/dist/maplibre-gl.css';
const DrawBridge=lazy(()=>import('./DrawBridge'));
export default function DrawMap({style,ready,onChange}:{style:any;ready:(d:any)=>void;onChange:(fc:FeatureCollection)=>void}){return <div className="drawMap"><Map mapStyle={style} initialViewState={{longitude:100.5018,latitude:13.7563,zoom:11}} dragRotate touchZoomRotate><Suspense fallback={<LinearProgress/>}><DrawBridge ready={ready} onChange={onChange}/></Suspense></Map></div>}

import {useEffect} from 'react';
import {useMap} from 'react-map-gl/maplibre';
import MapboxDraw from 'maplibre-gl-draw';
import type {FeatureCollection} from 'geojson';
import 'maplibre-gl-draw/dist/mapbox-gl-draw.css';
export default function DrawBridge({ready,onChange}:{ready:(d:any)=>void;onChange:(fc:FeatureCollection)=>void}){const {current}=useMap();useEffect(()=>{const map=current as any;if(!map)return;let draw:any=null;let disposed=false;const sync=()=>{if(draw&&!disposed)onChange(draw.getAll() as FeatureCollection)};const attach=()=>{if(disposed||draw)return;draw=new MapboxDraw({displayControlsDefault:false,controls:{point:false,line_string:false,polygon:false,trash:false}});map.addControl(draw,'top-right');ready(draw);sync();for(const event of ['draw.create','draw.update','draw.delete','draw.combine','draw.uncombine'])map.on(event,sync)};if(map.loaded?.())attach();else map.once('load',attach);return()=>{disposed=true;for(const event of ['draw.create','draw.update','draw.delete','draw.combine','draw.uncombine']){try{map.off(event,sync)}catch{}}if(draw){try{map.removeControl(draw)}catch{}}ready(null);draw=null}},[current,ready,onChange]);return null}

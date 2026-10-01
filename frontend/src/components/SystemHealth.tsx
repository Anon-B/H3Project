import {useCallback,useEffect,useState} from 'react';
import {Alert,Button,Chip,LinearProgress,Paper} from '@mui/material';
import {apiFetch} from '../lib/api';
import RefreshIcon from '@mui/icons-material/Refresh';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import AccessTimeIcon from '@mui/icons-material/AccessTime';

type Check={key:string;label:string;group:string;ok:boolean;detail:string;ms?:number};

async function probe(url:string):Promise<{ok:boolean;detail:string;ms:number}>{
 const started=performance.now();
 try{
  const r=await apiFetch(url,{cache:'no-store'});
  const ms=Math.round(performance.now()-started);
  let detail='HTTP '+r.status;
  try{const d=await r.json();if(d?.status)detail=d.status+(d.redis!==undefined?' · Redis '+(d.redis?'OK':'DOWN'):'')}catch{}
  return {ok:r.ok,detail,ms};
 }catch(e){return {ok:false,detail:e instanceof Error?e.message:'Request failed',ms:Math.round(performance.now()-started)}}
}

function Row({c}:{c:Check}){
 return <div className="hcRow">
  <div className={c.ok?'hcDot ok':'hcDot bad'}>{c.ok?<CheckCircleIcon/>:<ErrorIcon/>}</div>
  <div className="hcName"><b>{c.label}</b><span>{c.detail}</span></div>
  <span className="hcMs">{c.ms!==undefined?c.ms+' ms':'—'}</span>
 </div>
}

function Group({title,desc,items}:{title:string;desc:string;items:Check[]}){
 const ok=items.length>0&&items.every(x=>x.ok);
 return <Paper variant="outlined" className="hcGroup">
  <div className="hcGroupHead">
   <div><div className="hcGroupTitle">{title}</div><div className="hcGroupDesc">{desc}</div></div>
   <span className={ok?'hcBadge good':'hcBadge fail'}>{ok?'ALL OK':items.filter(x=>!x.ok).length+' FAILED'}</span>
  </div>
  {items.map(c=><Row key={c.key} c={c}/>)}
 </Paper>
}

export default function SystemHealth({api,basemaps,refreshSeconds=30}:{api:string;basemaps:any;refreshSeconds?:number}){
 const [checks,setChecks]=useState<Check[]>([]);
 const [loading,setLoading]=useState(false);
 const [lastRun,setLastRun]=useState('');

 const run=useCallback(async()=>{
  setLoading(true);
  const out:Check[]=[];
  const add=async(key:string,label:string,group:string,url:string)=>{
   const r=await probe(url);out.push({key,label,group,ok:r.ok,detail:r.detail,ms:r.ms});
  };
  await add('api','API Health','Backend',api+'/health');
  await add('ready','API Readiness','Backend',api+'/ready');
  await add('metrics','API Metrics','Backend',api+'/metrics');

  const webgl=(()=>{try{return !!document.createElement('canvas').getContext('webgl2')}catch{return false}})();
  out.push({key:'webgl2',label:'WebGL2','group':'Runtime',ok:webgl,detail:webgl?'Available':'Unavailable'});
  const runtime=typeof BigInt!=='undefined';
  out.push({key:'runtime',label:'Browser Runtime','group':'Runtime',ok:runtime,detail:runtime?'JavaScript runtime OK':'Runtime check failed'});

  await add('worker','MapLibre Worker','Mapping','/maplibre-gl-worker.mjs');
  await add('shared','MapLibre Shared Module','Mapping','/maplibre-gl-shared.mjs');
  const base=await probe(basemaps.liberty.url);
  out.push({key:'basemap',label:'Basemap Service','group':'Mapping',ok:base.ok,detail:base.ok?'Liberty style reachable':'Basemap style unavailable',ms:base.ms});

  setChecks(out);setLastRun(new Date().toLocaleString());setLoading(false);
 },[api,basemaps]);

 useEffect(()=>{run();if(refreshSeconds<=0)return;const id=window.setInterval(run,refreshSeconds*1000);return()=>window.clearInterval(id)},[run,refreshSeconds]);

 const failed=checks.filter(x=>!x.ok).length;
 const passed=checks.length-failed;
 const overall=checks.length>0&&failed===0;
 const groups=[
  ['Backend','API & service endpoints'],
  ['Runtime','Browser & graphics'],
  ['Mapping','Map rendering services']
 ] as const;

 return <section className="page healthPage">
 <style>{`
  .healthPage{overflow:auto;background:#f8fafc!important;padding:24px 28px!important}
  .healthWrap{max-width:1180px;margin:0 auto}
  .hcTop{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:20px}
  .hcEyebrow{font-size:10px;font-weight:700;letter-spacing:1.4px;color:#64748b;margin-bottom:5px}
  .hcTitle{font-size:28px!important;margin:0!important;letter-spacing:-.6px}
  .hcSub{font-size:12px;color:#64748b;margin:6px 0 0}
  .hcActions{display:flex;gap:8px;align-items:center}
  .hcHero{border:1px solid #e2e8f0!important;border-radius:14px!important;padding:20px 22px;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;background:#fff}
  .hcHeroLeft{display:flex;align-items:center;gap:15px}
  .hcHeroIcon{width:48px;height:48px;border-radius:12px;display:grid;place-items:center;background:#ecfdf5}
  .hcHeroIcon svg{font-size:27px;color:#16a34a}
  .hcHeroIcon.bad{background:#fef2f2}.hcHeroIcon.bad svg{color:#dc2626}
  .hcHeroTitle{font-size:16px;font-weight:700}.hcHeroText{font-size:11px;color:#64748b;margin-top:3px}
  .hcHeroStats{display:flex;gap:28px}.hcStat strong{display:block;font-size:22px}.hcStat span{font-size:10px;color:#64748b}
  .hcGrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
  .hcGroup{border-radius:12px!important;overflow:hidden;background:#fff}
  .hcGroupHead{padding:16px 17px 13px;border-bottom:1px solid #eef2f6;display:flex;justify-content:space-between;gap:8px}
  .hcGroupTitle{font-size:13px;font-weight:700}.hcGroupDesc{font-size:10px;color:#94a3b8;margin-top:3px}
  .hcBadge{font-size:9px;font-weight:700;letter-spacing:.3px;padding:4px 7px;border-radius:5px;height:max-content;white-space:nowrap}
  .hcBadge.good{color:#15803d;background:#f0fdf4}.hcBadge.fail{color:#b91c1c;background:#fef2f2}
  .hcRow{display:grid;grid-template-columns:25px 1fr auto;align-items:center;gap:8px;padding:11px 17px;border-bottom:1px solid #f1f5f9;min-height:55px}
  .hcRow:last-child{border-bottom:0}
  .hcDot{width:22px;height:22px;border-radius:50%;display:grid;place-items:center}.hcDot svg{font-size:16px}.hcDot.ok{color:#16a34a;background:#f0fdf4}.hcDot.bad{color:#dc2626;background:#fef2f2}
  .hcName b{display:block;font-size:11px;font-weight:600}.hcName span{display:block;font-size:10px;color:#94a3b8;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .hcMs{font-size:10px;color:#94a3b8;font-variant-numeric:tabular-nums}
  .statusLegend{display:flex;gap:18px;align-items:center;padding:0 2px 10px;color:#64748b;font-size:10px}
  .legendDot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:5px}.legendDot.good{background:#16a34a}.legendDot.warn{background:#f59e0b}.legendDot.bad{background:#dc2626}
  .statusTable{border-radius:12px!important;overflow:hidden;background:#fff}
  .statusTableTitle{display:flex;justify-content:space-between;align-items:center;padding:17px 19px;border-bottom:1px solid #e2e8f0}
  .statusTableTitle b{display:block;font-size:14px}.statusTableTitle span{display:block;color:#94a3b8;font-size:10px;margin-top:3px}.statusTableTitle .updated{color:#64748b;margin:0}
  .statusHead,.statusRow{display:grid;grid-template-columns:1fr 150px 100px;align-items:center}
  .statusHead{padding:8px 19px;background:#f8fafc;color:#94a3b8;font-size:9px;font-weight:700;letter-spacing:.5px}
  .statusRow{min-height:60px;padding:8px 19px;border-top:1px solid #f1f5f9}
  .component{display:flex;align-items:center;gap:10px}.component b{display:block;font-size:11px;font-weight:600}.component small{display:block;font-size:9px;color:#94a3b8;margin-top:3px}.serviceDot{width:8px;height:8px;border-radius:50%;flex:none}.serviceDot.good{background:#16a34a}.serviceDot.bad{background:#dc2626}
  .statusGood{font-size:10px;color:#15803d;font-weight:600}.statusBad{font-size:10px;color:#b91c1c;font-weight:600}.response{font-size:10px;color:#64748b;text-align:right;font-variant-numeric:tabular-nums}
  .statusSections{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;margin-top:14px;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;background:#e2e8f0}
  .statusSection{background:#fff;padding:12px 14px}.statusSection b{font-size:10px;display:block}.statusSection span{display:block;font-size:9px;color:#94a3b8;margin-top:2px}.statusSection strong{display:block;font-size:10px;color:#15803d;margin-top:7px}
  .hcFooter{margin-top:14px;border-radius:12px!important;padding:14px 17px;background:#fff}
  .hcFooterTitle{font-size:11px;font-weight:700;margin-bottom:9px}.hcTech{display:flex;gap:6px;flex-wrap:wrap}.hcTech span{font-size:9px;color:#64748b;background:#f8fafc;border:1px solid #e2e8f0;padding:4px 7px;border-radius:5px}
  .hcLast{display:flex;align-items:center;gap:5px;font-size:10px;color:#64748b}
  @media(max-width:900px){.hcGrid{grid-template-columns:1fr}.hcTop{align-items:flex-start;gap:12px;flex-direction:column}.hcHero{align-items:flex-start;gap:18px;flex-direction:column}.hcHeroStats{gap:22px}.statusHead,.statusRow{grid-template-columns:1fr 110px 70px}.statusSections{grid-template-columns:1fr}.statusTableTitle{align-items:flex-start;gap:8px;flex-direction:column}}
 `}</style>
 <div className="healthWrap">
  <div className="hcTop">
   <div><div className="hcEyebrow">SYSTEM OPERATIONS</div><h2 className="hcTitle">System Health</h2><p className="hcSub">ภาพรวมสถานะระบบและ dependencies ที่สำคัญ</p></div>
   <div className="hcActions">
    {lastRun&&<div className="hcLast"><AccessTimeIcon sx={{fontSize:14}}/>{lastRun}</div>}
    <Button size="small" variant="outlined" startIcon={<RefreshIcon/>} onClick={run} disabled={loading}>Run check</Button>
   </div>
  </div>
  {loading&&<LinearProgress sx={{mb:1.5}}/>}
  {failed>0&&<Alert severity="warning" sx={{mb:1.5,fontSize:11}}>พบ {failed} รายการที่ตรวจไม่ผ่าน</Alert>}
  <Paper variant="outlined" className="hcHero">
   <div className="hcHeroLeft">
    <div className={overall?'hcHeroIcon':'hcHeroIcon bad'}>{overall?<CheckCircleIcon/>:<ErrorIcon/>}</div>
    <div><div className="hcHeroTitle">{checks.length===0?'Checking system…':overall?'All systems operational':'Attention required'}</div><div className="hcHeroText">{overall?'ทุก health check ผ่านการตรวจสอบแล้ว':'มีบาง service หรือ runtime component ที่ต้องตรวจสอบ'}</div></div>
   </div>
   <div className="hcHeroStats"><div className="hcStat"><strong>{passed}</strong><span>Healthy</span></div><div className="hcStat"><strong>{failed}</strong><span>Failed</span></div><div className="hcStat"><strong>{checks.length}</strong><span>Total</span></div></div>
  </Paper>
  <div className="statusLegend">
   <span><i className="legendDot good"/> Operational</span>
   <span><i className="legendDot warn"/> Attention</span>
   <span><i className="legendDot bad"/> Major issue</span>
  </div>
  <Paper variant="outlined" className="statusTable">
   <div className="statusTableTitle">
    <div><b>Services</b><span>Current service status</span></div>
    <span className="updated">Updated {lastRun||'—'}</span>
   </div>
   <div className="statusHead"><span>COMPONENT</span><span>STATUS</span><span>RESPONSE</span></div>
   {checks.map(c=><div className="statusRow" key={c.key}>
    <div className="component"><i className={c.ok?'serviceDot good':'serviceDot bad'}/><div><b>{c.label}</b><small>{c.group} · {c.detail}</small></div></div>
    <span className={c.ok?'statusGood':'statusBad'}>{c.ok?'Operational':'Degraded'}</span>
    <span className="response">{c.ms!==undefined?c.ms+' ms':'—'}</span>
   </div>)}
  </Paper>
  <div className="statusSections">
   {groups.map(([title,desc])=><div className="statusSection" key={title}><b>{title}</b><span>{desc}</span><strong>{checks.filter(c=>c.group===title&&c.ok).length}/{checks.filter(c=>c.group===title).length} operational</strong></div>)}
  </div>
  <Paper variant="outlined" className="hcFooter"><div className="hcFooterTitle">System stack</div><div className="hcTech"><span>FastAPI</span><span>PostgreSQL</span><span>PostGIS</span><span>Redis</span><span>MapLibre GL 6.11.2</span><span>WebGL2</span><span>H3</span><span>deck.gl</span></div></Paper>
 </div>
 </section>;
}

import * as React from 'react';
import type {ReactNode} from 'react';
import {Paper,Divider,IconButton,Tooltip,Chip} from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CloseIcon from '@mui/icons-material/Close';

export function PageHeader({eyebrow,title,description,actions}:{eyebrow:string;title:string;description:string;actions?:ReactNode}){
  return <div className="pageHeader modernHeader"><div><div className="pageEyebrow">{eyebrow}</div><h2>{title}</h2><p>{description}</p></div>{actions&&<div className="pageActions">{actions}</div>}</div>;
}
export function Metric({label,value,detail,icon}:{label:string;value:string|number;detail?:string;icon?:ReactNode}){
  return <Paper className="metricCard" variant="outlined"><div className="metricIcon">{icon}</div><div><strong>{value}</strong><span>{label}</span>{detail&&<small>{detail}</small>}</div></Paper>;
}
export function SectionCard({title,subtitle,children,actions}:{title:string;subtitle?:string;children:ReactNode;actions?:ReactNode}){
  return <Paper className="sectionCard" variant="outlined"><div className="sectionCardHead"><div><b>{title}</b>{subtitle&&<small>{subtitle}</small>}</div>{actions}</div><Divider/>{children}</Paper>;
}
export function Results({data,close}:{data:any[];close:()=>void}){
  const [copied,setCopied]=React.useState(false);
  const copy=async()=>{try{await navigator.clipboard.writeText(JSON.stringify(data.length===1?data[0]:data,null,2));setCopied(true);setTimeout(()=>setCopied(false),1500)}catch{}};
  return <aside className="panel results"><div className="panelHead"><div><b>INSPECTOR</b><small>{data.length.toLocaleString()} selected · JSON</small></div><div className="panelActions"><Tooltip title={copied?'Copied':'Copy JSON'}><IconButton onClick={copy}><ContentCopyIcon fontSize="small"/></IconButton></Tooltip><Tooltip title="Close inspector"><IconButton onClick={close}><CloseIcon fontSize="small"/></IconButton></Tooltip></div></div><div className="inspectorType"><Chip size="small" label="H3 / ENTITY"/> <span>Click another cell to replace selection</span></div><div className="resultList">{data.slice(0,500).map((x,i)=><div className="result" key={i}><pre>{JSON.stringify(x,null,2)}</pre></div>)}</div></aside>;
}

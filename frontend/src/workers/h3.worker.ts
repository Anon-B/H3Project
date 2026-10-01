import * as h3 from 'h3-js';

type Part={entity_id:number;resolution:number;rings:Record<string,{ring_type:string;h3:string[]}>};
self.onmessage=(event:MessageEvent)=>{
  const {parts,targetRes}=event.data as {parts:Part[];targetRes:number};
  const out=new Map<string,any>();
  const add=(entity_id:number,cell:string)=>out.set(entity_id+'|'+cell,{hex:cell,entity_id});
  const convert=(cells:string[],sourceRes:number,id:number)=>{
    for(const cell of cells){
      try{
        if(targetRes===sourceRes)add(id,cell);
        else if(targetRes<sourceRes)add(id,h3.cellToParent(cell,targetRes));
        else h3.cellToChildren(cell,targetRes).forEach(x=>add(id,x));
      }catch{}
    }
  };
  for(const part of parts||[]){
    const sourceRes=Number(part.resolution)||targetRes,id=Number(part.entity_id);
    const rings=Object.values(part.rings||{});
    const outer=rings.filter(r=>r.ring_type==='outer').flatMap(r=>r.h3||[]);
    const holes=rings.filter(r=>r.ring_type==='hole').flatMap(r=>r.h3||[]);
    const line=rings.filter(r=>r.ring_type==='line').flatMap(r=>r.h3||[]);
    const point=rings.filter(r=>r.ring_type==='none').flatMap(r=>r.h3||[]);
    if(outer.length){
      const filled=new Set<string>();
      try{
        for(const poly of h3.cellsToMultiPolygon(outer,true) as any[]){
          const loop=Array.isArray(poly?.[0])?[poly[0]]:poly;
          h3.polygonToCells(loop,targetRes,true).forEach(x=>filled.add(x));
        }
      }catch{}
      if(filled.size)filled.forEach(c=>add(id,c));else convert(outer,sourceRes,id);
    }else if(line.length)convert(line,sourceRes,id);
    else convert(point,sourceRes,id);
  }
  self.postMessage(Array.from(out.values()));
};

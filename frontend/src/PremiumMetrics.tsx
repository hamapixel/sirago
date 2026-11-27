import {useId} from 'react';
const colors=['#16836c','#d6a743','#839b9c','#ae6255'];
export function Donut({title,items,center}:{title:string;items:{label:string;value:number}[];center:string}){
 const id=useId();
 const values=items.map(i=>({...i,value:Number.isFinite(i.value)?Math.max(0,i.value):0}));
 const total=values.reduce((sum,i)=>sum+i.value,0);
 let offset=0;
 return <article className="panel premium-chart"><h3 id={id}>{title}</h3><div className="premium-chart-body"><div className="donut-wrap"><svg viewBox="0 0 120 120" role="img" aria-labelledby={id}><circle cx="60" cy="60" r="45" fill="none" stroke="#e6edeb" strokeWidth="15"/>{total>0&&values.map((v,i)=>{const length=v.value/total*100;const start=offset;offset+=length;return <circle key={v.label} cx="60" cy="60" r="45" fill="none" pathLength="100" stroke={colors[i%colors.length]} strokeWidth="15" strokeDasharray={length+' '+(100-length)} strokeDashoffset={25-start}/>})}</svg><div><strong>{total.toLocaleString('fr-FR')}</strong><small>{center}</small></div></div><div className="donut-legend">{values.map((v,i)=><div key={v.label}><i style={{background:colors[i%colors.length]}}/><span>{v.label}</span><strong>{v.value.toLocaleString('fr-FR')}</strong></div>)}</div></div>{!total&&<small>Aucune donnée pour cette période.</small>}</article>
}

import {useEffect,useState} from 'react';
import {Wallet,Download,FileSpreadsheet,Building2,History,Percent} from 'lucide-react';
import {priceText,dayText} from './travel-api';
import {localToday} from './search';
import {Pagination,SearchField,type ResultPage} from './listing';
import {rateText} from './commission-math';
import './commission.css';
import './financial-report.css';

type Period='today'|'week'|'month'|'custom';
type View='companies'|'commissions'|'settlements';
export type Summary={sandbox:number;local:number;commission:number;share:number;unallocated:number;settled:number;real:number};
type Row={id:number;name:string;city?:string;date?:string;reference?:string;route?:string;gross?:number;rate_bps?:number|null;amount?:number}&Partial<Summary>;
type Report=ResultPage<Row>&{summary:Summary;view:View};
const base='/api/v1/auth/supervision/finances/';
const dateKey=(d:Date)=>d.toISOString().slice(0,10);
export function financialDates(period:Exclude<Period,'custom'>,today=localToday()){
 const from=new Date(today+'T00:00:00Z'),to=new Date(from);
 if(period==='week'){from.setUTCDate(from.getUTCDate()-((from.getUTCDay()+6)%7));to.setTime(from.getTime());to.setUTCDate(to.getUTCDate()+6)}
 if(period==='month'){from.setUTCDate(1);to.setTime(from.getTime());to.setUTCMonth(to.getUTCMonth()+1,0)}
 return {from:dateKey(from),to:dateKey(to)};
}
const labels=[['sandbox','SasPay TEST'],['commission','BTDIGIT TEST'],['share','Part compagnies TEST'],['settled','Reversé TEST'],['unallocated','Non réparti TEST'],['local','Simulation locale'],['real','Recettes réelles']] as const;
export function FinancialMetrics({summary}:{summary:Summary}){return <div className="financial-metrics">{labels.map(([key,label])=><div key={key}><small>{label}</small><strong>{priceText(summary[key])}</strong></div>)}</div>}
export function FinancialRow({row:r,view,rank}:{row:Row;view:View;rank:number}){
 return <article className="commission-ledger-line"><div className="commission-range"><strong>{view==='companies'?rank+'. ':''}{r.name}</strong><strong>{priceText(view==='companies'?r.sandbox??0:view==='commissions'?r.gross??0:r.amount??0)}</strong></div>{view==='companies'?<><small>{r.city} · SasPay TEST</small><div className="financial-row-values">{labels.filter(([k])=>k!=='sandbox'&&k!=='real').map(([k,l])=><div key={k}><small>{l}</small><strong>{priceText(r[k]??0)}</strong></div>)}</div></>:<><small>{r.route?r.route+' · ':''}{r.date?dayText(r.date):''}</small><small className="commission-reference">{r.reference}</small>{view==='commissions'&&(r.rate_bps==null?<small>Taux non configuré</small>:<div className="commission-line-values"><div><small>Taux</small><strong>{rateText(r.rate_bps)}</strong></div><div><small>BTDIGIT</small><strong>{priceText(r.commission??0)}</strong></div><div><small>Compagnie</small><strong>{priceText(r.share??0)}</strong></div></div>)}</>}</article>
}
export default function FinancialReport({revision}:{revision:number}){
 const [period,setPeriod]=useState<Period>('month'),[dates,setDates]=useState(()=>financialDates('month')),[query,setQuery]=useState(''),[view,setView]=useState<View>('companies'),[page,setPage]=useState(1),[data,setData]=useState<Report|null>(null),[error,setError]=useState(''),[loading,setLoading]=useState(true);
 const valid=!!dates.from&&!!dates.to&&dates.from<=dates.to&&(Date.parse(dates.to)-Date.parse(dates.from))/86400000<=365;
 const filters=new URLSearchParams({date_from:dates.from,date_to:dates.to,q:query});
 useEffect(()=>{const c=new AbortController();setData(null);setError('');if(!valid){setLoading(false);return}setLoading(true);const timer=window.setTimeout(async()=>{try{const params=new URLSearchParams({date_from:dates.from,date_to:dates.to,q:query,view,page:String(page),page_size:'10'});const r=await fetch(base+'?'+params,{credentials:'same-origin',cache:'no-store',signal:c.signal});if(!r.ok)throw new Error('Rapport indisponible.');const d=await r.json() as Report;if(!c.signal.aborted)setData(d)}catch(e){if(!c.signal.aborted)setError(e instanceof Error?e.message:'Chargement impossible.')}finally{if(!c.signal.aborted)setLoading(false)}},180);return()=>{c.abort();window.clearTimeout(timer)}},[dates.from,dates.to,query,view,page,revision,valid]);
 function choose(p:Period){setPeriod(p);setPage(1);if(p!=='custom')setDates(financialDates(p))}
 return <section className="financial-space"><article className="panel commission-config"><div className="commission-heading"><Wallet size={22}/><h3>Rapport financier</h3></div><small>TEST · Hors frais SasPay · Dates de confirmation et de reversement</small><div className="financial-periods">{([['today','Aujourd’hui'],['week','Semaine'],['month','Mois'],['custom','Période']] as const).map(([p,l])=><button key={p} type="button" className="outline" aria-pressed={period===p} onClick={()=>choose(p)}>{l}</button>)}</div><div className="financial-dates"><label>Du<input className="commission-input" type="date" value={dates.from} onChange={e=>{setDates({...dates,from:e.target.value});setPeriod('custom');setPage(1)}}/></label><label>Au<input className="commission-input" type="date" value={dates.to} onChange={e=>{setDates({...dates,to:e.target.value});setPeriod('custom');setPage(1)}}/></label></div><SearchField value={query} onChange={v=>{setQuery(v);setPage(1)}} placeholder="Compagnie ou ville…"/>{!valid&&<small role="alert">Période de 366 jours maximum.</small>}{valid&&<div className="financial-exports"><a className="outline settlement-download" href={base+'pdf/?'+filters}><Download size={18}/> PDF</a><a className="outline settlement-download" href={base+'excel/?'+filters}><FileSpreadsheet size={18}/> Excel</a></div>}</article>{loading&&<small role="status">Chargement…</small>}{error&&<small role="alert">{error}</small>}{data&&<FinancialMetrics summary={data.summary}/>}<article className="panel commission-config"><div className="financial-tabs">{([{id:'companies',label:'Compagnies',Icon:Building2},{id:'commissions',label:'Commissions',Icon:Percent},{id:'settlements',label:'Reversements',Icon:History}] as const).map(({id,label,Icon})=><button key={id} className="outline" aria-pressed={view===id} onClick={()=>{setView(id);setPage(1)}}><Icon size={17}/>{label}</button>)}</div>{view==='companies'&&<small>Classement par ventes SasPay TEST</small>}{data&&data.view===view&&<>{data.items.map((r,i)=><FinancialRow key={r.id} row={r} view={view} rank={(page-1)*data.page_size+i+1}/>)}{!data.total&&<small>Aucun résultat.</small>}<Pagination page={page} size={data.page_size} total={data.total} onChange={setPage}/></>}</article></section>
}

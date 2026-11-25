import {useState} from 'react';
import {History,CheckCircle2,UserRound,RefreshCw} from 'lucide-react';
import {dayText,timeText} from './travel-api';
import {SearchField,Pagination,useCompanyList} from './listing';
type Entry={id:number;name:string;origin:string;destination:string;boarded_at:string;agent:string;category:string};
export default function BoardingHistory(){
 const [query,setQuery]=useState(''),[date,setDate]=useState(''),[page,setPage]=useState(1),[revision,setRevision]=useState(0);
 const {data,loading,error}=useCompanyList<Entry>('boarding/history/',query,page,revision,date);
 return <section className="history-premium"><header><span className="history-icon"><History size={22}/></span><div><h3>Historique des embarquements</h3><small>Journal de contrôle · TEST</small></div><button type="button" className="outline history-refresh" aria-label="Actualiser l’historique" onClick={()=>setRevision(x=>x+1)} disabled={loading}><RefreshCw size={18}/></button></header><SearchField value={query} onChange={v=>{setQuery(v);setPage(1)}} placeholder="Passager, trajet ou agent…"/><label className="history-date">Date d’embarquement<input type="date" value={date} onChange={e=>{setDate(e.target.value);setPage(1)}}/></label>
 {loading&&<p role="status">Chargement…</p>}{error&&<p className="auth-error" role="alert">{error}</p>}{data&&<><small>{data.total} embarquement(s) trouvé(s)</small>{data.items.length===0&&<div className="history-empty"><History size={27}/><strong>Aucun embarquement trouvé</strong><small>Essayez une autre recherche.</small></div>}{data.items.map(r=><article className="history-entry" key={r.id}><div className="history-person"><span className="history-icon"><UserRound size={19}/></span><div><strong>{r.name}</strong><small>{r.category} · {r.origin} → {r.destination}</small></div><span className="history-state"><CheckCircle2 size={14}/> Embarqué</span></div><div className="history-meta"><span>{dayText(r.boarded_at)} · {timeText(r.boarded_at)}</span><span>Agent : {r.agent}</span></div></article>)}<Pagination page={page} size={data.page_size} total={data.total} onChange={setPage}/></>}
 </section>
}

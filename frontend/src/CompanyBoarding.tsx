import {useRef,useState} from 'react';
import {ScanLine,CheckCircle2,UserRound,History} from 'lucide-react';
import {companyPost} from './company-api';
import {dayText,timeText} from './travel-api';
import './boarding.css';
import QRReader,{validTicketCode} from './QRReader';
export {validTicketCode} from './QRReader';
type Passenger={index:number;name:string;boarded_at:string|null};
export type BoardingTicket={code:string;origin:string;destination:string;starts_at:string;boarding_point:string;category:string;count:number;boarded:number;remaining:number;can_board:boolean;passengers:Passenger[]};
import BoardingHistory from './BoardingHistory';
import {SearchField,useLocalPage,matchesSearch,Pagination} from './listing';
export function BoardingResult({ticket:t,selected,onToggle,onAll,onValidate,busy}:{ticket:BoardingTicket;selected:number[];onToggle:(i:number)=>void;onAll:()=>void;onValidate:()=>void;busy:boolean}){
 const [query,setQuery]=useState('');
 const paging=useLocalPage(t.passengers.filter(p=>matchesSearch(query,p.name)),10);
 return <div className="boarding-result">
 <div className="boarding-recognized"><CheckCircle2 size={22}/><div><strong>Billet de test reconnu</strong><p>{t.origin} → {t.destination}</p><small>{dayText(t.starts_at)} · {timeText(t.starts_at)} · {t.boarding_point}</small></div></div>
 <div className="boarding-stats"><div><small>Passagers</small><strong>{t.count}</strong></div><div><small>Embarqués</small><strong>{t.boarded}</strong></div><div><small>Restants</small><strong>{t.remaining}</strong></div></div>
 <progress max={t.count} value={t.boarded} aria-label="Progression des embarquements"/>
 <div className="boarding-list-heading"><h3>Liste des passagers</h3>{t.remaining>0&&t.can_board&&<button type="button" className="outline" disabled={busy} onClick={onAll}>Tout sélectionner</button>}</div>
 {t.count>10&&<SearchField value={query} onChange={v=>{setQuery(v);paging.setPage(1)}} placeholder="Rechercher un passager…"/>}
 {paging.rows.map(p=><label className="boarding-passenger" key={p.index}><UserRound size={18}/><span><strong>{p.name}</strong><small>{t.category}{p.boarded_at?' · Déjà embarqué à '+timeText(p.boarded_at):''}</small></span><input type="checkbox" aria-label={p.name+(p.boarded_at?' déjà embarqué':'')} checked={!!p.boarded_at||selected.includes(p.index)} disabled={busy||!!p.boarded_at||!t.can_board} onChange={()=>onToggle(p.index)}/></label>)}
 {t.count>10&&<Pagination page={paging.page} size={paging.size} total={paging.total} onChange={paging.setPage}/>}
 {!t.can_board&&<p role="status">Départ indisponible ou terminé. Validation bloquée.</p>}
 {t.remaining===0?<p className="boarding-complete"><CheckCircle2 size={20}/> Tous les passagers sont déjà embarqués.</p>:<button type="button" className="primary" disabled={busy||!selected.length||!t.can_board} onClick={onValidate}>{busy?'Validation…':"Valider l’embarquement ("+selected.length+"/"+t.remaining+")"}</button>}
 </div>
}
export default function CompanyBoarding({company,verified}:{company:string;verified:boolean}){
 const [code,setCode]=useState(''),[ticket,setTicket]=useState<BoardingTicket|null>(null),[selected,setSelected]=useState<number[]>([]),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState(''),[history,setHistory]=useState(false);
 const pending=useRef(false);
 async function lookup(raw:string){
  if(pending.current||!verified)return;
  const value=raw.trim().toUpperCase();
  if(!validTicketCode(value)){setError('Référence TEST invalide.');return}
  pending.current=true;setBusy(true);setError('');setNotice('');setCode(value);setTicket(null);setSelected([]);
  try{setTicket(await companyPost<BoardingTicket>('boarding/lookup/',{code:value}))}catch(e){setError(e instanceof Error?e.message:'Billet introuvable.')}finally{pending.current=false;setBusy(false)}
 }
 async function validate(){
  if(!ticket||pending.current||!selected.length||!ticket.can_board)return;
  pending.current=true;setBusy(true);setError('');setNotice('');
  try{const result=await companyPost<BoardingTicket>('boarding/validate/',{code:ticket.code,passengers:selected});setTicket(result);setSelected([]);setNotice('Embarquement de test enregistré.');setHistory(false)}catch(e){setError(e instanceof Error?e.message:'Validation impossible.')}finally{pending.current=false;setBusy(false)}
 }
 return <section className="boarding-space"><header className="boarding-head"><div><h2>Contrôle des billets</h2><p>{company}</p></div><ScanLine size={24}/></header>
 <p className="boarding-test">Simulation — Aucun embarquement réel.</p>
 {!verified?<p className="panel">Ce contrôle est réservé aux compagnies validées.</p>:<div className="panel boarding-panel">
 {error&&<p role="alert" className="auth-error">{error}</p>}{notice&&<p role="status" className="boarding-complete">{notice}</p>}
 {ticket?<><BoardingResult ticket={ticket} selected={selected} onToggle={i=>setSelected(old=>old.includes(i)?old.filter(x=>x!==i):[...old,i])} onAll={()=>setSelected(ticket.passengers.filter(p=>!p.boarded_at).map(p=>p.index))} onValidate={validate} busy={busy}/><button type="button" className="outline" disabled={busy} onClick={()=>{setTicket(null);setCode('');setSelected([]);setNotice('');setError('')}}><ScanLine size={20}/> Scanner un autre billet</button></>:<>
 <QRReader busy={busy} code={code} onCode={setCode} onLookup={lookup} onError={setError}/></>}
 <button className="outline" type="button" disabled={busy} onClick={()=>setHistory(v=>!v)} aria-expanded={history}><History size={18}/> Historique des embarquements</button>
 {history&&<BoardingHistory/>}
 </div>}</section>
}

import {useEffect,useId,useRef,useState} from 'react';
import {ShieldCheck,History,X} from 'lucide-react';
import {authPost} from './auth-api';
import {Pagination} from './listing';
import {dayText} from './travel-api';
import './admin-operations.css';

export type AdminKind='companies'|'travelers'|'support';
type Detail={id:number;name?:string;city?:string;address?:string;registration_number?:string;owner?:string;active?:boolean;status?:string;reference?:string;subject?:string;category?:string;requester?:string;message?:string;reply?:string;updated_at?:string;created_at:string};
type Audit={id:number;actor:string;target_type:string;target_id:number;before:string;after:string;reason:string;created_at:string};
type AuditPage={items:Audit[];total:number;page_size:number;page:number};
const labels:Record<string,string>={PENDING:'En attente',VERIFIED:'Validée',REJECTED:'Refusée',SUSPENDED:'Suspendue',ACTIVE:'Actif',INACTIVE:'Inactif',OPEN:'Reçue',IN_PROGRESS:'En cours',RESOLVED:'Résolue',COMPANY:'Compagnie',TRAVELER:'Voyageur',SUPPORT:'Assistance'};
const transitions:Record<string,string[]>={PENDING:['VERIFIED','REJECTED'],REJECTED:['PENDING'],VERIFIED:['SUSPENDED'],SUSPENDED:['VERIFIED']};
export function choices(kind:AdminKind,d:Detail):string[]{
 if(kind==='companies')return transitions[d.status||'']||[];
 if(kind==='travelers')return [d.active?'INACTIVE':'ACTIVE'];
 return ['OPEN','IN_PROGRESS','RESOLVED'];
}
async function read<T>(path:string,signal:AbortSignal):Promise<T>{
 const r=await fetch('/api/v1/auth/supervision/'+path,{credentials:'same-origin',cache:'no-store',signal});
 const body=await r.json().catch(()=>null);
 if(!r.ok)throw new Error(body?.detail||'Données indisponibles.');
 return body as T;
}
export default function AdminOperations({kind,id,onSaved}:{kind:AdminKind;id:number;onSaved:()=>void}){
 const [open,setOpen]=useState(false),[detail,setDetail]=useState<Detail|null>(null),[target,setTarget]=useState(''),[reply,setReply]=useState(''),[reason,setReason]=useState(''),[confirm,setConfirm]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const node=useRef<HTMLDialogElement>(null),pending=useRef(false),title=useId();
 useEffect(()=>{if(!open)return;const c=new AbortController();setDetail(null);setError('');setReason('');setConfirm(false);
 read<Detail>(kind+'/'+id+'/',c.signal).then(d=>{if(c.signal.aborted)return;setDetail(d);setTarget(kind==='support'?d.status||'OPEN':'');setReply(d.reply||'')}).catch(e=>{if(!c.signal.aborted)setError(e.message)});
 return()=>c.abort()},[open,kind,id]);
 useEffect(()=>{if(open&&!node.current?.open)node.current?.showModal();if(!open&&node.current?.open)node.current.close()},[open]);
 const valid=!!detail&&!!target&&reason.trim().length>=5&&(kind!=='support'||(target!==detail.status||reply.trim()!==(detail.reply||''))&&(target!=='RESOLVED'||!!reply.trim()));
 async function save(){if(!detail||!valid||!confirm||pending.current)return;pending.current=true;setBusy(true);setError('');
 const values=kind==='companies'?{status:target,expected_status:detail.status}:kind==='travelers'?{active:target==='ACTIVE',expected_active:detail.active}:{status:target,reply,expected_updated_at:detail.updated_at};
 try{await authPost('supervision/'+kind+'/'+id,{...values,reason,confirm:true});setOpen(false);onSaved()}catch(e){setError(e instanceof Error?e.message:'Opération impossible.');setConfirm(false)}finally{pending.current=false;setBusy(false)}}
 return <><button type="button" className="outline" onClick={()=>setOpen(true)}>Ouvrir la fiche</button><dialog ref={node} className="admin-operation-dialog" aria-labelledby={title} onCancel={e=>{if(busy)e.preventDefault();else setOpen(false)}} onClose={()=>setOpen(false)}>
 <div className="admin-operation-head"><div><small>OPÉRATION SÉCURISÉE</small><h2 id={title}>{detail?.name||detail?.subject||'Fiche administrative'}</h2></div><button type="button" className="outline" aria-label="Fermer la fiche" disabled={busy} onClick={()=>setOpen(false)}><X size={20}/></button></div>
 {error&&<p role="alert" className="auth-error">{error}</p>}
 {!detail&&!error&&<p role="status">Chargement…</p>}
 {detail&&<><div className="admin-operation-info"><strong>{labels[detail.status||(detail.active?'ACTIVE':'INACTIVE')]}</strong>{detail.city&&<p>{detail.city} · {detail.address}</p>}{detail.registration_number&&<p>Immatriculation : {detail.registration_number}</p>}{detail.owner&&<p>Responsable : {detail.owner}</p>}{detail.requester&&<p>{detail.reference} · {detail.requester} · {detail.category}</p>}{detail.message&&<p className="admin-operation-message">{detail.message}</p>}</div>
 <label>Action<select value={target} disabled={busy} onChange={e=>{setTarget(e.target.value);setConfirm(false)}}>{kind!=='support'&&<option value="">Choisir une action</option>}{choices(kind,detail).map(v=><option key={v} value={v}>{labels[v]}</option>)}</select></label>
 {kind==='support'&&<label>Réponse au demandeur<textarea rows={5} maxLength={4000} value={reply} disabled={busy} onChange={e=>{setReply(e.target.value);setConfirm(false)}}/></label>}
 <label>Motif de l'action (journal interne)<textarea rows={3} maxLength={300} value={reason} disabled={busy} onChange={e=>{setReason(e.target.value);setConfirm(false)}}/></label><small>Ne saisissez aucun secret ou donnée bancaire dans le motif.</small>
 {kind==='travelers'&&target==='INACTIVE'&&<p>Les sessions du voyageur seront révoquées. Son mot de passe et son historique restent conservés.</p>}
 {kind==='companies'&&target==='SUSPENDED'&&<p>Les nouvelles réservations seront bloquées. Les réservations futures actives doivent être traitées auparavant.</p>}
 {!confirm?<button type="button" className="outline" disabled={!valid||busy} onClick={()=>setConfirm(true)}>Préparer la confirmation</button>:<div className="admin-operation-confirm"><ShieldCheck size={22}/><strong>Confirmer : {labels[target]}</strong><p>Cette action sera enregistrée dans l’historique administratif.</p><div><button type="button" className="outline" disabled={busy} onClick={()=>setConfirm(false)}>Annuler</button><button type="button" className="admin-operation-primary" disabled={busy||!valid} onClick={save}>{busy?'Enregistrement…':'Confirmer et enregistrer'}</button></div></div>}</>}
 </dialog></>
}
export function AdminActionHistory({revision}:{revision:number}){
 const [kind,setKind]=useState(''),[page,setPage]=useState(1),[data,setData]=useState<AuditPage|null>(null),[error,setError]=useState('');
 useEffect(()=>{const c=new AbortController();setData(null);setError('');read<AuditPage>('actions/?'+new URLSearchParams({kind,page:String(page),page_size:'10'}),c.signal).then(d=>{if(!c.signal.aborted)setData(d)}).catch(e=>{if(!c.signal.aborted)setError(e.message)});return()=>c.abort()},[kind,page,revision]);
 return <article className="panel super-list"><h3><History size={20}/> Historique des opérations</h3><small>Journal en lecture seule · compagnies, voyageurs et assistance.</small><label>Type d'opération<select value={kind} onChange={e=>{setKind(e.target.value);setPage(1)}}><option value="">Toutes</option>{['COMPANY','TRAVELER','SUPPORT'].map(v=><option key={v} value={v}>{labels[v]}</option>)}</select></label>{error&&<p role="alert" className="auth-error">{error}</p>}{!data&&!error&&<p role="status">Chargement…</p>}{data&&<>{data.items.length===0&&<p>Aucune opération enregistrée.</p>}{data.items.map(a=><article key={a.id} className="super-row admin-audit-row"><div><strong>{labels[a.target_type]} #{a.target_id}</strong><small>{labels[a.before]} → {labels[a.after]}</small><p>{a.reason}</p><small>{a.actor} · {dayText(a.created_at)} · {new Date(a.created_at).toLocaleTimeString('fr-FR',{timeZone:'Africa/Bamako'})}</small></div></article>)}<Pagination page={page} size={data.page_size} total={data.total} onChange={setPage}/></>}</article>
}

import {lazy,Suspense,useState,useEffect,useRef,type FormEvent} from 'react';
import {ScanLine,CalendarDays,Ticket,ShieldCheck,LogOut} from 'lucide-react';
import {authPost,type Account} from './auth-api';
import {companyGet,type Departure,type Page} from './company-api';
import {dayText,timeText} from './travel-api';
import CompanyManifest from './CompanyManifest';
import CompanyReservations from './CompanyReservations';
import './agents.css';
import './profile.css';
const Boarding=lazy(()=>import('./CompanyBoarding'));
type Tab='boarding'|'departures'|'reservations'|'security';
export default function CompanyAgentSpace({account,onLogout}:{account:Account;onLogout:()=>void}){
 const [tab,setTab]=useState<Tab>('boarding'),[id,setId]=useState<number|null>(null),[page,setPage]=useState(1),[revision,setRevision]=useState(0),[rows,setRows]=useState<Page<Departure>|null>(null),[loading,setLoading]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
 const [current,setCurrent]=useState(''),[password,setPassword]=useState(''),[confirmation,setConfirmation]=useState(''),[busy,setBusy]=useState(false);
 const pending=useRef(false);
 const clerk=account.company_role==='CLERK',verified=account.company?.status==='VERIFIED';
 useEffect(()=>{if(tab!=='departures'||id!==null||!verified)return;let active=true;setLoading(true);setRows(null);setError('');companyGet<Page<Departure>>('departures/?page='+page).then(r=>{if(active)setRows(r)}).catch(e=>{if(active)setError(e instanceof Error?e.message:'Départs indisponibles.')}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[tab,id,page,revision,verified]);
 function navigate(t:Tab){if(busy)return;setTab(t);setId(null);setError('');setNotice('');setCurrent('');setPassword('');setConfirmation('')}
 async function save(e:FormEvent){e.preventDefault();if(pending.current||password!==confirmation)return;pending.current=true;setBusy(true);setError('');setNotice('');try{await authPost('company/password',{current_password:current,password,password_confirmation:confirmation});setCurrent('');setPassword('');setConfirmation('');setNotice('Mot de passe modifié.')}catch(e){setError(e instanceof Error?e.message:'Modification impossible.')}finally{pending.current=false;setBusy(false)}}
 const nav=[{id:'boarding',label:'Scanner',Icon:ScanLine},{id:'departures',label:'Départs',Icon:CalendarDays},...(clerk?[{id:'reservations',label:'Réservations',Icon:Ticket} as const]:[]),{id:'security',label:'Sécurité',Icon:ShieldCheck}] as const;
 return <section className="agent-workspace"><header className="boarding-head"><div><h2>{account.company?.name||'SiraGo Pro'}</h2><p>{account.first_name} {account.last_name} · {clerk?'Guichetier':'Contrôleur'}</p></div><ShieldCheck size={23}/></header>
 {!verified?<article className="panel">Accès indisponible : contactez le responsable de votre compagnie.</article>:<><nav className="agent-workspace-nav" aria-label="Navigation agent">{nav.map(({id,label,Icon})=><button className="outline" key={id} type="button" aria-pressed={tab===id} onClick={()=>navigate(id)} disabled={busy}><Icon size={18}/>{label}</button>)}</nav>
 {tab==='boarding'&&<Suspense fallback={<p role="status">Chargement du scanner…</p>}><Boarding company={account.company?.name||'Ma compagnie'} verified={verified}/></Suspense>}
 {tab==='departures'&&(id!==null?<CompanyManifest id={id} onBack={()=>setId(null)}/>:<><div className="company-section-head"><h2>Départs et manifestes</h2><button className="outline" onClick={()=>setRevision(x=>x+1)} disabled={loading}>Actualiser</button></div>{loading&&<p role="status">Chargement…</p>}{error&&<p className="auth-error" role="alert">{error}</p>}{rows?.items.map(d=><article className="panel agent-departure" key={d.id}><strong>{d.origin} → {d.destination}</strong><p>{dayText(d.starts_at)} · {timeText(d.starts_at)} · {d.bus_name}</p><p>{d.capacity} places · {d.remaining??'—'} libres</p><button className="outline" onClick={()=>setId(d.id)}>Manifeste voyageurs</button></article>)}{rows?.items.length===0&&<p className="panel">Aucun départ.</p>}<div className="profile-dialog-actions"><button className="outline" disabled={loading||page===1} onClick={()=>setPage(p=>p-1)}>Précédent</button><button className="outline" disabled={loading||!rows?.has_next} onClick={()=>setPage(p=>p+1)}>Suivant</button></div></>)}
 {tab==='reservations'&&clerk&&<CompanyReservations/>}
 {tab==='security'&&<form className="panel profile-form" onSubmit={save}><h2>Modifier mon mot de passe</h2><label>Mot de passe actuel<input required type="password" autoComplete="current-password" maxLength={128} value={current} onChange={e=>setCurrent(e.target.value)} disabled={busy}/></label><label>Nouveau mot de passe<input required type="password" autoComplete="new-password" minLength={8} maxLength={128} value={password} onChange={e=>setPassword(e.target.value)} disabled={busy}/></label><label>Confirmer<input required type="password" autoComplete="new-password" maxLength={128} value={confirmation} onChange={e=>setConfirmation(e.target.value)} disabled={busy}/></label>{error&&<p className="auth-error" role="alert">{error}</p>}{notice&&<p className="profile-success" role="status">{notice}</p>}<button className="primary" disabled={busy||password!==confirmation}>Enregistrer</button></form>}
 </>}<button className="outline profile-logout" onClick={onLogout}><LogOut size={18}/> Déconnexion</button></section>
}

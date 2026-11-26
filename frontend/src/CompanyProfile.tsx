import {t as tr} from './i18n';
import {lazy,Suspense,useState,useEffect,useRef,type FormEvent,type ReactNode} from 'react';
import {ArrowLeft,BusFront,Building2,UserRound,ShieldCheck,Users,Bell,Headset,ChevronRight,LogOut,BadgeCheck} from 'lucide-react';
import {authPost,type Account} from './auth-api';
import {passwordValid} from './auth-validation';
import {validProfileName} from './profile-validation';
import './profile.css';
import './company-profile.css';
import CompanyAgents from './CompanyAgents';
import CompanyBrand,{BrandLogo,BrandCover} from './CompanyBrand';
import NotificationCenter from './NotificationCenter';
const SupportCenter=lazy(()=>import('./SupportCenter'));

type Page='home'|'company'|'responsible'|'password'|'agents'|'notifications'|'support';
type Details={name:string;city:string;address:string;registration_number:string};
const titles:Record<Page,string>={home:'Profil compagnie',company:'Informations de la compagnie',responsible:'Informations du responsable',password:'Sécurité du compte',agents:'Agents de la compagnie',notifications:'Notifications',support:'Assistance SiraGo'};
const statusLabels={VERIFIED:'Compagnie vérifiée',PENDING:'Validation en attente',REJECTED:'Validation refusée',SUSPENDED:'Compagnie suspendue'};
function Item({icon,label,detail,onClick}:{icon:ReactNode;label:string;detail:string;onClick:()=>void}){
 return <button type="button" className="profile-item" onClick={onClick}><span className="profile-icon">{icon}</span><span className="profile-item-copy"><strong>{label}</strong><small>{detail}</small></span><ChevronRight size={19}/></button>
}
export default function CompanyProfile({account,status,onUpdated,onLogout}:{account:Account;status?:NonNullable<Account['company']>['status'];onUpdated:(account:Account)=>void;onLogout:()=>void}){
 const [page,setPage]=useState<Page>('home'),[details,setDetails]=useState<Details|null>(null),[loading,setLoading]=useState(false),[revision,setRevision]=useState(0),[first,setFirst]=useState(account.first_name),[last,setLast]=useState(account.last_name);
 const [current,setCurrent]=useState(''),[password,setPassword]=useState(''),[confirmation,setConfirmation]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState(''),[logout,setLogout]=useState(false);
 const pending=useRef(false),dialog=useRef<HTMLDialogElement>(null);
 useEffect(()=>{if(!logout)return;if(dialog.current&&!dialog.current.open)dialog.current.showModal()},[logout]);
 useEffect(()=>{if(page!=='company')return;let active=true;setLoading(true);setDetails(null);setError('');fetch('/api/v1/auth/company/',{credentials:'same-origin',cache:'no-store'}).then(async r=>{if(!r.ok)throw new Error('Informations indisponibles.');return await r.json() as Details}).then(d=>{if(active)setDetails(d)}).catch(e=>{if(active)setError(e instanceof Error?e.message:'Informations indisponibles.')}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[page,revision]);
 function navigate(next:Page){if(pending.current)return;setError('');setNotice('');setCurrent('');setPassword('');setConfirmation('');setFirst(account.first_name);setLast(account.last_name);setPage(next)}
 async function save(e:FormEvent){
  e.preventDefault();if(pending.current)return;
  if(page==='responsible'&&(!validProfileName(first)||!validProfileName(last)))return;
  if(page==='password'&&(!current||!passwordValid(password,confirmation)))return;
  pending.current=true;setBusy(true);setError('');setNotice('');
  try{if(page==='responsible'){const updated=await authPost<Account>('company/profile',{first_name:first,last_name:last});onUpdated(updated);setFirst(updated.first_name);setLast(updated.last_name);setNotice('Informations enregistrées.')}
  else if(page==='password'){await authPost('company/password',{current_password:current,password,password_confirmation:confirmation});setCurrent('');setPassword('');setConfirmation('');setNotice('Mot de passe modifié.')}
  }catch(e){setError(e instanceof Error?e.message:'Enregistrement impossible.')}finally{pending.current=false;setBusy(false)}
 }
 const state=status??account.company?.status;
 return <section className="company-profile-premium">
 {page==='home'?<article className="company-profile-card"><header className="company-profile-hero branded-hero"><BrandCover banner={account.company?.banner}/><BrandLogo logo={account.company?.logo}/><h2>{account.company?.name||'Ma compagnie'}</h2><p>{account.company?.city||'Mali'}{account.company?.city?', Mali':''}</p><span className={'company-profile-status '+(state==='VERIFIED'?'verified':'')}><BadgeCheck size={17}/>{state?tr(statusLabels[state]):'Statut indisponible'}</span></header>
 <div className="company-profile-menu"><Item icon={<Building2 size={21}/>} label={tr(titles.company)} detail="Identité, adresse et immatriculation" onClick={()=>navigate('company')}/><Item icon={<UserRound size={21}/>} label={tr(titles.responsible)} detail="Nom, téléphone et email" onClick={()=>navigate('responsible')}/><Item icon={<ShieldCheck size={21}/>} label={tr(titles.password)} detail="Modifier le mot de passe" onClick={()=>navigate('password')}/><Item icon={<Users size={21}/>} label={tr(titles.agents)} detail="Créer et gérer les accès" onClick={()=>navigate('agents')}/><Item icon={<Bell size={21}/>} label={tr(titles.notifications)} detail="Réservations et embarquements" onClick={()=>navigate('notifications')}/><Item icon={<Headset size={21}/>} label={tr(titles.support)} detail="Aide et informations" onClick={()=>navigate('support')}/><button type="button" className="outline profile-logout" onClick={()=>setLogout(true)}><LogOut size={19}/> {tr("Déconnexion")}</button><small className="company-profile-footer">Propulsé par BTDIGIT</small></div></article>:<>
 <div className="profile-heading"><button type="button" className="profile-back" onClick={()=>navigate('home')} disabled={busy} aria-label={tr("Retour")}><ArrowLeft size={22}/></button><h2>{tr(titles[page])}</h2><ShieldCheck size={22}/></div>
 {page==='company'&&<article className="panel profile-form">{loading&&<p role="status">{tr("Chargement…")}</p>}{details&&<><div className="company-identity-banner branded-hero"><BrandCover banner={account.company?.banner}/><BrandLogo logo={account.company?.logo}/><h3>{details.name}</h3><p>{details.city} · {details.address}</p></div><label>{tr("Nom de la compagnie")}<input readOnly value={details.name}/></label><label>{tr("Ville")}<input readOnly value={details.city}/></label><label>{tr("Adresse")}<input readOnly value={details.address}/></label><label>{tr("Immatriculation")}<input readOnly value={details.registration_number||'Non renseignée'}/></label><small>Toute modification de l’identité légale nécessite une vérification administrative.</small><CompanyBrand account={account} onUpdated={onUpdated}/></>}{error&&<><p role="alert" className="auth-error">{error}</p><button className="outline" onClick={()=>setRevision(x=>x+1)}>{tr("Réessayer")}</button></>}</article>}
 {(page==='responsible'||page==='password')&&<form className="panel profile-form" onSubmit={save}>{page==='responsible'?<><label>{tr("Prénom")}<input required autoComplete="given-name" maxLength={150} value={first} disabled={busy} onChange={e=>setFirst(e.target.value)}/></label><label>{tr("Nom")}<input required autoComplete="family-name" maxLength={150} value={last} disabled={busy} onChange={e=>setLast(e.target.value)}/></label><label>{tr("Téléphone")}<input readOnly value={account.phone||'Non renseigné'}/></label><label>{tr("Email")}<input readOnly value={account.email||'Non renseigné'}/></label><small>Les identifiants de connexion restent protégés.</small></>:<><label>{tr("Mot de passe actuel")}<input type="password" autoComplete="current-password" required maxLength={128} value={current} disabled={busy} onChange={e=>setCurrent(e.target.value)}/></label><label>{tr("Nouveau mot de passe")}<input type="password" autoComplete="new-password" required minLength={8} maxLength={128} value={password} disabled={busy} onChange={e=>setPassword(e.target.value)}/></label><label>{tr("Confirmer le mot de passe")}<input type="password" autoComplete="new-password" required maxLength={128} value={confirmation} disabled={busy} onChange={e=>setConfirmation(e.target.value)}/></label><small>8 caractères minimum. Choisissez un mot de passe unique.</small></>}{error&&<p className="auth-error" role="alert">{error}</p>}{notice&&<p className="profile-success" role="status">{notice}</p>}<button className="primary" disabled={busy||(page==='responsible'?(!validProfileName(first)||!validProfileName(last)):(!current||!passwordValid(password,confirmation)))}>{busy?'Enregistrement…':'Enregistrer'}</button></form>}
 {page==='agents'&&<CompanyAgents verified={state==='VERIFIED'}/>}
 {page==='notifications'&&<NotificationCenter/>}
 {page==='support'&&<Suspense fallback={<p role="status">Chargement de l’assistance…</p>}><SupportCenter/></Suspense>}
 </>}
 {logout&&<dialog ref={dialog} className="booking-dialog" aria-label="Confirmer la déconnexion" onCancel={e=>{e.preventDefault();setLogout(false)}}><h2>Se déconnecter ?</h2><p>Les réservations et contrôles enregistrés seront conservés.</p><div className="profile-dialog-actions"><button className="outline" autoFocus onClick={()=>setLogout(false)}>{tr("Retour")}</button><button className="primary" onClick={()=>{setLogout(false);onLogout()}}>{tr("Déconnexion")}</button></div></dialog>}
 </section>
}

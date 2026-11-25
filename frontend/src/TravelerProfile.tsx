import {lazy,Suspense,useState,useRef,useEffect,type FormEvent,type ReactNode} from 'react';
import {ArrowLeft,Bell,ChevronRight,Globe,Headset,History,Info,LockKeyhole,LogOut,Mail,Phone,Settings,ShieldCheck,Ticket,UserRound,UserRoundPen} from 'lucide-react';
import {authPost,type Account} from './auth-api';
import {passwordValid} from './auth-validation';
import {initials,validProfileName} from './profile-validation';
import './profile.css';
import NotificationCenter from './NotificationCenter';
const SupportCenter=lazy(()=>import('./SupportCenter'));

type Page='home'|'settings'|'edit'|'password'|'transactions'|'language'|'notifications'|'support'|'about'|'legal';
type Props={account:Account|null;onUpdated:(account:Account)=>void;onTickets:()=>void;onLogout:()=>Promise<void>};
function Item({icon,label,detail,onClick}:{icon:ReactNode;label:string;detail?:string;onClick:()=>void}){
 return <button type="button" className="profile-item" onClick={onClick}><span className="profile-icon">{icon}</span><span className="profile-item-copy"><strong>{label}</strong>{detail&&<small>{detail}</small>}</span><ChevronRight size={19} aria-hidden="true"/></button>
}
const titles:Record<Page,string>={home:'Mon profil',settings:'Paramètres',edit:'Modifier mon profil',password:'Mot de passe',transactions:'Transactions',language:'Langue',notifications:'Notifications',support:'Aide & support',about:'À propos',legal:'Informations légales'};
export default function TravelerProfile({account,onUpdated,onTickets,onLogout}:Props){
 const [page,setPage]=useState<Page>('home'),[first,setFirst]=useState(account?.first_name||''),[last,setLast]=useState(account?.last_name||'');
 const [current,setCurrent]=useState(''),[password,setPassword]=useState(''),[confirmation,setConfirmation]=useState('');
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[success,setSuccess]=useState(''),[confirmLogout,setConfirmLogout]=useState(false);
 const pending=useRef(false),dialog=useRef<HTMLDialogElement>(null),heading=useRef<HTMLHeadingElement>(null);
 useEffect(()=>{if(confirmLogout&&dialog.current&&!dialog.current.open)dialog.current.showModal()},[confirmLogout]);
 useEffect(()=>{heading.current?.focus({preventScroll:true})},[page]);
 function navigate(next:Page){setPage(next);setError('');setSuccess('');setCurrent('');setPassword('');setConfirmation('');if(next==='edit'){setFirst(account?.first_name||'');setLast(account?.last_name||'')}window.scrollTo({top:0,behavior:'instant'})}
 function back(){navigate(['edit','password','about','legal'].includes(page)?'settings':'home')}
 async function save(e:FormEvent){
  e.preventDefault();if(pending.current||!account)return;
  if(page==='edit'&&(!validProfileName(first)||!validProfileName(last)))return;
  if(page==='password'&&(!current||current.length>128||!passwordValid(password,confirmation)))return;
  pending.current=true;setBusy(true);setError('');setSuccess('');
  try{
   if(page==='edit'){const updated=await authPost<Account>('profile',{first_name:first,last_name:last});onUpdated(updated);setFirst(updated.first_name);setLast(updated.last_name);setSuccess('Profil enregistré.')}
   else if(page==='password'){await authPost('password',{current_password:current,password,password_confirmation:confirmation});setCurrent('');setPassword('');setConfirmation('');setSuccess('Mot de passe modifié.')}
  }catch(e){setError(e instanceof Error?e.message:'Enregistrement impossible.')}
  finally{pending.current=false;setBusy(false)}
 }
 async function logout(){if(pending.current)return;pending.current=true;setBusy(true);try{await onLogout()}finally{pending.current=false;setBusy(false);setConfirmLogout(false)}}
 if(!account)return <section className="panel empty account-info"><UserRound size={40}/><h1>Mon profil</h1><p>Connectez-vous pour retrouver vos voyages.</p><a className="primary" href="/register/">Créer mon compte</a><a className="outline" href="/login/">Se connecter</a></section>;
 return <section className="traveler-profile">
 <div className="profile-heading">{page!=='home'&&<button type="button" className="profile-back" aria-label="Retour" onClick={back} disabled={busy}><ArrowLeft size={22}/></button>}<h1 ref={heading} tabIndex={-1}>{titles[page]}</h1><UserRound size={23}/></div>
 {page==='home'&&<>
 <div className="profile-identity"><div className="profile-avatar">{initials(account.first_name,account.last_name)}</div><div><h2>{account.first_name} {account.last_name}</h2><small>Voyageur SiraGo</small>{account.phone&&<p><Phone size={15}/>{account.phone}</p>}{account.email&&<p><Mail size={15}/>{account.email}</p>}</div></div>
 <h2 className="profile-section-title">Mon compte</h2><div className="panel profile-menu">
 <Item icon={<Ticket size={22}/>} label="Mes réservations" onClick={onTickets}/>
 <Item icon={<History size={22}/>} label="Transactions" detail="Paiement à venir" onClick={()=>navigate('transactions')}/>
 <Item icon={<Settings size={22}/>} label="Paramètres" onClick={()=>navigate('settings')}/>
 <Item icon={<Globe size={22}/>} label="Langue" detail="Français" onClick={()=>navigate('language')}/>
 <Item icon={<Bell size={22}/>} label="Notifications" onClick={()=>navigate('notifications')}/>
 <Item icon={<Headset size={22}/>} label="Aide & support" onClick={()=>navigate('support')}/>
 </div><button type="button" className="outline profile-logout" onClick={()=>setConfirmLogout(true)}><LogOut size={19}/> Déconnexion</button>
 </>}
 {page==='settings'&&<><h2 className="profile-section-title">Compte</h2><div className="panel profile-menu">
 <Item icon={<UserRoundPen size={22}/>} label="Modifier mon profil" onClick={()=>navigate('edit')}/>
 <Item icon={<LockKeyhole size={22}/>} label="Changer le mot de passe" onClick={()=>navigate('password')}/>
 </div><h2 className="profile-section-title">Application</h2><div className="panel profile-menu">
 <Item icon={<ShieldCheck size={22}/>} label="Informations légales" onClick={()=>navigate('legal')}/>
 <Item icon={<Info size={22}/>} label="À propos de SiraGo" onClick={()=>navigate('about')}/>
 <Item icon={<Headset size={22}/>} label="Aide & support" onClick={()=>navigate('support')}/>
 </div></>}
 {(page==='edit'||page==='password')&&<form className="panel profile-form" onSubmit={save}>
 {page==='edit'?<><label>Prénom<input autoComplete="given-name" required maxLength={150} value={first} disabled={busy} onChange={e=>setFirst(e.target.value)}/></label><label>Nom<input autoComplete="family-name" required maxLength={150} value={last} disabled={busy} onChange={e=>setLast(e.target.value)}/></label><label>Téléphone<input value={account.phone||'Non renseigné'} readOnly/></label><label>Email<input value={account.email||'Non renseigné'} readOnly/></label><small>Les identifiants de connexion ne sont pas modifiables ici.</small></>:<><label>Mot de passe actuel<input type="password" autoComplete="current-password" required maxLength={128} value={current} disabled={busy} onChange={e=>setCurrent(e.target.value)}/></label><label>Nouveau mot de passe<input type="password" autoComplete="new-password" required minLength={8} maxLength={128} value={password} disabled={busy} onChange={e=>setPassword(e.target.value)}/></label><label>Confirmer<input type="password" autoComplete="new-password" required maxLength={128} value={confirmation} disabled={busy} onChange={e=>setConfirmation(e.target.value)}/></label><small>8 caractères minimum. Évitez les mots de passe courants.</small></>}
 {error&&<p className="auth-error" role="alert">{error}</p>}{success&&<p className="profile-success" role="status">{success}</p>}
 <button className="primary" disabled={busy||(page==='edit'?(!validProfileName(first)||!validProfileName(last)):(!current||!passwordValid(password,confirmation)))}>{busy?'Enregistrement…':'Enregistrer'}</button></form>}
 {page==='transactions'&&<div className="panel profile-message"><History size={30}/><h2>Paiements à venir</h2><p>L’historique sera disponible après activation des paiements.</p><button className="outline" onClick={onTickets}>Mes réservations</button></div>}
 {page==='language'&&<div className="panel profile-message"><Globe size={30}/><h2>Français</h2><p>Langue actuellement disponible.</p></div>}
 {page==='notifications'&&<NotificationCenter signedIn={!!account}/>}
 {page==='support'&&<Suspense fallback={<p role="status">Chargement de l’assistance…</p>}><SupportCenter/></Suspense>}
 {page==='about'&&<div className="panel profile-message"><img src="/logo.svg" width="64" height="64" alt=""/><h2>SiraGo</h2><p>Ka billet ta fô i sigi yorola.</p><p>Réservez votre billet sans vous déplacer.</p><small>Propulsé par BTDIGIT</small></div>}
 {page==='legal'&&<div className="panel profile-message"><ShieldCheck size={30}/><h2>Version de développement</h2><p>Les conditions définitives et la politique de confidentialité seront publiées avant le lancement.</p></div>}
 {confirmLogout&&<dialog ref={dialog} className="booking-dialog" aria-labelledby="profile-logout-title" onCancel={e=>{e.preventDefault();if(!busy)setConfirmLogout(false)}}><h2 id="profile-logout-title">Se déconnecter ?</h2><p>Vos réservations restent enregistrées.</p><div className="profile-dialog-actions"><button className="outline" autoFocus disabled={busy} onClick={()=>setConfirmLogout(false)}>Retour</button><button className="primary" disabled={busy} onClick={logout}>Déconnexion</button></div></dialog>}
 </section>
}

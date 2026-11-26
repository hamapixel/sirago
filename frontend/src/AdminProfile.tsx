import {useRef,useState,type FormEvent} from 'react';
import {UserRound,ShieldCheck,LockKeyhole,Mail,Phone,LogOut} from 'lucide-react';
import {authPost,type Account} from './auth-api';
import {passwordValid} from './auth-validation';
import {validProfileName,initials} from './profile-validation';

export function adminDisplayName(account:Account){
 return [account.first_name,account.last_name].filter(Boolean).join(' ').trim()||account.username||'Superadministrateur';
}

export default function AdminProfile({account,onUpdated,onLogout}:{account:Account;onUpdated:(account:Account)=>void;onLogout:()=>void}){
 const [first,setFirst]=useState(account.first_name),[last,setLast]=useState(account.last_name);
 const [current,setCurrent]=useState(''),[password,setPassword]=useState(''),[confirmation,setConfirmation]=useState('');
 const [busy,setBusy]=useState<'profile'|'password'|null>(null),[error,setError]=useState(''),[notice,setNotice]=useState('');
 const pending=useRef(false);
 async function save(e:FormEvent,kind:'profile'|'password'){
  e.preventDefault();
  if(pending.current)return;
  if(kind==='profile'&&(!validProfileName(first)||!validProfileName(last)))return;
  if(kind==='password'&&(!current||!passwordValid(password,confirmation)))return;
  pending.current=true;setBusy(kind);setError('');setNotice('');
  try{
   if(kind==='profile'){
    const updated=await authPost<Account>('supervision/profile',{first_name:first,last_name:last});
    onUpdated(updated);setFirst(updated.first_name);setLast(updated.last_name);setNotice('Profil enregistré.');
   }else{
    await authPost('supervision/password',{current_password:current,password,password_confirmation:confirmation});
    setCurrent('');setPassword('');setConfirmation('');setNotice('Mot de passe modifié.');
   }
  }catch(e){setError(e instanceof Error?e.message:'Enregistrement impossible.')}
  finally{pending.current=false;setBusy(null)}
 }
 return <section className="super-profile">
 <article className="panel super-profile-identity"><span className="super-profile-avatar">{account.first_name||account.last_name?initials(account.first_name,account.last_name):<UserRound size={32}/>}</span><div><h3>{adminDisplayName(account)}</h3><span className="super-role"><ShieldCheck size={16}/> Superadministrateur</span>{account.username&&<p>Identifiant : {account.username}</p>}{account.email&&<p><Mail size={16}/>{account.email}</p>}{account.phone&&<p><Phone size={16}/>{account.phone}</p>}</div></article>
 {error&&<p role="alert" className="auth-error">{error}</p>}{notice&&<p role="status" className="super-profile-notice">{notice}</p>}
 <div className="super-profile-grid">
 <form className="panel super-profile-form" onSubmit={e=>save(e,'profile')}><h3><UserRound size={21}/> Informations personnelles</h3><label>Prénom<input autoComplete="given-name" maxLength={150} required value={first} onChange={e=>setFirst(e.target.value)}/></label><label>Nom<input autoComplete="family-name" maxLength={150} required value={last} onChange={e=>setLast(e.target.value)}/></label><small>Les identifiants et les droits administratifs restent inchangés.</small><button className="primary" type="submit" disabled={!!busy||!validProfileName(first)||!validProfileName(last)}>{busy==='profile'?'Enregistrement…':'Enregistrer mon profil'}</button></form>
 <form className="panel super-profile-form" onSubmit={e=>save(e,'password')}><h3><LockKeyhole size={21}/> Sécurité du compte</h3><label>Mot de passe actuel<input type="password" autoComplete="current-password" maxLength={128} required value={current} onChange={e=>setCurrent(e.target.value)}/></label><label>Nouveau mot de passe<input type="password" autoComplete="new-password" minLength={8} maxLength={128} required value={password} onChange={e=>setPassword(e.target.value)}/></label><label>Confirmer le mot de passe<input type="password" autoComplete="new-password" maxLength={128} required value={confirmation} onChange={e=>setConfirmation(e.target.value)}/></label><small>8 caractères minimum. Robustesse vérifiée par le serveur.</small><button type="submit" className="primary" disabled={!!busy||!current||!passwordValid(password,confirmation)}>{busy==='password'?'Enregistrement…':'Changer le mot de passe'}</button></form>
 </div><button className="outline super-profile-logout" type="button" disabled={!!busy} onClick={onLogout}><LogOut size={19}/> Déconnexion</button>
 </section>
}

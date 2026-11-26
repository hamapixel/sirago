import {t as tr} from './i18n';
import {useState,type FormEvent} from 'react';
import {ArrowLeft,ArrowRight,BusFront,Check,CircleCheck,CircleX,Eye,EyeOff,LockKeyhole,UserRound} from 'lucide-react';
import {authPost,destination,type Account} from './auth-api';
import {phoneValid,emailValid,passwordValid,passwordChecks} from './auth-validation';
import './auth.css';
import {AuthTrip} from './BookingSpace';
import {authUrl,bookingUrl,type Selection} from './booking-api';
type Role='traveler'|'company';
const initial={first_name:'',last_name:'',phone:'',email:'',company_name:'',city:'Bamako',address:'',registration_number:'',password:'',password_confirmation:'',terms:false};
export default function AuthPage({register,selection=null}:{register:boolean;selection?:Selection|null}){
 const [role,setRole]=useState<Role>('traveler'),[step,setStep]=useState(selection&&register?1:0),[values,setValues]=useState(initial),[identifier,setIdentifier]=useState(''),[show,setShow]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const change=(key:keyof typeof initial,value:string|boolean)=>{setValues(old=>({...old,[key]:value}));setError('')};
 const next=()=>{setError('');setStep(s=>s+1)};
 const validIdentity=!!values.first_name.trim()&&!!values.last_name.trim()&&phoneValid(values.phone)&&emailValid(values.email)&&(role==='traveler'||!!values.company_name.trim());
 const checks=passwordChecks(values.password,values.password_confirmation);
 const validSecurity=passwordValid(values.password,values.password_confirmation)&&values.terms&&(role==='traveler'||!!values.address.trim()&&!!values.city.trim());
 const field=(key:Exclude<keyof typeof initial,'terms'>,label:string,type='text',autoComplete?:string,maxLength=150)=><label key={key}>{label}<input type={type} value={values[key]} autoComplete={autoComplete} maxLength={maxLength} onChange={e=>change(key,e.target.value)}/></label>;
 async function submit(e:FormEvent){e.preventDefault();if(busy)return;setError('');
 if(register&&step===1){if(validIdentity)next();return}
 if(register&&step===2){if(validSecurity)next();return}
 if(register&&step!==3)return;
 if(register&&(!validIdentity||!validSecurity))return;
 setBusy(true);
 try{const account=await authPost<Account>(register?'register/'+role:'login',register?values:{identifier,password:values.password});window.location.assign(selection&&account.role==='TRAVELER'?bookingUrl(selection):destination(account))}
 catch(e){setError(e instanceof Error?e.message:'Connexion au serveur impossible.');setBusy(false)}
 }
 return <section className="auth-shell">
 <div className="auth-banner"><img src="/logo.svg" alt="" width="54" height="54"/><h1>SiraGo</h1><strong>Ka billet ta fô i sigi yorola.</strong><p>{tr("Réservez votre billet sans vous déplacer.")}</p></div>
 {selection&&<AuthTrip selection={selection}/>}
 <div className="panel auth-form">
 <div className="auth-heading">{register&&step>(selection?1:0)&&<button className="icon-button" type="button" aria-label="Étape précédente" disabled={busy} onClick={()=>{setStep(s=>s-1);setError('')}}><ArrowLeft/></button>}<h2>{selection?(register?'Compte voyageur':'Connexion pour réserver'):(register?'Créer mon compte':'Bienvenue sur SiraGo')}</h2></div>
 {register&&step===0?<><p className="auth-muted">Choisissez votre profil.</p><div className="role-choices">{(['traveler','company'] as const).map(r=><button type="button" key={r} className={'role-card '+(role===r?'chosen':'')} aria-pressed={role===r} onClick={()=>setRole(r)}>{r==='traveler'?<UserRound/>:<BusFront/>}<span><strong>{r==='traveler'?'Je suis voyageur':'Je suis une compagnie'}</strong><small>{r==='traveler'?'Réserver mes voyages':'Gérer mes trajets'}</small></span>{role===r&&<Check size={18}/>}</button>)}</div><button type="button" className="primary" onClick={next}>Commencer <ArrowRight size={18}/></button></>:<form onSubmit={submit} className="auth-fields">
 {register&&<div className="auth-steps">{['Identité','Sécurité','Confirmation'].map((t,i)=><div key={t} className={step>=i+1?'reached':''}><span>{step>i+1?<Check size={16}/>:i+1}</span><small>{t}</small></div>)}</div>}
 {!register?<><p className="auth-muted">{selection?'Connectez-vous pour réserver.':'Téléphone, email ou identifiant administrateur.'}</p><label>Téléphone, email ou identifiant admin<input value={identifier} onChange={e=>setIdentifier(e.target.value)} autoComplete="username" required maxLength={254}/></label></>:step===1?<>{role==='company'&&field('company_name','Nom de la compagnie','text','organization')}{field('last_name','Nom','text','family-name')}{field('first_name','Prénom','text','given-name')}<label>{tr("Téléphone")}<div className="auth-phone"><span>+223</span><input type="tel" inputMode="tel" autoComplete="tel-national" value={values.phone} onChange={e=>change('phone',e.target.value)} placeholder="70 00 00 00" maxLength={20}/></div></label>{field('email','Email (facultatif)','email','email',254)}</>:step===2?<>{role==='company'&&<>{field('city','Ville du siège','text','address-level2',100)}{field('address','Adresse ou gare','text','street-address',250)}{field('registration_number','Immatriculation commerciale (facultatif)','text',undefined,100)}</>}<p className="auth-muted"><LockKeyhole size={15}/> Mot de passe : 8 caractères minimum.</p></>:<div className="auth-summary"><h3>Vérifiez vos informations</h3><p><small>Type de compte</small><strong>{role==='traveler'?'Voyageur':'Compagnie'}</strong></p><p><small>Nom complet</small><strong>{values.first_name} {values.last_name}</strong></p><p><small>{tr("Téléphone")}</small><strong>{values.phone.startsWith('+223')?'':'+223 '}{values.phone}</strong></p>{values.email&&<p><small>{tr("Email")}</small><strong>{values.email}</strong></p>}{role==='company'&&<><p><small>Compagnie</small><strong>{values.company_name}</strong></p><p><small>{tr("Adresse")}</small><strong>{values.address}, {values.city}</strong></p><small>La publication des trajets nécessitera une validation BTDIGIT.</small></>}</div>}
 {(!register||step===2)&&<><label>{tr("Mot de passe")}<div className="auth-password"><input type={show?'text':'password'} value={values.password} onChange={e=>change('password',e.target.value)} autoComplete={register?'new-password':'current-password'} maxLength={128} required/><button type="button" className="icon-button" onClick={()=>setShow(v=>!v)} aria-label={show?'Masquer le mot de passe':'Afficher le mot de passe'}>{show?<EyeOff size={19}/>:<Eye size={19}/>}</button></div></label>{register&&<>{field('password_confirmation','Confirmer le mot de passe',show?'text':'password','new-password',128)}<label className="auth-check"><input type="checkbox" checked={values.terms} onChange={e=>change('terms',e.target.checked)}/> J’accepte les conditions d’utilisation de SiraGo en phase de test.</label><ul className="auth-checklist" aria-live="polite" aria-label="Conditions de validation">{[{ok:checks.length,text:'Entre 8 et 128 caractères'},{ok:checks.matching,text:'Mots de passe identiques'},{ok:values.terms,text:'Conditions acceptées'},...(role==='company'?[{ok:!!values.city.trim()&&!!values.address.trim(),text:'Ville et adresse'}]:[])].map(rule=><li key={rule.text} className={rule.ok?'passed':'missing'}>{rule.ok?<CircleCheck size={17} aria-hidden="true"/>:<CircleX size={17} aria-hidden="true"/>}<span>{rule.ok?'Validé : ':'À compléter : '}{rule.text}</span></li>)}</ul><small>Robustesse vérifiée par le serveur.</small><small>Mode test : données fictives uniquement.</small></>}</>}
 {register&&step===1&&!validIdentity&&<small role="status">Nom, prénom et téléphone (8 chiffres) requis. Email valide si renseigné.</small>}
 {error&&<p className="auth-error" role="alert">{error}</p>}
 <button className="primary" type="submit" disabled={busy||(register&&(step===1?!validIdentity:step===2?!validSecurity:!validIdentity||!validSecurity))||(!register&&(!identifier.trim()||!values.password))}>{busy?'Veuillez patienter…':!register?'Se connecter':step===3?'Créer mon compte':'Continuer'}<ArrowRight size={18}/></button>
 </form>}
 <p className="auth-switch">{register?'Vous avez déjà un compte ?':'Pas encore de compte ?'} <a href={selection?authUrl(!register,selection):register?'/login/':'/register/'}>{register?'Se connecter':'Créer mon compte'}</a></p><a className="auth-back" href="/">Retour à l’accueil</a>
 </div></section>
}

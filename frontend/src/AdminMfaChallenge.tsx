import {useState,type FormEvent} from 'react';
import {ShieldCheck,LockKeyhole} from 'lucide-react';
import {authPost,destination,type Account,type MfaChallenge} from './auth-api';
import './mfa.css';

export function validMfaCode(value:string,mode:'totp'|'recovery'|'activation'){
 const s=value.trim();
 return mode==='totp'?/^[0-9]{6}$/.test(s):mode==='recovery'?/^[0-9a-fA-F]{32}$/.test(s):/^[0-9a-f]{48}$/.test(s);
}
export default function AdminMfaChallenge({challenge}:{challenge:MfaChallenge}){
 const [stage,setStage]=useState<'enroll'|'confirm'|'verify'|'complete'>(challenge.stage);
 const [value,setValue]=useState(''),[secret,setSecret]=useState(''),[qr,setQr]=useState('');
 const [recovery,setRecovery]=useState(false),[codes,setCodes]=useState<string[]>([]);
 const [account,setAccount]=useState<Account|null>(null),[ack,setAck]=useState(false);
 const [busy,setBusy]=useState(false),[error,setError]=useState('');
 const mode=stage==='enroll'?'activation':stage==='verify'&&recovery?'recovery':'totp';
 async function submit(e:FormEvent){
  e.preventDefault();if(busy||!validMfaCode(value,mode))return;setBusy(true);setError('');
  try{
   if(stage==='enroll'){
    const r=await authPost<{secret:string;qr:string}>('mfa/enroll',{activation_code:value.trim()});
    setSecret(r.secret);setQr(r.qr);setStage('confirm');setValue('');
   }else{
    const r=await authPost<{account:Account;recovery_codes?:string[]}>('mfa/verify',{code:value.trim()});
    setValue('');setSecret('');setQr('');
    if(r.recovery_codes?.length){setCodes(r.recovery_codes);setAccount(r.account);setStage('complete')}
    else window.location.assign(destination(r.account));
   }
  }catch(e){setError(e instanceof Error?e.message:'Vérification indisponible.')}
  finally{setBusy(false)}
 }
 async function cancel(){setBusy(true);try{await authPost('logout',{});window.location.assign('/login/')}catch(e){setError(e instanceof Error?e.message:'Réessayez.');setBusy(false)}}
 return <section className="auth-shell auth-login"><div className="auth-banner"><img className="auth-brand-mark" src="/brand-mark.svg" alt="" width="54" height="54"/><h1>SiraGo</h1><strong>Superadmin · Sécurité</strong></div>
 <div className="panel auth-form mfa-panel"><div className="mfa-symbol"><ShieldCheck size={32}/></div>
 <h2>{stage==='complete'?'Codes de récupération':stage==='enroll'?'Activer la double authentification':'Vérification de sécurité'}</h2>
 {stage==='complete'?<><p>Conservez ces codes hors ligne. Ils ne seront affichés qu’une fois. Chaque code est utilisable une seule fois.</p><div className="mfa-codes">{codes.map(c=><code key={c}>{c}</code>)}</div><label className="auth-check"><input type="checkbox" checked={ack} onChange={e=>setAck(e.target.checked)}/> J’ai conservé mes codes en lieu sûr.</label><button className="primary" disabled={!ack||!account} onClick={()=>{if(account){setCodes([]);window.location.assign(destination(account))}}}>Accéder au Superadmin</button></>:<form className="auth-fields" onSubmit={submit}>
 {stage==='enroll'?<p>Demandez au responsable système le code privé d’activation à usage unique, valable 15 minutes.</p>:stage==='confirm'?<><p>Scannez ce QR code dans votre application d’authentification (Google Authenticator, Microsoft Authenticator ou autre TOTP).</p><img className="mfa-qr" src={qr} alt="QR code d’activation TOTP"/><details><summary>Saisir la clé manuellement</summary><code className="mfa-secret">{secret}</code></details></>:<p>{recovery?'Saisissez un code de récupération inutilisé.':'Saisissez le code à six chiffres de votre application d’authentification.'}</p>}
 <label>{mode==='activation'?'Code privé d’activation':mode==='recovery'?'Code de récupération':'Code à six chiffres'}<input value={value} onChange={e=>setValue(e.target.value)} autoComplete={mode==='totp'?'one-time-code':'off'} inputMode={mode==='totp'?'numeric':'text'} spellCheck={false} autoCapitalize="none" maxLength={mode==='totp'?6:mode==='recovery'?32:48} required className={mode==='totp'?'mfa-otp':''}/></label>
 {error&&<p className="auth-error" role="alert">{error}</p>}
 <button className="primary" disabled={busy||!validMfaCode(value,mode)} type="submit"><LockKeyhole size={18}/>{busy?'Vérification…':stage==='enroll'?'Afficher le QR code':'Vérifier mon identité'}</button>
 {stage==='verify'&&<button type="button" className="outline" disabled={busy} onClick={()=>{setRecovery(v=>!v);setValue('');setError('')}}>{recovery?'Utiliser un code à six chiffres':'Utiliser un code de récupération'}</button>}
 <button type="button" className="outline" disabled={busy} onClick={cancel}>Annuler et se reconnecter</button>
 <small>Pour votre sécurité, cette étape expire après 5 minutes.</small></form>}
 </div></section>
}

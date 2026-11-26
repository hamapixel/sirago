import {useEffect,useState,useRef} from 'react';
import {BellRing,BellOff,Smartphone} from 'lucide-react';
import {authPost} from './auth-api';
type State='loading'|'unavailable'|'unsupported'|'denied'|'off'|'on'|'error';
export function vapidBytes(value:string):Uint8Array<ArrayBuffer>{
 const raw=atob(value.replace(/-/g,'+').replace(/_/g,'/')+'='.repeat((4-value.length%4)%4));
 const result=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)result[i]=raw.charCodeAt(i);
 if(result.length!==65||result[0]!==4)throw new Error('Clé publique invalide.');
 return result;
}
export default function PushPreferences(){
 const [state,setState]=useState<State>('loading'),[key,setKey]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const pending=useRef(false);
 const [revision,setRevision]=useState(0);
 useEffect(()=>{let active=true;const controller=new AbortController();
 async function load(){
  if(!window.isSecureContext||!('serviceWorker' in navigator)||!('PushManager' in window)||!('Notification' in window)){if(active)setState('unsupported');return}
  if(Notification.permission==='denied'){if(active)setState('denied');return}
  const response=await fetch('/api/v1/auth/notifications/push/',{credentials:'same-origin',cache:'no-store',signal:controller.signal});
  if(!response.ok)throw Error('Configuration indisponible.');
  const {public_key}=await response.json();if(!active)return;
  const registration=await navigator.serviceWorker.getRegistration();
  if(!active)return;
  const sub=await registration?.pushManager.getSubscription();
  if(!active)return;
  if(sub){
   const status=await authPost<{enabled:boolean}>('notifications/push/status',{endpoint:sub.endpoint});
   if(!active)return;
   if(status.enabled){setKey(public_key||'');setState('on');return}
  }
  if(!public_key||!registration?.active){setState('unavailable');return}
  vapidBytes(public_key);setKey(public_key);setState('off');
 }
 void load().catch(()=>{if(active)setState('error')});return()=>{active=false;controller.abort()}
 },[revision]);
 async function change(){
  if(pending.current)return;pending.current=true;setBusy(true);setError('');
  try{
   if(state==='on'){
    const registration=await navigator.serviceWorker.getRegistration();
    const sub=await registration?.pushManager.getSubscription();
    if(sub){await authPost('notifications/push/unsubscribe',{endpoint:sub.endpoint});await sub.unsubscribe()}
    setState(key?'off':'unavailable');return;
   }
   // Safari requires a direct gesture for the permission prompt.
   const permission=await Notification.requestPermission();
   if(permission!=='granted'){setState(permission==='denied'?'denied':'off');return}
   const registration=await navigator.serviceWorker.getRegistration();
   if(!registration?.active)throw Error('Application non prête. Actualisez SiraGo.');
   let sub=await registration.pushManager.getSubscription();
   if(!sub)sub=await registration.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:vapidBytes(key)});
   await authPost('notifications/push/subscribe',sub.toJSON() as Record<string,unknown>);
   setState('on');
  }catch(e){setError(e instanceof Error?e.message:'Action impossible.');}
  finally{pending.current=false;setBusy(false)}
 }
 const detail:Record<State,string>={loading:'Vérification de cet appareil…',unavailable:'Disponible après configuration du serveur et de la PWA.',unsupported:'Sur iPhone, installez SiraGo sur l’écran d’accueil. Utilisez un navigateur compatible et HTTPS.',denied:'Autorisez les notifications dans les réglages de votre téléphone ou navigateur.',off:'Recevez vos alertes même lorsque SiraGo est fermé.',on:'Alertes autorisées sur cet appareil.',error:'Impossible de vérifier les alertes externes.'};
 return <article className="push-preferences"><span className="push-device-icon">{state==='on'?<BellRing size={23}/>:<Smartphone size={23}/>}</span><div><strong>Notifications sur cet appareil</strong><small>{detail[state]}</small></div>{(state==='on'||state==='off')&&<button type="button" className={state==='on'?'outline':'primary'} disabled={busy} onClick={()=>void change()}>{state==='on'?<BellOff size={17}/>:<BellRing size={17}/>} {busy?'Patientez…':state==='on'?'Désactiver':'Activer'}</button>}{state==='error'&&<button className="outline" type="button" onClick={()=>setRevision(r=>r+1)}>Réessayer</button>}{error&&<p className="auth-error" role="alert">{error}</p>}</article>
}

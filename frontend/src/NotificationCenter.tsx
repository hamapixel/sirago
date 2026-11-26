import {useState,useEffect,useRef} from 'react';
import {Bell,CheckCheck,CheckCircle2,Ticket,CalendarDays,ScanLine,RefreshCw} from 'lucide-react';
import {authPost} from './auth-api';
import PushPreferences from './PushPreferences';
import {t} from './i18n';
import {dayText,timeText} from './travel-api';
import {Pagination} from './listing';
import './notifications-dialog.css';

type Notice={id:number;kind:string;title:string;message:string;created_at:string;read_at:string|null};
type NoticePage={items:Notice[];total:number;page_size:number;unread_count:number};
const changed='sirago:notifications-changed';
function listenForUpdates(refresh:()=>void){
 const onPush=(e:MessageEvent)=>{if(e.data?.type==='SIRAGO_PUSH_RECEIVED')refresh()};
 window.addEventListener(changed,refresh);window.addEventListener('online',refresh);window.addEventListener('focus',refresh);document.addEventListener('visibilitychange',refresh);
 if('serviceWorker' in navigator)navigator.serviceWorker.addEventListener('message',onPush);
 const timer=window.setInterval(refresh,30000);
 return()=>{window.clearInterval(timer);window.removeEventListener(changed,refresh);window.removeEventListener('online',refresh);window.removeEventListener('focus',refresh);document.removeEventListener('visibilitychange',refresh);if('serviceWorker' in navigator)navigator.serviceWorker.removeEventListener('message',onPush)};
}
async function get<T>(path:string,signal:AbortSignal):Promise<T>{
 const r=await fetch('/api/v1/auth/notifications/'+path,{credentials:'same-origin',cache:'no-store',signal});
 if(!r.ok)throw new Error('Notifications indisponibles. Vérifiez votre connexion.');
 return await r.json() as T;
}
export function useNotificationCount(enabled:boolean){
 const [count,setCount]=useState(0);
 useEffect(()=>{if(!enabled){setCount(0);return}let active=true;let controller:AbortController|undefined;
 const refresh=()=>{if(document.visibilityState==='hidden')return;controller?.abort();const c=new AbortController();controller=c;void get<{unread_count:number}>('count/',c.signal).then(r=>{if(active&&!c.signal.aborted)setCount(r.unread_count)}).catch(()=>{})};
 refresh();const stop=listenForUpdates(refresh);
 return()=>{active=false;controller?.abort();stop()}},[enabled]);
 return count;
}
export function NotificationItem({item,onRead,busy}:{item:Notice;onRead:(id:number)=>void;busy:boolean}){
 const Icon=(item.kind==='DEPARTURE'||item.kind==='TEST_REPORT')?CalendarDays:item.kind==='TEST_BOARDING'?ScanLine:item.kind==='CANCELLED'?Bell:Ticket;
 return <article className={'notice-card '+(!item.read_at?'unread':'')}><div className="notice-card-top"><span className="notice-icon"><Icon size={21}/></span><div><strong>{item.title.replace(/\bTEST\b/g,'').trim()}</strong><small>{dayText(item.created_at)} · {timeText(item.created_at)}</small></div>{(item.kind.startsWith('TEST_')||/\bTEST\b/.test(item.title))&&<span className="notice-simulation">Simulation</span>}{!item.read_at&&<span className="notice-dot" aria-label="Non lu"/>}</div><p>{item.message.replace(/\bmode TEST\b/g,'simulation')}</p>{item.read_at?<small className="notice-read"><CheckCircle2 size={15}/> Lu</small>:<button className="notice-mark" type="button" disabled={busy} onClick={()=>onRead(item.id)}><CheckCircle2 size={16}/> Marquer comme lu</button>}</article>
}
export default function NotificationCenter({signedIn=true,compact=false}:{signedIn?:boolean;compact?:boolean}){
 const [page,setPage]=useState(1),[unread,setUnread]=useState(false),[revision,setRevision]=useState(0),[data,setData]=useState<NoticePage|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const pending=useRef(false);
 useEffect(()=>{if(!signedIn)return;return listenForUpdates(()=>{if(document.visibilityState!=='hidden'&&!pending.current)setRevision(x=>x+1)})},[signedIn]);
 useEffect(()=>{setData(null)},[page,unread,signedIn]);
 useEffect(()=>{if(!signedIn)return;const c=new AbortController();setLoading(true);setError('');
 get<NoticePage>('?'+new URLSearchParams({page:String(page),unread:unread?'1':'0'}),c.signal).then(r=>{if(c.signal.aborted)return;if(page>1&&r.items.length===0){setPage(Math.max(1,Math.ceil(r.total/r.page_size)));return}setData(r)}).catch(e=>{if(!c.signal.aborted)setError(e instanceof Error?e.message:'Chargement impossible.')}).finally(()=>{if(!c.signal.aborted)setLoading(false)});
 return()=>c.abort()},[page,unread,revision,signedIn]);
 async function read(id?:number){if(pending.current)return;pending.current=true;setBusy(true);setError('');
 try{await authPost(id===undefined?'notifications/read-all':'notifications/'+id+'/read',{});window.dispatchEvent(new Event(changed));setRevision(x=>x+1)}
 catch(e){setError(e instanceof Error?e.message:'Modification impossible.')}finally{pending.current=false;setBusy(false)}}
 if(!signedIn)return <div className="notice-empty"><Bell size={32}/><strong>Connectez-vous pour recevoir vos notifications</strong><p>Retrouvez vos alertes de voyage et de réservation.</p><a className="primary" href="/login/">Se connecter</a></div>;
 return <section className={"notice-center"+(compact?" notice-compact":"")} aria-label="Centre de notifications"><PushPreferences/><div className="notice-toolbar"><div className="notice-tabs" role="group" aria-label="Filtrer les notifications"><button type="button" aria-pressed={!unread} onClick={()=>{setUnread(false);setPage(1)}}>Toutes</button><button type="button" aria-pressed={unread} onClick={()=>{setUnread(true);setPage(1)}}>Non lues</button></div><button className="outline notice-refresh" type="button" aria-label="Actualiser les notifications" disabled={loading||busy} onClick={()=>setRevision(x=>x+1)}><RefreshCw size={18}/></button></div>
 {data&&<div className="notice-status"><small>{data.unread_count} non lue(s)</small><button type="button" className="notice-mark" disabled={busy||!data.unread_count} onClick={()=>void read()}><CheckCheck size={17}/> Tout marquer comme lu</button></div>}
 {error&&<p role="alert" className="auth-error">{error}</p>}{loading&&<p role="status">Chargement des notifications…</p>}
 {data&&<>{data.items.length===0&&<div className="notice-empty"><Bell size={30}/><strong>{unread?'Vous êtes à jour':'Aucune notification'}</strong><p>Les nouvelles alertes apparaîtront ici.</p></div>}<div className="notice-grid">{data.items.map(n=><NotificationItem key={n.id} item={n} busy={busy} onRead={id=>void read(id)}/>)}</div><Pagination page={page} size={data.page_size} total={data.total} onChange={setPage} disabled={busy}/></>}
 </section>
}

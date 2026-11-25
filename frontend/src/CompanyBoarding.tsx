import {useEffect,useRef,useState} from 'react';
import {ScanLine,CheckCircle2,UserRound,History,Camera} from 'lucide-react';
import {companyGet,companyPost} from './company-api';
import {dayText,timeText} from './travel-api';
import './boarding.css';
type Passenger={index:number;name:string;boarded_at:string|null};
export type BoardingTicket={code:string;origin:string;destination:string;starts_at:string;boarding_point:string;category:string;count:number;boarded:number;remaining:number;can_board:boolean;passengers:Passenger[]};
type Entry={id:number;name:string;origin:string;destination:string;boarded_at:string};
type Detector={detect:(source:HTMLVideoElement)=>Promise<{rawValue:string}[]>};
type DetectorClass=new(options:{formats:string[]})=>Detector;
const detectorClass=()=> (globalThis as typeof globalThis & {BarcodeDetector?:DetectorClass}).BarcodeDetector;
export const validTicketCode=(value:string)=>/^SRG-TEST-[0-9A-F]{32}$/.test(value.trim().toUpperCase());
export function BoardingResult({ticket:t,selected,onToggle,onAll,onValidate,busy}:{ticket:BoardingTicket;selected:number[];onToggle:(i:number)=>void;onAll:()=>void;onValidate:()=>void;busy:boolean}){
 return <div className="boarding-result">
 <div className="boarding-recognized"><CheckCircle2 size={22}/><div><strong>Billet de test reconnu</strong><p>{t.origin} → {t.destination}</p><small>{dayText(t.starts_at)} · {timeText(t.starts_at)} · {t.boarding_point}</small></div></div>
 <div className="boarding-stats"><div><small>Passagers</small><strong>{t.count}</strong></div><div><small>Embarqués</small><strong>{t.boarded}</strong></div><div><small>Restants</small><strong>{t.remaining}</strong></div></div>
 <progress max={t.count} value={t.boarded} aria-label="Progression des embarquements"/>
 <div className="boarding-list-heading"><h3>Liste des passagers</h3>{t.remaining>0&&t.can_board&&<button type="button" className="outline" disabled={busy} onClick={onAll}>Tout sélectionner</button>}</div>
 {t.passengers.map(p=><label className="boarding-passenger" key={p.index}><UserRound size={18}/><span><strong>{p.name}</strong><small>{t.category}{p.boarded_at?' · Déjà embarqué à '+timeText(p.boarded_at):''}</small></span><input type="checkbox" aria-label={p.name+(p.boarded_at?' déjà embarqué':'')} checked={!!p.boarded_at||selected.includes(p.index)} disabled={busy||!!p.boarded_at||!t.can_board} onChange={()=>onToggle(p.index)}/></label>)}
 {!t.can_board&&<p role="status">Départ indisponible ou terminé. Validation bloquée.</p>}
 {t.remaining===0?<p className="boarding-complete"><CheckCircle2 size={20}/> Tous les passagers sont déjà embarqués.</p>:<button type="button" className="primary" disabled={busy||!selected.length||!t.can_board} onClick={onValidate}>{busy?'Validation…':"Valider l’embarquement ("+selected.length+"/"+t.count+")"}</button>}
 </div>
}
export default function CompanyBoarding({company,verified}:{company:string;verified:boolean}){
 const [code,setCode]=useState(''),[ticket,setTicket]=useState<BoardingTicket|null>(null),[selected,setSelected]=useState<number[]>([]),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState(''),[camera,setCamera]=useState(false),[history,setHistory]=useState<Entry[]|null>(null);
 const video=useRef<HTMLVideoElement>(null),pending=useRef(false);
 async function lookup(raw:string){
  if(pending.current||!verified)return;
  const value=raw.trim().toUpperCase();
  if(!validTicketCode(value)){setError('Référence TEST invalide.');return}
  pending.current=true;setBusy(true);setCamera(false);setError('');setNotice('');setCode(value);setTicket(null);setSelected([]);
  try{setTicket(await companyPost<BoardingTicket>('boarding/lookup/',{code:value}))}catch(e){setError(e instanceof Error?e.message:'Billet introuvable.')}finally{pending.current=false;setBusy(false)}
 }
 useEffect(()=>{
  if(!camera||!verified)return;
  let active=true;let stream:MediaStream|undefined;let timer:number|undefined;
  const run=async()=>{
   try{
    const C=detectorClass();
    if(!C||!navigator.mediaDevices?.getUserMedia)throw new Error('Lecture QR caméra indisponible sur ce navigateur. Saisissez la référence.');
    const detector=new C({formats:['qr_code']});
    stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});
    if(!active){stream.getTracks().forEach(t=>t.stop());return}
    if(!video.current)throw new Error('Caméra indisponible.');
    video.current.srcObject=stream;await video.current.play();
    const scan=async()=>{
     if(!active||!video.current)return;
     try{const found=await detector.detect(video.current);if(!active)return;const value=found.find(x=>validTicketCode(x.rawValue));if(value){setCamera(false);void lookup(value.rawValue);return}}
     catch{if(active){setError('Lecture QR indisponible. Utilisez la référence.');setCamera(false)}return}
     if(active)timer=window.setTimeout(scan,200);
    };
    void scan();
   }catch(e){if(active){setError(e instanceof Error?e.message:'Caméra indisponible.');setCamera(false)}}
  };
  void run();
  return()=>{active=false;stream?.getTracks().forEach(t=>t.stop());if(timer!==undefined)window.clearTimeout(timer)};
 },[camera,verified]);
 async function validate(){
  if(!ticket||pending.current||!selected.length||!ticket.can_board)return;
  pending.current=true;setBusy(true);setError('');setNotice('');
  try{const result=await companyPost<BoardingTicket>('boarding/validate/',{code:ticket.code,passengers:selected});setTicket(result);setSelected([]);setNotice('Embarquement de test enregistré.');setHistory(null)}catch(e){setError(e instanceof Error?e.message:'Validation impossible.')}finally{pending.current=false;setBusy(false)}
 }
 async function loadHistory(){
  if(pending.current)return;
  pending.current=true;setBusy(true);setError('');
  try{setHistory((await companyGet<{items:Entry[]}>('boarding/history/')).items)}catch(e){setError(e instanceof Error?e.message:'Historique indisponible.')}finally{pending.current=false;setBusy(false)}
 }
 return <section className="boarding-space"><header className="boarding-head"><div><h2>Contrôle des billets</h2><p>{company}</p></div><ScanLine size={24}/></header>
 <p className="boarding-test">MODE TEST — Aucun embarquement réel.</p>
 {!verified?<p className="panel">Ce contrôle est réservé aux compagnies validées.</p>:<div className="panel boarding-panel">
 {error&&<p role="alert" className="auth-error">{error}</p>}{notice&&<p role="status" className="boarding-complete">{notice}</p>}
 {ticket?<><BoardingResult ticket={ticket} selected={selected} onToggle={i=>setSelected(old=>old.includes(i)?old.filter(x=>x!==i):[...old,i])} onAll={()=>setSelected(ticket.passengers.filter(p=>!p.boarded_at).map(p=>p.index))} onValidate={validate} busy={busy}/><button type="button" className="outline" disabled={busy} onClick={()=>{setTicket(null);setCode('');setSelected([]);setNotice('');setError('')}}><ScanLine size={20}/> Scanner un autre billet</button></>:<>
 <button className="primary" type="button" disabled={busy} onClick={()=>{setError('');setCamera(v=>!v)}}><Camera size={20}/>{camera?'Arrêter la caméra':'Ouvrir la caméra'}</button>
 {camera&&<video ref={video} autoPlay muted playsInline className="boarding-video"/>}
 <form className="boarding-manual" onSubmit={e=>{e.preventDefault();void lookup(code)}}><label>Référence du billet<input value={code} onChange={e=>setCode(e.target.value)} maxLength={60} autoComplete="off" placeholder="SRG-TEST-…" disabled={busy}/></label><button className="outline" disabled={busy||!code.trim()} type="submit">{busy?'Recherche…':'Vérifier le billet'}</button></form><small>La caméra dépend du navigateur et de ses autorisations. La référence peut être saisie ou collée.</small></>}
 <button className="outline" type="button" disabled={busy} onClick={loadHistory}><History size={18}/> Historique des embarquements</button>
 {history!==null&&<div className="boarding-history"><h3>Derniers embarquements TEST</h3>{!history.length&&<p>Aucun embarquement.</p>}{history.map(r=><div key={r.id}><strong>{r.name}</strong><small>{r.origin} → {r.destination} · {dayText(r.boarded_at)} · {timeText(r.boarded_at)}</small></div>)}</div>}
 <small className="boarding-footer">Propulsé par BTDIGIT</small></div>}</section>
}

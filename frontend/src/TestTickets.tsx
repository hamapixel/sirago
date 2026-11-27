import {t as tr} from './i18n';
import {useState,lazy,Suspense} from 'react';
import {ArrowLeft,BusFront,Crown,Download,Share2,Ticket,CheckCircle2} from 'lucide-react';
import {useTravel,priceText,timeText} from './travel-api';
import {sandboxTicketsIssued,type Booking,type ReportResult} from './booking-api';
import './tickets.css';
import ReportAction,{reportUnavailableReason} from './ReportAction';
const TicketReport=lazy(()=>import('./TicketReport'));

export type TestTicket={code:string;leg:number;passenger:number;name:string;names?:string[];count?:number;unit_price?:number;category:'Standard'|'Premium';amount:number;company:string;company_city?:string;bus_name?:string;origin:string;destination:string;starts_at:string;ends_at:string;boarding_point:string;arrival_point:string;qr:string[]};
const dateText=(iso:string)=>new Intl.DateTimeFormat('fr-FR',{day:'2-digit',month:'2-digit',year:'numeric',timeZone:'Africa/Bamako'}).format(new Date(iso));
export function TicketCard({ticket:t,bookingId,round=false}:{ticket:TestTicket;bookingId:number;round?:boolean}){
 const [busy,setBusy]=useState(false),[message,setMessage]=useState('');
 const collective=(t.count??1)>1;
 const url='/api/v1/travel/bookings/'+bookingId+'/tickets/'+t.leg+'/'+t.passenger+'/pdf/';
 const path=t.qr.map((row,y)=>Array.from(row,(v,x)=>v==='1'?'M'+x+' '+y+'h1v1h-1z':'').join('')).join('');
 async function share(){
  if(busy)return;
  setBusy(true);setMessage('');
  try{
   const response=await fetch(url,{cache:'no-store',credentials:'same-origin'});
   if(!response.ok)throw new Error('Billet indisponible.');
   const file=new File([await response.blob()],t.code+'.pdf',{type:'application/pdf'});
   if(navigator.share&&navigator.canShare?.({files:[file]})){
    await navigator.share({files:[file],title:'Billet SiraGo TEST'});
   }else{
    const objectUrl=URL.createObjectURL(file);
    const link=document.createElement('a');link.href=objectUrl;link.download=file.name;document.body.appendChild(link);link.click();link.remove();
    window.setTimeout(()=>URL.revokeObjectURL(objectUrl),30000);
    setMessage('PDF téléchargé. Vous pouvez le joindre à votre message.');
   }
  }catch(e){if(!(e instanceof DOMException&&e.name==='AbortError'))setMessage('Partage indisponible. Téléchargez le PDF.')}
  finally{setBusy(false)}
 }
 return <article className="digital-ticket">
  <header className="digital-ticket-head"><div className="digital-ticket-brand"><div><img src="/logo.svg" alt="" width={28} height={28}/><strong>SiraGo</strong></div><span className="digital-ticket-kind"><Ticket size={15}/> {tr("BILLET")}</span></div><div className="digital-ticket-operator"><small>COMPAGNIE DE TRANSPORT</small><h2>{t.company}</h2>{(t.company_city||t.bus_name||round)&&<span>{[t.company_city,t.bus_name,round?(t.leg===0?'Aller':'Retour'):''].filter(Boolean).join(' · ')}</span>}</div><p className="digital-ticket-journey">{t.origin} → {t.destination}</p></header>
  <div className="digital-ticket-body">
   <div className="digital-ticket-route"><div><small>{tr("Départ")}</small><strong>{timeText(t.starts_at)}</strong><b>{t.origin}</b><small>{t.boarding_point}</small></div><BusFront size={23}/><div><small>{tr("Arrivée")}</small><strong>{timeText(t.ends_at)}</strong><b>{t.destination}</b><small>{t.arrival_point}</small>{dateText(t.ends_at)!==dateText(t.starts_at)&&<small>{dateText(t.ends_at)}</small>}</div></div>
   <div className="digital-ticket-fields"><div><small>{collective?"Passagers":"Passager"}</small><b>{collective?`${t.count} personnes`:t.name}</b></div><div><small>{tr("Catégorie")}</small><b className={t.category==='Premium'?'ticket-premium':''}>{t.category==='Premium'&&<Crown size={15}/>} {t.category}</b></div><div><small>{tr("Date")}</small><b>{dateText(t.starts_at)}</b></div><div><small>{collective?"Total":"Montant"}</small><b>{priceText(t.amount)}</b></div></div>
   {collective&&<details className="ticket-passenger-list"><summary>Liste des {t.count} passagers</summary><ol>{t.names?.map((name,i)=><li key={i}>{name}</li>)}</ol><small>Prix unitaire : {priceText(t.unit_price??0)}</small></details>}
   <div className="digital-ticket-qr"><svg role="img" aria-label={collective?"QR code de test collectif":"QR code de test individuel"} viewBox={'0 0 '+t.qr.length+' '+t.qr.length} shapeRendering="crispEdges" xmlns="http://www.w3.org/2000/svg"><rect width={t.qr.length} height={t.qr.length} fill="#fff"/><path d={path} fill="#103b38"/></svg><div className="digital-ticket-qr-copy"><b>{collective?"QR code collectif":"QR code individuel"}</b><small className="digital-ticket-code">{t.code}</small></div></div><span className="digital-ticket-test">{tr("Simulation — Non valable pour voyager")}</span>
   <div className="digital-ticket-actions"><a href={url} download><Download size={20}/>{tr("Télécharger")}</a><button type="button" disabled={busy} onClick={share}><Share2 size={20}/>{busy?'Partage…':'Partager'}</button></div>
   {message&&<small role="status">{message}</small>}
  </div>
 </article>
}
export default function TestTickets({booking:initial,onBack,initialReport=false}:{booking:Booking;onBack:()=>void;initialReport?:boolean}){
 const [replacements,setReplacements]=useState<Booking[]>([]),[activeId,setActiveId]=useState<number|null>(null),[reporting,setReporting]=useState(initialReport&&!reportUnavailableReason(initial));
 const booking=replacements.find(b=>b.id===activeId)??initial;
 function reported(b:ReportResult){setReplacements(old=>[...old.filter(x=>x.id!==booking.id),b,...(b.retained_booking?[b.retained_booking]:[])]);setActiveId(b.id);setReporting(false)}
 const enabled=booking.status==='TEST_PAID'&&!!booking.simulation_enabled;
 const q=useTravel<{items:TestTicket[]}>(enabled?'bookings/'+booking.id+'/tickets/':null,0);
 if(reporting)return <Suspense fallback={<p role="status">Chargement du report…</p>}><TicketReport booking={booking} onBack={()=>setReporting(false)} onReported={reported}/></Suspense>;
 return <section className="booking-space booking-details ticket-screen"><div className="travel-heading booking-heading"><div className="travel-heading-top"><button type="button" onClick={onBack}><ArrowLeft size={19}/> {tr("Retour")}</button><Ticket size={22}/></div><h1>{tr("Mes billets")}</h1><p>{booking.ticket_mode==="group"?"Un billet par catégorie et par trajet.":"Un billet par passager et par trajet."}</p></div>
 {!enabled?<p className="panel">Billets de test indisponibles.</p>:<><article className="panel booking-checkout ticket-success"><CheckCircle2 size={23}/><div><strong>{sandboxTicketsIssued(booking)?'Paiement SasPay Sandbox réussi':'Paiement simulé réussi'}</strong><p>Aucun argent débité.</p></div></article>
 {replacements.length>0&&<p className="panel profile-success" role="status">Report de test enregistré. Les anciens QR codes ne sont plus valides. Distribuez les nouveaux billets.</p>}
 {replacements.length>1&&<article className="panel ticket-report-groups"><h2>Nouvelles réservations</h2>{replacements.map(b=><button type="button" className="outline" key={b.id} aria-pressed={booking.id===b.id} onClick={()=>setActiveId(b.id)}><strong>{dateText(b.trips[0].starts_at)} · {timeText(b.trips[0].starts_at)}</strong>{b.trips.length===2&&<small>Retour : {dateText(b.trips[1].starts_at)} · {timeText(b.trips[1].starts_at)}</small>}<small>{b.count} passager(s) · {priceText(b.total)}</small></button>)}</article>}
 <ReportAction booking={booking} onReport={()=>setReporting(true)}/>
 {q.loading&&<p role="status">Chargement des billets…</p>}{q.error&&<article className="panel booking-checkout" role="alert">{q.error}<button className="outline" onClick={q.retry}>{tr("Réessayer")}</button></article>}
 <div className="ticket-list-title"><h2>{tr("Billets numériques")}</h2><small>{q.data?.items.length??0} billet(s)</small></div><div className="digital-ticket-list">{q.data?.items.map(t=><TicketCard key={t.code} ticket={t} bookingId={booking.id} round={booking.trips.length>1}/>)}</div></>}
 </section>
}

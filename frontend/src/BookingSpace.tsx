import {useState,useEffect,useRef} from 'react';
import {ArrowLeft,BusFront,Clock,LockKeyhole,ShieldCheck,Ticket,Users} from 'lucide-react';
import {useTravel,priceText,timeText,dayText,minimumTripTotal} from './travel-api';
import {bookingPost,selectionQuery,attemptKey,clearAttempt,bookingLabel,effectiveBookingStatus,normalizePassengerName,validPassengerNames,defaultPremiumPositions,categoryTotal,validCategories,type Selection,type Quote,type Booking} from './booking-api';
import {type Account} from './auth-api';
import './booking.css';
import SeatCategoryCards from './SeatCategoryCards';
import PaymentPreview from './PaymentPreview';
import TestTickets from './TestTickets';
import ReportAction from './ReportAction';

export function QuoteSummary({quote,positions}:{quote:Quote;positions?:number[][]}){
 return <div className="booking-summary">{quote.trips.map((t,i)=><div className="booking-leg" key={t.id}><BusFront size={22}/><div><small>{i===0?'Aller':'Retour'} · {t.company}</small><strong>{t.origin} → {t.destination}</strong><p>{dayText(t.starts_at)} · {timeText(t.starts_at)} – {timeText(t.ends_at)}</p><small>{t.remaining} places restantes</small></div><strong>{priceText(positions?categoryTotal(t,quote.count,positions[i]):minimumTripTotal(t,quote.count))}</strong></div>)}<div className="booking-total"><span><Users size={18}/> {quote.count} passager(s)</span><strong>{priceText(positions?quote.trips.reduce((sum,t,i)=>sum+categoryTotal(t,quote.count,positions[i]),0):quote.total)}</strong></div></div>
}
export function AuthTrip({selection}:{selection:Selection}){
 const q=useTravel<Quote>('quote/'+selectionQuery(selection),0);
 return <section className="panel auth-trip"><h2><LockKeyhole size={20}/> Votre réservation</h2>{q.loading?<p>Vérification du départ…</p>:q.error?<p role="alert">{q.error} Refaites une recherche.</p>:q.data?<QuoteSummary quote={q.data}/>:null}<small>Places non bloquées.</small></section>
}
function Countdown({expires}:{expires:string}){
 const [now,setNow]=useState(Date.now());
 useEffect(()=>{const timer=window.setInterval(()=>setNow(Date.now()),1000);return()=>window.clearInterval(timer)},[]);
 const seconds=Math.max(0,Math.ceil((Date.parse(expires)-now)/1000));
 return <span>{seconds?Math.floor(seconds/60)+':'+String(seconds%60).padStart(2,'0'):'Expirée'}</span>
}
export default function BookingSpace({selection,account,onHistory}:{selection:Selection;account:Account;onHistory:()=>void}){
 const q=useTravel<Quote>('quote/'+selectionQuery(selection),0);
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[booked,setBooked]=useState<Booking|null>(null);
 const [showDetails,setShowDetails]=useState(false),[showPayment,setShowPayment]=useState(false);
 const [ticketMode,setTicketMode]=useState<"group"|"individual">("group");
 const [names,setNames]=useState<string[]>(()=>Array.from({length:selection.count},(_,i)=>i===0?[account.first_name,account.last_name].filter(Boolean).join(" "):""));
 const namesValid=validPassengerNames(names,selection.count);
 const [choices,setChoices]=useState<Record<number,number[]>>({});
 const positions=q.data?.trips.map(t=>choices[t.id]??defaultPremiumPositions(t,selection.count))??[];
 const categoriesValid=!!q.data&&q.data.trips.every((t,i)=>validCategories(t,selection.count,positions[i]));
 const total=q.data?.trips.reduce((sum,t,i)=>sum+categoryTotal(t,selection.count,positions[i]),0)??0;
 function chooseCategory(leg:number,passenger:number,premium:boolean){const t=q.data?.trips[leg];if(!t)return;const current=positions[leg];const next=premium?[...new Set([...current,passenger])].sort((a,b)=>a-b):current.filter(p=>p!==passenger);setChoices(old=>({...old,[t.id]:next}))}
 const submitting=useRef(false);
 async function reserve(){
  if(submitting.current||!q.data||!namesValid||!categoriesValid)return;
  submitting.current=true;setBusy(true);setError('');
  try{const result=await bookingPost<Booking>('bookings/reserve/',{...selection,request_id:attemptKey(selection),total,ticket_mode:ticketMode,premium_positions:positions,passenger_names:names.map(normalizePassengerName)});setBooked(result);clearAttempt(selection)}
  catch(e){setError(e instanceof Error?e.message:'Réservation impossible.');q.retry()}
  finally{submitting.current=false;setBusy(false)}
 }
 if(booked&&showPayment)return <BookingDetails id={booked.id} initialPayment onBack={()=>setShowPayment(false)}/>;
 if(booked&&showDetails)return <BookingDetails id={booked.id} onBack={onHistory}/>;
 return <section className="booking-space booking-details"><div className="travel-heading"><a className="booking-back" href="/app/"><ArrowLeft size={18}/> Retour</a><h1>{booked?'Réservation enregistrée':'Confirmer le voyage'}</h1><p>{account.first_name} · SiraGo</p></div>
 {booked?<article className="panel booking-success"><ShieldCheck size={32}/><h2>{bookingLabel(booked.status)}</h2><p>Référence : {booked.reference}</p><h3>{priceText(booked.total)}</h3>{booked.status==='HELD'&&<><p><Clock size={17}/> Places bloquées : <Countdown expires={booked.expires_at}/></p><p>Aucun débit effectué.</p><button className="primary" onClick={()=>setShowPayment(true)}>Continuer vers le paiement</button></>}<button className="outline" onClick={()=>setShowDetails(true)}>Voir les détails</button><button className="outline" onClick={onHistory}>Mes réservations</button></article>:<>
 {q.loading&&<p className="panel" role="status">Vérification du voyage…</p>}
 {q.error&&<div className="panel" role="alert">{q.error}<button className="outline" onClick={q.retry}>Réessayer</button></div>}
 {q.data&&<>
 <article className="panel booking-checkout"><h2>Votre voyage</h2><QuoteSummary quote={q.data} positions={positions}/></article>
 <article className="panel booking-checkout"><h2>Passagers</h2><p className="muted">Un nom par passager. Sièges attribués par la compagnie.</p>
 {names.map((name,i)=><div className="passenger-config" key={i}><div className="passenger-config-head"><span className="passenger-number">{i+1}</span><strong>Passager {i+1}</strong><small>{priceText(q.data!.trips.reduce((sum,t,j)=>sum+(positions[j].includes(i)?t.premium_price:t.price),0))}</small></div><label htmlFor={'passenger-'+i}>Nom complet</label><input id={'passenger-'+i} autoComplete={i===0?'name':'off'} maxLength={100} value={name} disabled={busy} placeholder="Nom et prénom" required onChange={e=>setNames(old=>old.map((n,j)=>j===i?e.target.value:n))}/>{q.data!.trips.map((t,j)=><div key={t.id} className="passenger-category">{q.data!.trips.length>1&&<small>{j===0?'Aller':'Retour'}</small>}<SeatCategoryCards trip={t} premium={positions[j].includes(i)} disabled={busy} label={`Type de place, passager ${i+1}${q.data!.trips.length>1?(j===0?' aller':' retour'):''}`} onChange={value=>chooseCategory(j,i,value)}/></div>)}</div>)}
 </article>
 {selection.count>1&&<article className="panel booking-checkout"><h2>Format des billets</h2><div className="ticket-mode-options" role="group" aria-label="Format des billets"><button type="button" className={'outline '+(ticketMode==='group'?'selected':'')} aria-pressed={ticketMode==='group'} disabled={busy} onClick={()=>setTicketMode('group')}><Users size={22}/><span><strong>Billets collectifs</strong><small>Un billet par catégorie et par trajet.</small></span></button><button type="button" className={'outline '+(ticketMode==='individual'?'selected':'')} aria-pressed={ticketMode==='individual'} disabled={busy} onClick={()=>setTicketMode('individual')}><Ticket size={22}/><span><strong>Billets individuels</strong><small>Un billet par passager et par trajet.</small></span></button></div><small>Nombre de billets : {ticketMode==='individual'?selection.count*positions.length:positions.reduce((sum,p)=>sum+Number(p.length>0)+Number(p.length<selection.count),0)}</small></article>}
 <article className="panel booking-checkout"><div className="booking-total"><strong>Total</strong><strong>{priceText(total)}</strong></div><div className="booking-info"><Clock size={20}/><p>Blocage : 15 min max. Aucun débit.</p></div>{!namesValid&&<small role="status">Renseignez tous les noms.</small>}{!categoriesValid&&<small role="alert">Places insuffisantes dans une catégorie. Modifiez votre choix.</small>}<button className="primary" disabled={busy||!namesValid||!categoriesValid} onClick={reserve}>{busy?'Enregistrement…':'Confirmer'}</button></article></>}
 {error&&<p className="auth-error" role="alert">{error}</p>}</>}
 </section>
}
export function MyBookings({account,onSearch}:{account:Account|null;onSearch:()=>void}){
 const [page,setPage]=useState(1),[busy,setBusy]=useState(false),[error,setError]=useState(''),[confirm,setConfirm]=useState<number|null>(null);
 const [detailId,setDetailId]=useState<number|null>(null),[startReport,setStartReport]=useState(false);
 const q=useTravel<{items:Booking[];has_next:boolean}>(account?.role==='TRAVELER'?'bookings/?page='+page:null,0);
 async function cancel(id:number){if(busy)return;setBusy(true);setError('');try{await bookingPost('bookings/'+id+'/cancel/',{});setConfirm(null);q.retry()}catch(e){setError(e instanceof Error?e.message:'Annulation impossible.')}finally{setBusy(false)}}
 if(detailId!==null&&account?.role==='TRAVELER')return <BookingDetails id={detailId} initialReport={startReport} onBack={()=>{setDetailId(null);setStartReport(false);q.retry()}}/>;
 return <section className="booking-space"><div className="travel-heading"><Ticket size={26}/><h1>Mes billets</h1><p>Consultez vos réservations et gérez vos voyages.</p></div>{!account?<div className="panel booking-checkout"><p>Connectez-vous pour voir vos réservations.</p><a className="primary" href="/login/">Se connecter</a></div>:<>
 <button className="outline" onClick={q.retry}>Actualiser</button>{q.loading&&<p role="status">Chargement…</p>}{q.error&&<p role="alert">{q.error}</p>}{error&&<p className="auth-error" role="alert">{error}</p>}
 {q.data?.items.length===0&&<div className="panel booking-checkout"><p>Aucune réservation.</p><button className="primary" onClick={onSearch}>Rechercher un voyage</button></div>}
 {q.data?.items.map(b=><article className="panel booking-checkout" key={b.id}><div className="booking-total"><strong>{bookingLabel(b.status)}</strong><strong>{priceText(b.total)}</strong></div><small>Réf. {b.reference}</small>{b.trips.map(t=><div key={t.id}><strong>{t.origin} → {t.destination}</strong><p>{t.company} · {dayText(t.starts_at)} · {timeText(t.starts_at)}</p></div>)}<p>{b.count} passager(s)</p><button className="outline" onClick={()=>{setStartReport(false);setDetailId(b.id)}}>{b.status==="TEST_PAID"&&b.simulation_enabled?"Voir mes billets":"Voir les détails"}</button>{(b.status==='TEST_PAID'||b.status==='REPORTED')&&<ReportAction booking={b} onReport={()=>{setStartReport(true);setDetailId(b.id)}}/>}{b.status==='HELD'&&<><small>Expiration : <Countdown expires={b.expires_at}/></small>{confirm===b.id?<div className="booking-actions"><p>Libérer les places ?</p><button className="outline" disabled={busy} onClick={()=>setConfirm(null)}>Retour</button><button className="primary" disabled={busy} onClick={()=>cancel(b.id)}>Confirmer</button></div>:<button className="outline" onClick={()=>setConfirm(b.id)}>Annuler</button>}</>}</article>)}
 {q.data&&(page>1||q.data.has_next)&&<div className="booking-actions"><button className="outline" disabled={page===1} onClick={()=>setPage(p=>p-1)}>Précédent</button><button className="outline" disabled={!q.data.has_next} onClick={()=>setPage(p=>p+1)}>Suivant</button></div>}</>}
 </section>
}

function BookingDetails({id,onBack,initialPayment=false,initialReport=false}:{id:number;onBack:()=>void;initialPayment?:boolean;initialReport?:boolean}){
 const q=useTravel<Booking>('bookings/'+id+'/',0);
 const [now,setNow]=useState(Date.now()),[busy,setBusy]=useState(false),[confirm,setConfirm]=useState(false),[error,setError]=useState('');
 const dialog=useRef<HTMLDialogElement>(null),submitting=useRef(false);
 useEffect(()=>{const timer=window.setInterval(()=>setNow(Date.now()),1000);return()=>window.clearInterval(timer)},[]);
 useEffect(()=>{const el=dialog.current;if(confirm&&el&&!el.open)el.showModal();return()=>{if(el?.open)el.close()}},[confirm]);
 const [payment,setPayment]=useState(initialPayment),[showTickets,setShowTickets]=useState(true),[reportRequested,setReportRequested]=useState(initialReport);
 const b=q.data;
 const status=b?effectiveBookingStatus(b,now):null;
 async function cancel(){
  if(submitting.current||status!=='HELD')return;
  submitting.current=true;setBusy(true);setError('');
  try{await bookingPost<Booking>('bookings/'+id+'/cancel/',{});q.retry();setConfirm(false)}
  catch(e){setError(e instanceof Error?e.message:'Annulation impossible.');setConfirm(false)}
  finally{setBusy(false);submitting.current=false}
 }
 if(b&&status==='TEST_PAID'&&b.simulation_enabled&&!q.loading&&!q.error&&showTickets)return <TestTickets booking={b} initialReport={reportRequested} onBack={()=>{setShowTickets(false);setReportRequested(false);setPayment(false);q.retry()}}/>;
 if(payment&&b&&!q.loading&&!q.error)return <PaymentPreview booking={b} onBack={()=>{setPayment(false);q.retry()}}/>;
 return <section className="booking-space booking-details">
 <div className="travel-heading"><div className="travel-heading-top"><button onClick={onBack} disabled={busy}><ArrowLeft size={19}/> Retour</button><Ticket size={23}/></div><h1>Détails de la réservation</h1><p>Consultez votre voyage.</p></div>
 {q.loading&&<p className="panel" role="status">Chargement…</p>}
 {q.error&&<div className="panel booking-checkout" role="alert"><p>{q.error}</p><button className="outline" onClick={q.retry}>Réessayer</button></div>}
 {error&&<p role="alert" className="auth-error">{error}</p>}
 {b&&status&&<>
 <article className="panel booking-checkout"><div className="booking-total"><strong>Réservation</strong><span className={'booking-state '+status.toLowerCase()}>{bookingLabel(status)}</span></div><small>Réf. {b.reference}</small><small>Créée le {dayText(b.created_at)} · {timeText(b.created_at)}</small><div className="booking-total"><span><Users size={18}/> {b.count} passager(s)</span><strong>{priceText(b.total)}</strong></div></article>
 {b.passenger_names.length>0&&<article className="panel booking-checkout"><h2>Passagers</h2>{b.passenger_names.map((name,i)=><div className="passenger-config-head" key={i}><span className="passenger-number">{i+1}</span><strong>{name}</strong><small>{b.trips.map((t,j)=>(b.trips.length>1?(j===0?'Aller : ':'Retour : '):'')+(t.premium_positions.includes(i)?'Premium':'Standard')).join(' · ')}</small></div>)}</article>}
 {b.trips.map((t,i)=><article key={t.id} className="panel booking-checkout"><div className="trip-company"><div className="trip-logo"><BusFront size={23}/></div><div><strong>{t.company}</strong><small>{i===0?'Aller':'Retour'} · {t.bus_name}</small></div></div><small>{dayText(t.starts_at)}</small><div className="trip-timeline"><div className="trip-stop"><strong className="trip-time">{timeText(t.starts_at)}</strong><b>{t.origin}</b><small>{t.boarding_point}</small></div><div className="trip-middle"><div className="trip-line"><i/><span/><i/></div><BusFront size={20}/></div><div className="trip-stop arrival"><strong className="trip-time">{timeText(t.ends_at)}</strong><b>{t.destination}</b><small>{t.arrival_point}</small>{dayText(t.ends_at)!==dayText(t.starts_at)&&<small>{dayText(t.ends_at)}</small>}</div></div><div className="booking-total"><small>{b.count-t.premium_positions.length} Standard{t.premium_positions.length>0?` · ${t.premium_positions.length} Premium`: ''}</small><strong>{priceText(t.total)}</strong></div></article>)}
 <article className="panel booking-checkout"><h2>Paiement</h2><div className="booking-total"><span>Montant à payer</span><strong>{priceText(status==='HELD'?b.total:0)}</strong></div><div className="booking-total"><span>Montant payé</span><strong>0 FCFA</strong></div>{status==="REPORTED"?<><p>Cette réservation a été reportée. Ses anciens billets ne sont plus utilisables.</p><small>Retrouvez {b.retained_id?'les deux nouvelles réservations':'la réservation de remplacement'} dans Mes billets.</small></>:status==="TEST_PAID"?<><p><ShieldCheck size={18}/> Simulation réussie · Aucun débit réel.</p><p>Montant simulé : {priceText(b.simulated_payment?.amount??b.total)}</p><small>Aucun billet valable pour voyager.</small>{b.simulation_enabled&&<button className="primary" onClick={()=>{setReportRequested(false);setShowTickets(true)}}>Voir mes billets de test</button>}<ReportAction booking={b} now={now} onReport={()=>{setPayment(false);setReportRequested(true);setShowTickets(true)}}/></>:<p>Aucun paiement enregistré. Aucun billet émis.</p>}{status==='HELD'&&<><div className="booking-info"><Clock size={20}/><p>Places bloquées : <Countdown expires={b.expires_at}/></p></div><button className="primary" disabled={busy} onClick={()=>setPayment(true)}>Continuer vers le paiement</button></>}</article>
 {status==='HELD'&&<button className="outline booking-danger" onClick={()=>setConfirm(true)} disabled={busy}>Annuler la réservation</button>}
 <button className="outline" onClick={q.retry} disabled={busy}>Actualiser</button>
 </>}
 {confirm&&<dialog ref={dialog} className="booking-dialog" aria-labelledby="booking-cancel-title" onCancel={e=>{e.preventDefault();if(!busy)setConfirm(false)}}><h2 id="booking-cancel-title">Annuler la réservation ?</h2><p>Les places seront libérées.</p><div className="booking-actions"><button autoFocus className="outline" disabled={busy} onClick={()=>setConfirm(false)}>Retour</button><button className="primary booking-danger-solid" disabled={busy||status!=='HELD'} onClick={cancel}>{busy?'Annulation…':'Confirmer'}</button></div></dialog>}
 </section>
}

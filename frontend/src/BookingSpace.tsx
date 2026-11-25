import {useState,useEffect,useRef} from 'react';
import {ArrowLeft,BusFront,Clock,LockKeyhole,ShieldCheck,Ticket,Users} from 'lucide-react';
import {useTravel,priceText,timeText,dayText} from './travel-api';
import {bookingPost,selectionQuery,attemptKey,clearAttempt,bookingLabel,effectiveBookingStatus,normalizePassengerName,validPassengerNames,type Selection,type Quote,type Booking} from './booking-api';
import {type Account} from './auth-api';
import './booking.css';

export function QuoteSummary({quote}:{quote:Quote}){
 return <div className="booking-summary">{quote.trips.map((t,i)=><div className="booking-leg" key={t.id}><BusFront size={22}/><div><small>{i===0?'Aller':'Retour'} · {t.company}</small><strong>{t.origin} → {t.destination}</strong><p>{dayText(t.starts_at)} · {timeText(t.starts_at)} – {timeText(t.ends_at)}</p><small>{t.remaining} places restantes</small></div><strong>{priceText(t.price*quote.count)}</strong></div>)}<div className="booking-total"><span><Users size={18}/> {quote.count} passager(s)</span><strong>{priceText(quote.total)}</strong></div></div>
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
 const [showDetails,setShowDetails]=useState(false);
 const [names,setNames]=useState<string[]>(()=>Array.from({length:selection.count},(_,i)=>i===0?[account.first_name,account.last_name].filter(Boolean).join(" "):""));
 const namesValid=validPassengerNames(names,selection.count);
 const submitting=useRef(false);
 async function reserve(){
  if(submitting.current||!q.data||!namesValid)return;
  submitting.current=true;setBusy(true);setError('');
  try{const result=await bookingPost<Booking>('bookings/reserve/',{...selection,request_id:attemptKey(selection),total:q.data.total,passenger_names:names.map(normalizePassengerName)});setBooked(result);clearAttempt(selection)}
  catch(e){setError(e instanceof Error?e.message:'Réservation impossible.');q.retry()}
  finally{submitting.current=false;setBusy(false)}
 }
 if(booked&&showDetails)return <BookingDetails id={booked.id} onBack={onHistory}/>;
 return <section className="booking-space booking-details"><div className="travel-heading"><a className="booking-back" href="/app/"><ArrowLeft size={18}/> Retour</a><h1>{booked?'Réservation enregistrée':'Confirmer le voyage'}</h1><p>{account.first_name} · SiraGo</p></div>
 {booked?<article className="panel booking-success"><ShieldCheck size={32}/><h2>{bookingLabel(booked.status)}</h2><p>Référence : {booked.reference}</p><h3>{priceText(booked.total)}</h3>{booked.status==='HELD'&&<><p><Clock size={17}/> Places bloquées : <Countdown expires={booked.expires_at}/></p><p>Paiement à venir. Aucun billet émis.</p></>}<button className="primary" onClick={()=>setShowDetails(true)}>Voir les détails</button><button className="outline" onClick={onHistory}>Mes réservations</button></article>:<>
 {q.loading&&<p className="panel" role="status">Vérification du voyage…</p>}
 {q.error&&<div className="panel" role="alert">{q.error}<button className="outline" onClick={q.retry}>Réessayer</button></div>}
 {q.data&&<>
 <article className="panel booking-checkout"><h2>Votre voyage</h2><QuoteSummary quote={q.data}/></article>
 <article className="panel booking-checkout"><h2>Passagers</h2><p className="muted">Un nom par passager. Sièges attribués par la compagnie.</p>
 {names.map((name,i)=><div className="passenger-config" key={i}><div className="passenger-config-head"><span className="passenger-number">{i+1}</span><strong>Passager {i+1}</strong><small>{priceText(q.data!.trips.reduce((sum,t)=>sum+t.price,0))}</small></div><label htmlFor={'passenger-'+i}>Nom complet</label><input id={'passenger-'+i} autoComplete={i===0?'name':'off'} maxLength={100} value={name} disabled={busy} placeholder="Nom et prénom" required onChange={e=>setNames(old=>old.map((n,j)=>j===i?e.target.value:n))}/><small>Standard</small></div>)}
 </article>
 <article className="panel booking-checkout"><div className="booking-total"><strong>Total</strong><strong>{priceText(q.data.total)}</strong></div><div className="booking-info"><Clock size={20}/><p>Blocage : 15 min max. Aucun débit.</p></div>{!namesValid&&<small role="status">Renseignez tous les noms.</small>}<button className="primary" disabled={busy||!namesValid} onClick={reserve}>{busy?'Enregistrement…':'Confirmer'}</button></article></>}
 {error&&<p className="auth-error" role="alert">{error}</p>}</>}
 </section>
}
export function MyBookings({account,onSearch}:{account:Account|null;onSearch:()=>void}){
 const [page,setPage]=useState(1),[busy,setBusy]=useState(false),[error,setError]=useState(''),[confirm,setConfirm]=useState<number|null>(null);
 const [detailId,setDetailId]=useState<number|null>(null);
 const q=useTravel<{items:Booking[];has_next:boolean}>(account?.role==='TRAVELER'?'bookings/?page='+page:null,0);
 async function cancel(id:number){if(busy)return;setBusy(true);setError('');try{await bookingPost('bookings/'+id+'/cancel/',{});setConfirm(null);q.retry()}catch(e){setError(e instanceof Error?e.message:'Annulation impossible.')}finally{setBusy(false)}}
 if(detailId!==null&&account?.role==='TRAVELER')return <BookingDetails id={detailId} onBack={()=>{setDetailId(null);q.retry()}}/>;
 return <section className="booking-space"><div className="travel-heading"><Ticket size={26}/><h1>Mes réservations</h1><p>Suivez vos voyages.</p></div>{!account?<div className="panel booking-checkout"><p>Connectez-vous pour voir vos réservations.</p><a className="primary" href="/login/">Se connecter</a></div>:<>
 <button className="outline" onClick={q.retry}>Actualiser</button>{q.loading&&<p role="status">Chargement…</p>}{q.error&&<p role="alert">{q.error}</p>}{error&&<p className="auth-error" role="alert">{error}</p>}
 {q.data?.items.length===0&&<div className="panel booking-checkout"><p>Aucune réservation.</p><button className="primary" onClick={onSearch}>Rechercher un voyage</button></div>}
 {q.data?.items.map(b=><article className="panel booking-checkout" key={b.id}><div className="booking-total"><strong>{bookingLabel(b.status)}</strong><strong>{priceText(b.total)}</strong></div><small>Réf. {b.reference}</small>{b.trips.map(t=><div key={t.id}><strong>{t.origin} → {t.destination}</strong><p>{t.company} · {dayText(t.starts_at)} · {timeText(t.starts_at)}</p></div>)}<p>{b.count} passager(s)</p><button className="outline" onClick={()=>setDetailId(b.id)}>Voir les détails</button>{b.status==='HELD'&&<><small>Expiration : <Countdown expires={b.expires_at}/></small>{confirm===b.id?<div className="booking-actions"><p>Libérer les places ?</p><button className="outline" disabled={busy} onClick={()=>setConfirm(null)}>Retour</button><button className="primary" disabled={busy} onClick={()=>cancel(b.id)}>Confirmer</button></div>:<button className="outline" onClick={()=>setConfirm(b.id)}>Annuler</button>}</>}</article>)}
 {q.data&&(page>1||q.data.has_next)&&<div className="booking-actions"><button className="outline" disabled={page===1} onClick={()=>setPage(p=>p-1)}>Précédent</button><button className="outline" disabled={!q.data.has_next} onClick={()=>setPage(p=>p+1)}>Suivant</button></div>}</>}
 </section>
}

function BookingDetails({id,onBack}:{id:number;onBack:()=>void}){
 const q=useTravel<Booking>('bookings/'+id+'/',0);
 const [now,setNow]=useState(Date.now()),[busy,setBusy]=useState(false),[confirm,setConfirm]=useState(false),[error,setError]=useState('');
 const dialog=useRef<HTMLDialogElement>(null),submitting=useRef(false);
 useEffect(()=>{const timer=window.setInterval(()=>setNow(Date.now()),1000);return()=>window.clearInterval(timer)},[]);
 useEffect(()=>{const el=dialog.current;if(confirm&&el&&!el.open)el.showModal();return()=>{if(el?.open)el.close()}},[confirm]);
 const b=q.data;
 const status=b?effectiveBookingStatus(b,now):null;
 async function cancel(){
  if(submitting.current||status!=='HELD')return;
  submitting.current=true;setBusy(true);setError('');
  try{await bookingPost<Booking>('bookings/'+id+'/cancel/',{});q.retry();setConfirm(false)}
  catch(e){setError(e instanceof Error?e.message:'Annulation impossible.');setConfirm(false)}
  finally{setBusy(false);submitting.current=false}
 }
 return <section className="booking-space booking-details">
 <div className="travel-heading"><div className="travel-heading-top"><button onClick={onBack} disabled={busy}><ArrowLeft size={19}/> Retour</button><Ticket size={23}/></div><h1>Détails de la réservation</h1><p>Consultez votre voyage.</p></div>
 {q.loading&&<p className="panel" role="status">Chargement…</p>}
 {q.error&&<div className="panel booking-checkout" role="alert"><p>{q.error}</p><button className="outline" onClick={q.retry}>Réessayer</button></div>}
 {error&&<p role="alert" className="auth-error">{error}</p>}
 {b&&status&&<>
 <article className="panel booking-checkout"><div className="booking-total"><strong>Réservation</strong><span className={'booking-state '+status.toLowerCase()}>{bookingLabel(status)}</span></div><small>Réf. {b.reference}</small><small>Créée le {dayText(b.created_at)} · {timeText(b.created_at)}</small><div className="booking-total"><span><Users size={18}/> {b.count} passager(s)</span><strong>{priceText(b.total)}</strong></div></article>
 {b.passenger_names.length>0&&<article className="panel booking-checkout"><h2>Passagers</h2>{b.passenger_names.map((name,i)=><div className="passenger-config-head" key={i}><span className="passenger-number">{i+1}</span><strong>{name}</strong></div>)}</article>}
 {b.trips.map((t,i)=><article key={t.id} className="panel booking-checkout"><div className="trip-company"><div className="trip-logo"><BusFront size={23}/></div><div><strong>{t.company}</strong><small>{i===0?'Aller':'Retour'} · {t.bus_name}</small></div></div><small>{dayText(t.starts_at)}</small><div className="trip-timeline"><div className="trip-stop"><strong className="trip-time">{timeText(t.starts_at)}</strong><b>{t.origin}</b><small>{t.boarding_point}</small></div><div className="trip-middle"><div className="trip-line"><i/><span/><i/></div><BusFront size={20}/></div><div className="trip-stop arrival"><strong className="trip-time">{timeText(t.ends_at)}</strong><b>{t.destination}</b><small>{t.arrival_point}</small>{dayText(t.ends_at)!==dayText(t.starts_at)&&<small>{dayText(t.ends_at)}</small>}</div></div><div className="booking-total"><small>{priceText(t.price)} / passager</small><strong>{priceText(t.price*b.count)}</strong></div></article>)}
 <article className="panel booking-checkout"><h2>Paiement</h2><div className="booking-total"><span>Montant à payer</span><strong>{priceText(status==='HELD'?b.total:0)}</strong></div><div className="booking-total"><span>Montant payé</span><strong>0 FCFA</strong></div><p>Paiement à venir. Aucun billet émis.</p>{status==='HELD'&&<div className="booking-info"><Clock size={20}/><p>Places bloquées : <Countdown expires={b.expires_at}/></p></div>}</article>
 {status==='HELD'&&<button className="outline booking-danger" onClick={()=>setConfirm(true)} disabled={busy}>Annuler la réservation</button>}
 <button className="outline" onClick={q.retry} disabled={busy}>Actualiser</button>
 </>}
 {confirm&&<dialog ref={dialog} className="booking-dialog" aria-labelledby="booking-cancel-title" onCancel={e=>{e.preventDefault();if(!busy)setConfirm(false)}}><h2 id="booking-cancel-title">Annuler la réservation ?</h2><p>Les places seront libérées.</p><div className="booking-actions"><button autoFocus className="outline" disabled={busy} onClick={()=>setConfirm(false)}>Retour</button><button className="primary booking-danger-solid" disabled={busy||status!=='HELD'} onClick={cancel}>{busy?'Annulation…':'Confirmer'}</button></div></dialog>}
 </section>
}

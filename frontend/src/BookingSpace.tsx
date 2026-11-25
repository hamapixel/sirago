import {useState,useEffect,useRef} from 'react';
import {ArrowLeft,BusFront,Clock,LockKeyhole,ShieldCheck,Ticket,Users} from 'lucide-react';
import {useTravel,priceText,timeText,dayText} from './travel-api';
import {bookingPost,selectionQuery,attemptKey,clearAttempt,bookingLabel,type Selection,type Quote,type Booking} from './booking-api';
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
 const submitting=useRef(false);
 async function reserve(){
  if(submitting.current||!q.data)return;
  submitting.current=true;setBusy(true);setError('');
  try{const result=await bookingPost<Booking>('bookings/reserve/',{...selection,request_id:attemptKey(selection),total:q.data.total});setBooked(result);clearAttempt(selection)}
  catch(e){setError(e instanceof Error?e.message:'Réservation impossible.');q.retry()}
  finally{submitting.current=false;setBusy(false)}
 }
 return <section className="booking-space"><div className="travel-heading"><a className="booking-back" href="/app/"><ArrowLeft size={18}/> Retour</a><h1>{booked?'Réservation enregistrée':'Confirmer le voyage'}</h1><p>{account.first_name} · SiraGo</p></div>
 {booked?<article className="panel booking-success"><ShieldCheck size={32}/><h2>{bookingLabel(booked.status)}</h2><p>Référence : {booked.reference}</p><h3>{priceText(booked.total)}</h3>{booked.status==='HELD'&&<><p><Clock size={17}/> Places bloquées : <Countdown expires={booked.expires_at}/></p><p>Paiement à venir. Aucun billet émis.</p></>}<button className="primary" onClick={onHistory}>Mes réservations</button></article>:<>
 {q.loading&&<p className="panel" role="status">Vérification du voyage…</p>}
 {q.error&&<div className="panel" role="alert">{q.error}<button className="outline" onClick={q.retry}>Réessayer</button></div>}
 {q.data&&<article className="panel booking-checkout"><h2>Votre voyage</h2><QuoteSummary quote={q.data}/><div className="booking-info"><Clock size={20}/><p>Blocage : 15 min max. Aucun débit.</p></div><button className="primary" disabled={busy} onClick={reserve}>{busy?'Enregistrement…':'Confirmer'}</button></article>}
 {error&&<p className="auth-error" role="alert">{error}</p>}</>}
 </section>
}
export function MyBookings({account,onSearch}:{account:Account|null;onSearch:()=>void}){
 const [page,setPage]=useState(1),[busy,setBusy]=useState(false),[error,setError]=useState(''),[confirm,setConfirm]=useState<number|null>(null);
 const q=useTravel<{items:Booking[];has_next:boolean}>(account?.role==='TRAVELER'?'bookings/?page='+page:null,0);
 async function cancel(id:number){if(busy)return;setBusy(true);setError('');try{await bookingPost('bookings/'+id+'/cancel/',{});setConfirm(null);q.retry()}catch(e){setError(e instanceof Error?e.message:'Annulation impossible.')}finally{setBusy(false)}}
 return <section className="booking-space"><div className="travel-heading"><Ticket size={26}/><h1>Mes réservations</h1><p>Suivez vos voyages.</p></div>{!account?<div className="panel booking-checkout"><p>Connectez-vous pour voir vos réservations.</p><a className="primary" href="/login/">Se connecter</a></div>:<>
 <button className="outline" onClick={q.retry}>Actualiser</button>{q.loading&&<p role="status">Chargement…</p>}{q.error&&<p role="alert">{q.error}</p>}{error&&<p className="auth-error" role="alert">{error}</p>}
 {q.data?.items.length===0&&<div className="panel booking-checkout"><p>Aucune réservation.</p><button className="primary" onClick={onSearch}>Rechercher un voyage</button></div>}
 {q.data?.items.map(b=><article className="panel booking-checkout" key={b.id}><div className="booking-total"><strong>{bookingLabel(b.status)}</strong><strong>{priceText(b.total)}</strong></div><small>Réf. {b.reference}</small>{b.trips.map(t=><div key={t.id}><strong>{t.origin} → {t.destination}</strong><p>{t.company} · {dayText(t.starts_at)} · {timeText(t.starts_at)}</p></div>)}<p>{b.count} passager(s)</p>{b.status==='HELD'&&<><small>Expiration : <Countdown expires={b.expires_at}/></small>{confirm===b.id?<div className="booking-actions"><p>Libérer les places ?</p><button className="outline" disabled={busy} onClick={()=>setConfirm(null)}>Retour</button><button className="primary" disabled={busy} onClick={()=>cancel(b.id)}>Confirmer</button></div>:<button className="outline" onClick={()=>setConfirm(b.id)}>Annuler</button>}</>}</article>)}
 {q.data&&(page>1||q.data.has_next)&&<div className="booking-actions"><button className="outline" disabled={page===1} onClick={()=>setPage(p=>p-1)}>Précédent</button><button className="outline" disabled={!q.data.has_next} onClick={()=>setPage(p=>p+1)}>Suivant</button></div>}</>}
 </section>
}

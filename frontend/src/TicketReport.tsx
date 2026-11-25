import {useState,useRef} from 'react';
import {ArrowLeft,CalendarDays,BusFront,ShieldCheck} from 'lucide-react';
import {bookingPost,type Booking} from './booking-api';
import {useTravel,dayText,timeText,priceText,type Trip} from './travel-api';
import {Pagination} from './listing';
import './report.css';

export type ReportOption=Trip&{total:number;difference:number};
type Options={items:ReportOption[];previous_amount:number;page_size:number;total:number;page:number};
export function ReportAmounts({previous,option}:{previous:number;option:ReportOption}){
 return <div className="report-amounts"><div><span>Ancien montant simulé</span><strong>{priceText(previous)}</strong></div><div><span>Nouveau montant simulé</span><strong>{priceText(option.total)}</strong></div><div><span>{option.difference>0?'Supplément simulé':option.difference<0?'Écart de tarif simulé':'Différence'}</span><strong>{priceText(Math.abs(option.difference))}{option.difference<0?' de moins':''}</strong></div><small>Aucun argent ne sera débité ou remboursé. Les tarifs et conditions réels restent à définir.</small></div>
}
export default function TicketReport({booking,onBack,onReported}:{booking:Booking;onBack:()=>void;onReported:(b:Booking)=>void}){
 const [date,setDate]=useState(''),[page,setPage]=useState(1),[choice,setChoice]=useState<ReportOption|null>(null),[confirm,setConfirm]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const pending=useRef(false);
 const q=useTravel<Options>('bookings/'+booking.id+'/report/options/?'+new URLSearchParams({date,page:String(page),page_size:'10'}));
 function reset(){setChoice(null);setConfirm(false);setError('')}
 async function submit(){if(!choice||!confirm||pending.current)return;pending.current=true;setBusy(true);setError('');
 try{const b=await bookingPost<Booking>('bookings/'+booking.id+'/report/',{departure_id:choice.id,total:choice.total});onReported(b)}catch(e){setError(e instanceof Error?e.message:'Report impossible.')}finally{pending.current=false;setBusy(false)}}
 const trip=booking.trips[0];
 return <section className="booking-space booking-details report-space"><div className="travel-heading"><div className="travel-heading-top"><button type="button" onClick={onBack} disabled={busy}><ArrowLeft size={19}/> Retour</button><CalendarDays size={22}/></div><h1>Reporter le voyage</h1><p>{trip.origin} → {trip.destination} · {trip.company}</p></div>
 <article className="panel report-panel"><strong>Départ actuel</strong><p>{dayText(trip.starts_at)} · {timeText(trip.starts_at)}</p><small>{booking.count} passager(s) · {booking.count-trip.premium_positions.length} Standard · {trip.premium_positions.length} Premium</small><p>Le report concerne tous les passagers de cette réservation aller simple. Les catégories et le format des billets sont conservés.</p></article>
 <p className="report-test"><ShieldCheck size={17}/> MODE TEST — Aucun paiement réel.</p>
 <article className="panel report-panel"><h2>Choisir un nouveau départ</h2><label>Date souhaitée (facultative)<input type="date" value={date} disabled={busy} onChange={e=>{setDate(e.target.value);setPage(1);reset()}}/></label><button type="button" className="outline" disabled={busy||q.loading} onClick={()=>{reset();q.retry()}}>Actualiser les disponibilités</button>
 {q.loading&&<p role="status">Recherche des départs…</p>}{q.error&&<p role="alert" className="auth-error">{q.error}</p>}{q.data&&<>{q.data.items.length===0&&<p>Aucun autre départ disponible pour ces catégories.</p>}{q.data.items.map(d=><button type="button" key={d.id} disabled={busy} aria-pressed={choice?.id===d.id} className="report-option" onClick={()=>{setChoice(d);setConfirm(false);setError('')}}><BusFront size={22}/><span><strong>{dayText(d.starts_at)} · {timeText(d.starts_at)}</strong><small>{d.bus_name} · {d.boarding_point}</small></span><strong>{priceText(d.total)}</strong></button>)}<Pagination page={page} size={q.data.page_size} total={q.data.total} onChange={p=>{setPage(p);reset()}} disabled={busy}/></>}</article>
 {choice&&q.data&&<article className="panel report-panel"><h2>Récapitulatif du report</h2><p>Nouveau départ : {dayText(choice.starts_at)} à {timeText(choice.starts_at)}</p><ReportAmounts previous={q.data.previous_amount} option={choice}/><label className="report-confirm"><input type="checkbox" checked={confirm} disabled={busy} onChange={e=>setConfirm(e.target.checked)}/><span>Je confirme le report de tous les passagers et l’invalidation des anciens billets.</span></label><button type="button" className="primary" disabled={!confirm||busy} onClick={()=>void submit()}>{busy?'Report en cours…':'Confirmer le report TEST'}</button>{error&&<p role="alert" className="auth-error">{error}</p>}</article>}
 </section>
}

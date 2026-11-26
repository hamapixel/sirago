import {useEffect,useRef,useState} from 'react';
import {ArrowLeft,Clock,LockKeyhole,Smartphone,Ticket,UserRound} from 'lucide-react';
import {bookingPost,effectiveBookingStatus,bookingLabel,type Booking} from './booking-api';
import {priceText,dayText,timeText} from './travel-api';
import './payment-preview.css';
import TestTickets from './TestTickets';
import SandboxCheckoutPanel from './SandboxCheckoutPanel';

export default function PaymentPreview({booking,onBack}:{booking:Booking;onBack:()=>void}){
 const [now,setNow]=useState(Date.now());
 const [result,setResult]=useState<Booking|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const pending=useRef(false);
 const [method,setMethod]=useState<'orange'|'moov'>('orange');
 useEffect(()=>{const t=window.setInterval(()=>setNow(Date.now()),1000);return()=>window.clearInterval(t)},[]);
 const current=result??booking;
 const status=effectiveBookingStatus(current,now);
 async function simulate(){if(pending.current||current.sandbox_checkout||!booking.simulation_enabled||effectiveBookingStatus(booking)!=='HELD')return;pending.current=true;setBusy(true);setError('');try{setResult(await bookingPost<Booking>('bookings/'+booking.id+'/simulate-payment/',{network:method==='orange'?'orange_ml':'moov_ml'}))}catch(e){setError(e instanceof Error?e.message:'Simulation impossible.')}finally{pending.current=false;setBusy(false)}}
 const seconds=Math.max(0,Math.ceil((Date.parse(booking.expires_at)-now)/1000));
 if(status==='TEST_PAID'&&(result??booking).simulation_enabled)return <TestTickets booking={result??booking} onBack={onBack}/>;
 return <section className="booking-space booking-details payment-preview">
 <div className="travel-heading"><div className="travel-heading-top"><button type="button" disabled={busy} onClick={onBack}><ArrowLeft size={19}/> Retour</button><LockKeyhole size={22}/></div><h1>Paiement</h1><p>{booking.trips[0]?.origin} → {booking.trips[0]?.destination}</p></div>
 {current.sandbox_checkout_enabled&&(status==='HELD'||!!current.sandbox_checkout)&&<SandboxCheckoutPanel booking={current} expired={status!=='HELD'} onUpdate={setResult}/>}
 {status!=='HELD'?<article className="panel booking-checkout"><h2>{bookingLabel(status)}</h2><p>{status==='TEST_PAID'?'Test réussi. Aucun argent débité. Aucun billet valable émis.':'Cette réservation ne peut plus être payée.'}</p><button className="primary" onClick={onBack}>Retour aux détails</button></article>:<>
 <article className="panel booking-checkout"><h2 className="payment-title"><Ticket size={20}/> Résumé du voyage</h2>
 {booking.trips.map((trip,j)=><div className="payment-leg" key={trip.id}><strong>{booking.trips.length>1?(j===0?'Aller · ':'Retour · '):''}{trip.origin} → {trip.destination}</strong><small>{trip.company} · {dayText(trip.starts_at)} · {timeText(trip.starts_at)}</small>{Array.from({length:booking.count},(_,i)=>{const premium=trip.premium_positions.includes(i);return <div className="payment-passenger" key={i}><span className="passenger-number">{i+1}</span><div><strong>{booking.passenger_names[i]||'Passager '+(i+1)}</strong><small>{premium?'Premium':'Standard'}</small></div><strong>{priceText(premium?trip.premium_price:trip.price)}</strong></div>})}<div className="booking-total"><span>Sous-total</span><strong>{priceText(trip.total)}</strong></div></div>)}
 <div className="booking-total"><strong>Total</strong><strong>{priceText(booking.total)}</strong></div></article>
 <article className="panel booking-checkout"><h2 className="payment-title"><UserRound size={20}/> Réservation</h2><small className="payment-reference">Réf. {booking.reference}</small><p>{booking.count} passager(s)</p></article>
 <article className="panel booking-checkout"><h2 className="payment-title"><Smartphone size={20}/> Mode de paiement</h2><small>{booking.simulation_enabled?'Simulation locale · Aucun débit.':'SasPay · Réseaux à vérifier.'}</small><div role="group" aria-label="Mode de paiement" className="payment-methods">{([{id:'orange',label:'Orange Money'},{id:'moov',label:'Moov Money'}] as const).map(o=><button type="button" key={o.id} aria-pressed={method===o.id} disabled={busy} onClick={()=>setMethod(o.id)} className={'payment-method '+(method===o.id?'selected':'')}><span className={'payment-method-icon '+o.id}><Smartphone size={22}/></span><strong>{o.label}</strong><span className="payment-radio" aria-hidden="true"/></button>)}</div></article>
 <article className="panel booking-checkout"><div className="booking-info"><Clock size={20}/><p>Temps restant : {Math.floor(seconds/60)} min {String(seconds%60).padStart(2,'0')} s</p></div><div className="booking-total"><strong>Total à payer</strong><strong className="payment-total">{priceText(booking.total)}</strong></div>{error&&<p className="auth-error" role="alert">{error}</p>}<button className="primary" disabled={busy||!!current.sandbox_checkout||!booking.simulation_enabled||seconds===0} onClick={simulate}><LockKeyhole size={18}/> {busy?"Simulation…":booking.simulation_enabled?"Simuler le paiement":"Confirmer et payer"}</button><small role="status">{booking.simulation_enabled?"MODE TEST · Aucun débit réel.":"SasPay en préparation. Aucun débit possible."}</small></article>
 </>}
 </section>
}

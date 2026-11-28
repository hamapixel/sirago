import {useRef,useState} from 'react';
import {ShieldCheck,ExternalLink,RefreshCw,LockKeyhole,ArrowRight} from 'lucide-react';
import {bookingPost,type Booking} from './booking-api';
import {priceText} from './travel-api';

export default function SandboxCheckoutPanel({booking,onUpdate,expired}:{booking:Booking;onUpdate:(b:Booking)=>void;expired:boolean}){
 const [busy,setBusy]=useState(false),[error,setError]=useState('');
 const pending=useRef(false);
 const a=booking.sandbox_checkout;
 async function action(verify:boolean){
  if(pending.current)return;pending.current=true;setBusy(true);setError('');
  try{onUpdate(await bookingPost<Booking>('bookings/'+booking.id+'/sandbox-checkout/'+(verify?'verify/':''),{}))}
  catch(e){setError(e instanceof Error?e.message:'SasPay indisponible.');try{const r=await fetch('/api/v1/travel/bookings/'+booking.id+'/',{credentials:'same-origin',cache:'no-store'});if(r.ok)onUpdate(await r.json() as Booking)}catch{/* retain error */}}
  finally{pending.current=false;setBusy(false)}
 }
 let safe=false;
 try{const u=new URL(a?.checkout_url||'');safe=u.origin==='https://sandbox-checkout.saspay.me'&&!u.username&&!u.password}catch{/* invalid URL */}
 return <article className="panel booking-checkout payment-provider"><div className="payment-provider-head"><span className="payment-provider-symbol"><ShieldCheck size={26}/></span><div><h2 className="payment-title">SasPay</h2><small>Page de paiement hébergée</small></div><span className="payment-test-tag">SANDBOX · TEST</span></div>
 <div className="payment-test-note"><LockKeyhole size={17}/><small>TEST uniquement · Aucun débit réel ni billet émis à cette étape.</small></div>
 <div className="payment-network-grid" aria-label="Exemples de moyens de paiement"><div className="payment-network orange"><strong>Orange</strong><span>Money</span></div><div className="payment-network moov"><strong>Moov</strong><span>Money</span></div><div className="payment-network wave"><strong>Wave</strong><span>Mobile Money</span></div></div>
 <p className="payment-provider-note">Choisissez votre moyen de paiement sur SasPay. Les réseaux effectivement disponibles et les frais éventuels sont affichés sur le Checkout.</p>
 <div className="booking-total payment-provider-total"><span>Montant de la réservation</span><strong>{priceText(booking.total)}</strong></div>
 {!a&&!expired&&<button type="button" className="primary payment-provider-cta" disabled={busy} onClick={()=>action(false)}><LockKeyhole size={18}/><span>{busy?'Création…':'Payer avec SasPay (TEST)'}</span><ArrowRight size={18}/></button>}
 {a?.status==='PENDING'&&<><p>Session en attente.</p>{safe&&!expired&&<a className="primary" href={a.checkout_url} target="_blank" rel="noopener noreferrer"><ExternalLink size={17}/> Ouvrir le paiement SasPay</a>}<button type="button" className="outline" disabled={busy} onClick={()=>action(true)}><RefreshCw size={17}/> Vérifier le paiement</button></>}
 {a?.status==='PAID'&&<p role="status" className="profile-success">Paiement Sandbox confirmé par Django. Aucun billet émis pour cette étape.</p>}
 {a?.status==='REVIEW_PAID'&&<p role="alert">Paiement de test confirmé, mais la réservation ne peut pas être finalisée. Contactez l’assistance ; ne payez pas à nouveau.</p>}
 {a?.status==='LATE_PAID'&&<p role="alert">Paiement de test reçu après expiration. Aucun billet émis.</p>}
 {a&&['CREATING','UNKNOWN'].includes(a.status)&&<p role="alert">Création en cours ou incertaine. Ne créez pas une autre session. Consultez SasPay.</p>}
 {a&&['EXPIRED','CANCELLED'].includes(a.status)&&<p>Session terminée sans paiement. Créez une nouvelle réservation si nécessaire.</p>}
 {error&&<p className="auth-error" role="alert">{error}</p>}</article>
}

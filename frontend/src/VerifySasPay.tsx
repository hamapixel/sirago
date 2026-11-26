import {useRef,useState} from 'react';
import {RefreshCw} from 'lucide-react';
import {bookingPost,type Booking} from './booking-api';
export default function VerifySasPay({booking,onUpdate}:{booking:Booking;onUpdate:(b:Booking)=>void}){
 const pending=useRef(false);const [busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
 async function verify(){if(pending.current)return;pending.current=true;setBusy(true);setError('');setNotice('');
 try{const b=await bookingPost<Booking>('bookings/'+booking.id+'/sandbox-checkout/verify/',{});if(b.sandbox_checkout?.status==='PENDING')setNotice('SasPay indique toujours une session en attente. Réessayez dans quelques instants.');else onUpdate(b)}
 catch(e){setError(e instanceof Error?e.message:'Vérification indisponible.')}
 finally{pending.current=false;setBusy(false)}}
 return <div className="history-verify"><button type="button" className="primary" disabled={busy} onClick={verify}><RefreshCw size={18}/>{busy?'Vérification…':'Vérifier le paiement SasPay'}</button>{error&&<p className="auth-error" role="alert">{error}</p>}{notice&&<small role="status">{notice}</small>}</div>
}

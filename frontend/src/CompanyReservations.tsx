import {useEffect,useState} from 'react';
import {companyGet} from './company-api';
import {bookingLabel,type Booking} from './booking-api';
import {dayText,timeText,priceText} from './travel-api';
type Row={id:number;reference:string;origin:string;destination:string;starts_at:string;count:number;premium_count:number;total:number;status:Booking['status'];expires_at:string};
export default function CompanyReservations(){
 const [items,setItems]=useState<Row[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState(''),[revision,setRevision]=useState(0);
 useEffect(()=>{let active=true;setLoading(true);setError('');companyGet<{items:Row[]}>('reservations/').then(r=>{if(active)setItems(r.items)}).catch(e=>{if(active)setError(e instanceof Error?e.message:'Chargement impossible.')}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[revision]);
 return <section className="booking-space"><div className="company-section-head"><h2>Réservations</h2><button className="outline" onClick={()=>setRevision(r=>r+1)}>Actualiser</button></div><small>100 dernières lignes · paiement à venir.</small>{loading?<p>Chargement…</p>:error?<p role="alert">{error}</p>:!items.length?<p className="panel">Aucune réservation.</p>:items.map(r=><article className="panel booking-checkout" key={r.id}><strong>{r.origin} → {r.destination}</strong><p>{dayText(r.starts_at)} · {timeText(r.starts_at)}</p><div className="booking-total"><span>{r.count} passager(s)</span><strong>{priceText(r.total)}</strong></div>{r.premium_count>0&&<small>{r.count-r.premium_count} Standard · {r.premium_count} Premium</small>}<p>{bookingLabel(r.status)}</p><small>Réf. {r.reference}</small></article>)}</section>
}

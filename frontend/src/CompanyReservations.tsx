import {useState} from 'react';
import {bookingLabel,type Booking} from './booking-api';
import {dayText,timeText,priceText} from './travel-api';
import {SearchField,Pagination,useCompanyList} from './listing';
type Row={id:number;reference:string;origin:string;destination:string;starts_at:string;count:number;premium_count:number;total?:number;status:Booking['status'];expires_at:string};
export default function CompanyReservations(){
 const [query,setQuery]=useState(''),[page,setPage]=useState(1),[revision,setRevision]=useState(0);
 const {data,loading,error}=useCompanyList<Row>('reservations/',query,page,revision);
 return <section className="booking-space"><div className="company-section-head"><h2>Réservations</h2><button className="outline" onClick={()=>setRevision(r=>r+1)} disabled={loading}>Actualiser</button></div><SearchField value={query} onChange={v=>{setQuery(v);setPage(1)}} placeholder="Passager, trajet ou référence…"/><small>Les tests ne sont pas des recettes.</small>{loading?<p>Chargement…</p>:error?<p role="alert">{error}</p>:!data?.items.length?<p className="panel">Aucune réservation trouvée.</p>:data.items.map(r=><article className="panel booking-checkout reservation-record" key={r.id}><strong>{r.origin} → {r.destination}</strong><p>{dayText(r.starts_at)} · {timeText(r.starts_at)}</p><div className="booking-total"><span>{r.count} passager(s)</span>{r.total!==undefined&&<strong>{priceText(r.total)}</strong>}</div>{r.premium_count>0&&<small>{r.count-r.premium_count} Standard · {r.premium_count} Premium</small>}<p>{bookingLabel(r.status)}</p><small>Réf. {r.reference}</small></article>)}{data&&<Pagination page={page} size={data.page_size} total={data.total} onChange={setPage}/>}</section>
}

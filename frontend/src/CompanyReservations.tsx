import {t as tr} from './i18n';
import {useState} from 'react';
import {Ticket,BusFront,Users,CalendarDays,RefreshCw} from 'lucide-react';
import {bookingLabel,type Booking} from './booking-api';
import {dayText,timeText,priceText} from './travel-api';
import {SearchField,Pagination,useCompanyList} from './listing';
type Row={id:number;reference:string;origin:string;destination:string;starts_at:string;count:number;premium_count:number;total?:number;status:Booking['status'];expires_at:string};
export function ReservationCard({row:r}:{row:Row}){
 return <article className="panel reservation-record premium-reservation"><div className="reservation-top"><span className="route-emblem"><BusFront size={22}/></span><div><h3>{r.origin} → {r.destination}</h3><small><CalendarDays size={14}/> {dayText(r.starts_at)} · {timeText(r.starts_at)}</small></div></div><div className="reservation-meta"><span><Users size={17}/> {r.count} passager(s)</span>{r.total!==undefined&&<strong>{priceText(r.total)}</strong>}</div>{r.premium_count>0&&<small>{r.count-r.premium_count} Standard · {r.premium_count} Premium</small>}<div className="reservation-foot"><span className={'premium-status '+(r.status==='TEST_PAID'?'is-active':r.status==='HELD'?'is-pending':'is-inactive')}>{tr(bookingLabel(r.status))}</span><small title={r.reference}>Réf. {r.reference}</small></div></article>
}
export default function CompanyReservations(){
 const [query,setQuery]=useState(''),[page,setPage]=useState(1),[revision,setRevision]=useState(0);
 const {data,loading,error}=useCompanyList<Row>('reservations/',query,page,revision);
 return <section className="premium-reservations"><header className="premium-section-banner"><div><small>ESPACE COMPAGNIE</small><h2>{tr("Réservations")}</h2><p>Suivez les voyageurs de vos départs.</p></div><Ticket size={30}/></header><div className="panel reservation-toolbar"><SearchField value={query} onChange={v=>{setQuery(v);setPage(1)}} placeholder="Passager, trajet ou référence…"/><button className="outline" onClick={()=>setRevision(r=>r+1)} disabled={loading}><RefreshCw size={16}/> {tr("Actualiser")}</button></div>{loading?<p role="status">{tr("Chargement…")}</p>:error?<p role="alert">{error}</p>:!data?.items.length?<p className="panel">{tr("Aucune réservation trouvée.")}</p>:<div className="premium-reservation-grid">{data.items.map(r=><ReservationCard key={r.id} row={r}/>)}</div>}{data&&<Pagination page={page} size={data.page_size} total={data.total} onChange={setPage}/>}</section>
}

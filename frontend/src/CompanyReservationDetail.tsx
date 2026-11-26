import {useEffect,useState} from 'react';
import {ArrowLeft,ArrowRight,Armchair,BusFront,CalendarDays,CheckCircle2,Clock,MapPin,RefreshCw,Ticket,UserRound,Users,Wallet} from 'lucide-react';
import {companyGet} from './company-api';
import {bookingLabel,type Booking} from './booking-api';
import {dayText,timeText,priceText} from './travel-api';
import {t,useLanguage} from './i18n';
import './reservation-detail.css';

type PassengerState='BOARDED'|'WAITING'|'PENDING'|'ABSENT'|'UNAVAILABLE';
export type ReservationDetailData={
 id:number;reference:string;company:string;status:Booking['status'];departure_status:string;
 created_at:string;expires_at:string;position:number;origin:string;destination:string;
 boarding_point:string;arrival_point:string;starts_at:string;ends_at:string;bus_name:string;plate:string;
 ticket_mode:'group'|'individual';payment_method:'SASPAY_SIMULATION'|'LOCAL_SIMULATION'|'NONE';
 count:number;premium_count:number;boarded_count:number;total?:number;real_amount?:number;simulated_amount?:number;
 passengers:{index:number;name:string;category:'Standard'|'Premium';state:PassengerState;boarded_at:string|null;amount?:number}[];
};
const passengerLabels:Record<PassengerState,string>={BOARDED:'Embarqué (simulation)',WAITING:'Non embarqué',PENDING:'Paiement en attente',ABSENT:'Absent (simulation)',UNAVAILABLE:'Billet indisponible'};
const departureLabels:Record<string,string>={PUBLISHED:'Publié',SUSPENDED:'Suspendu',CANCELLED:'Annulé',DRAFT:'Brouillon'};
export function ReservationDetailContent({data:d}:{data:ReservationDetailData}){
 useLanguage();
 const financial=d.total!==undefined;
 return <>
 <header className="reservation-detail-hero"><div className="reservation-hero-top"><small>{t('Détails de la réservation')}</small><span className="reservation-detail-status">{t(bookingLabel(d.status))}</span></div><h2>{d.origin}<ArrowRight size={22} aria-hidden="true"/>{d.destination}</h2><p><BusFront size={17}/>{d.company} · {d.bus_name}</p><p className="reservation-detail-reference">{t('Référence')} : {d.reference}</p></header>
 <div className="reservation-detail-metrics">{[{label:'Passagers',value:d.count,Icon:Users},{label:'Standard',value:d.count-d.premium_count,Icon:Armchair},{label:'Premium',value:d.premium_count,Icon:Ticket},{label:'Embarqués (simulation)',value:d.boarded_count,Icon:CheckCircle2}].map(({label,value,Icon})=><article className="panel" key={label}><span className="route-emblem"><Icon size={21}/></span><div><small>{t(label)}</small><strong>{value}</strong></div></article>)}</div>
 <article className="panel reservation-trip-detail"><div className="reservation-detail-section-title"><h3><BusFront size={20}/>{t('Informations du trajet')}</h3><span className="premium-status">{t(departureLabels[d.departure_status]??d.departure_status)}</span></div>
 <div className="reservation-trip-points">{[{city:d.origin,place:d.boarding_point,date:d.starts_at,label:'Départ'},{city:d.destination,place:d.arrival_point,date:d.ends_at,label:'Arrivée'}].map((point,i)=><div key={i}><small>{t(point.label)}</small><strong>{timeText(point.date)}</strong><b>{point.city}</b><span><MapPin size={15}/>{point.place}</span><small>{dayText(point.date)}</small></div>)}</div>
 <div className="reservation-trip-extra"><span><BusFront size={16}/>{d.bus_name} · {d.plate}</span><span><Ticket size={16}/>{t(d.ticket_mode==='group'?'Billets collectifs':'Billets individuels')}</span><span><CalendarDays size={16}/>{t(d.position===0?'Aller':'Retour')}</span></div></article>
 <article className="panel reservation-passengers"><div className="reservation-detail-section-title"><h3><Users size={20}/>{t('Liste des passagers')}</h3><span className="premium-status is-active">{d.count}</span></div><div className="reservation-passenger-grid">{d.passengers.map(p=><div key={p.index} className="reservation-passenger-card"><div className="reservation-passenger-top"><span className="reservation-passenger-avatar"><UserRound size={22}/></span><div><small>{t('Passager')} {p.index+1}</small><strong>{p.name}</strong></div><span className={'reservation-category '+(p.category==='Premium'?'gold':'')}>{t(p.category)}</span></div><div className="reservation-passenger-meta"><span className={'reservation-passenger-state '+p.state.toLowerCase()}>{t(passengerLabels[p.state])}</span>{financial&&p.amount!==undefined&&<strong>{priceText(p.amount)}</strong>}</div>{p.boarded_at&&<small className="reservation-boarded-at"><Clock size={14}/>{dayText(p.boarded_at)} · {timeText(p.boarded_at)}</small>}</div>)}</div></article>
 <article className="panel reservation-payment-detail"><div className="reservation-detail-section-title"><h3><Wallet size={20}/>{t('Paiement')}</h3></div><p>{t(bookingLabel(d.status))}</p>{d.payment_method!=='NONE'&&<small>{t(d.payment_method==='SASPAY_SIMULATION'?'SasPay · Simulation':'Simulation locale')}</small>}{financial&&<dl><div><dt>{t('Montant du trajet')}</dt><dd>{priceText(d.total!)}</dd></div><div><dt>{t('Montant simulé')}</dt><dd>{priceText(d.simulated_amount??0)}</dd></div><div><dt>{t('Montant encaissé (réel)')}</dt><dd>{priceText(d.real_amount??0)}</dd></div></dl>}<p className="reservation-simulation-note">{t('Aucun encaissement ni embarquement réel.')}</p></article>
 <p className="reservation-created"><CalendarDays size={15}/>{t('Réservation créée le')} {dayText(d.created_at)} · {timeText(d.created_at)}</p>
 </>
}
export default function CompanyReservationDetail({id,onBack}:{id:number;onBack:()=>void}){
 const [data,setData]=useState<ReservationDetailData|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState(''),[revision,setRevision]=useState(0);
 useEffect(()=>{const controller=new AbortController();let active=true;setLoading(true);setError('');setData(null);companyGet<ReservationDetailData>('reservations/'+id+'/',controller.signal).then(result=>{if(active)setData(result)}).catch(e=>{if(active)setError(e instanceof Error?e.message:'Chargement impossible.')}).finally(()=>{if(active)setLoading(false)});return()=>{active=false;controller.abort()}},[id,revision]);
 return <section className="reservation-detail"><div className="reservation-detail-toolbar"><button type="button" className="outline" onClick={onBack}><ArrowLeft size={18}/>{t('Retour aux réservations')}</button><button type="button" className="outline" onClick={()=>setRevision(x=>x+1)} disabled={loading}><RefreshCw size={17}/>{t('Actualiser')}</button></div>{loading?<p role="status">{t('Chargement…')}</p>:error?<p className="auth-error" role="alert">{error}</p>:data?<ReservationDetailContent data={data}/>:null}</section>
}

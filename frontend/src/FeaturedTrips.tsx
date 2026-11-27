import {useState} from 'react';
import {ArrowRight,BusFront,CalendarDays,ShieldCheck,Users} from 'lucide-react';
import {PartnerLogo} from './PartnerCard';
import {partnerInfo} from './partners';
import {dayText,timeText,durationText,priceText,minimumTripTotal,type Trip,type Criteria} from './travel-api';
import {t,useLanguage} from './i18n';
import './featured-trips.css';
import QuickBooking from './QuickBooking';

export function FeaturedTripCard({trip,count,logo,onBook}:{trip:Trip;count:number;logo?:string;onBook:(trip:Trip,count:number)=>void}){
 useLanguage();
 const standard=trip.standard_remaining>0, premium=trip.premium_remaining>0&&trip.premium_price>0;
 const canBook=trip.remaining>=count&&((standard?trip.standard_remaining:0)+(premium?trip.premium_remaining:0))>=count;
 const image=logo?.startsWith('data:image/jpeg;base64,')?logo:partnerInfo({id:trip.company_id,name:trip.company})?.logo;
 return <article className="panel featured-trip-card">
 <div className="featured-trip-identity"><PartnerLogo key={image||trip.company_id} name={trip.company} src={image}/><div><h3>{trip.company}</h3><small>{trip.origin} → {trip.destination}</small></div><span className="featured-verified" title={t('Compagnie validée')}><ShieldCheck size={19}/><span className="featured-sr">{t('Compagnie validée')}</span></span></div>
 <div className="featured-trip-date"><CalendarDays size={15}/>{dayText(trip.starts_at)}</div>
 <div className="featured-trip-timeline"><div className="featured-stop"><strong>{timeText(trip.starts_at)}</strong><b>{trip.origin}</b><small>{trip.boarding_point}</small></div><div className="featured-trip-middle"><div className="featured-line"><i/><span/><BusFront size={24}/><span/><i/></div><small>{durationText(trip.duration_minutes)}</small></div><div className="featured-stop featured-arrival"><strong>{timeText(trip.ends_at)}</strong><b>{trip.destination}</b><small>{trip.arrival_point}</small>{dayText(trip.starts_at)!==dayText(trip.ends_at)&&<small>{dayText(trip.ends_at)}</small>}</div></div>
 <div className="featured-trip-fares">{standard&&<div><small>{t('Standard')}</small><strong>{priceText(trip.price)}</strong></div>}{premium&&<div className="featured-fare-premium"><small>{t('Premium')}</small><strong>{priceText(trip.premium_price)}</strong></div>}</div>
 <div className="featured-trip-meta"><span><Users size={15}/>{trip.remaining} {t('places disponibles')}</span><span>{t('Aller simple')} · {count} {t(count===1?'passager':'passagers')}</span></div>
 {count>1&&canBook&&<p className="featured-total">{t('Total minimum')} : <strong>{priceText(minimumTripTotal(trip,count))}</strong></p>}
 <button type="button" className="primary featured-book" disabled={!canBook} onClick={()=>onBook(trip,count)}>{t(canBook?'Réserver maintenant':'Places insuffisantes')}<ArrowRight size={18}/></button>
 </article>
}
export default function FeaturedTrips({trips,logos,count,onSearch}:{trips:Trip[];logos:Record<string,string>;count:number;onSearch:(criteria:Criteria,companyId:number)=>void}){
 useLanguage();
 const [expanded,setExpanded]=useState(false),[selected,setSelected]=useState<Trip|null>(null);
 return <div className="featured-trips"><div className="featured-title"><h2>{t('Trajets proposés')}</h2>{trips.length>4&&<button type="button" className="featured-more" aria-expanded={expanded} onClick={()=>setExpanded(v=>!v)}>{t(expanded?'Voir moins':'Voir plus')}<ArrowRight size={16}/></button>}</div>{!trips.length?<p className="panel travel-home-empty">{t('Aucun trajet publié.')}</p>:<div className="featured-trip-grid">{(expanded?trips:trips.slice(0,4)).map(trip=><FeaturedTripCard key={trip.id} trip={trip} logo={logos[String(trip.company_id)]} count={count} onBook={trip=>setSelected(trip)}/>)}</div>}{selected&&<QuickBooking key={selected.id} trip={selected} initialCount={count} onClose={()=>setSelected(null)} onSearch={onSearch}/>}</div>
}

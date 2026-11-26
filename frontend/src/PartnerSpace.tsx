import {useState} from 'react';
import {ArrowLeft,ArrowRight,BusFront,CalendarDays,MapPin,Phone,ShieldCheck,Users,LocateFixed} from 'lucide-react';
import {partnerInfo,partnerMapUrl,partnerPhones} from './partners';
import {useTravel,partnerPath,priceText,timeText,durationText,dayText,minimumTripTotal,type Trip,type PartnerCompany,type PartnerPage} from './travel-api';
import {localToday} from './search';
import {Pagination,SearchField} from './listing';
import './partners.css';
import {PartnerLogo} from './PartnerCard';
import './travel.css';

export function groupPartnerTrips(items:Trip[]){
 const groups=new Map<string,Trip[]>();
 for(const trip of items){const key=JSON.stringify([trip.origin,trip.destination]);const rows=groups.get(key)??[];rows.push(trip);groups.set(key,rows)}
 return [...groups.entries()];
}
export function PartnerRoute({trips,count,onBook}:{trips:Trip[];count:number;onBook:(trip:Trip,count:number)=>void}){
 const [chosen,setChosen]=useState<number>(trips[0].id);
 const trip=trips.find(t=>t.id===chosen)??trips[0];
 return <article className="panel partner-route"><div className="partner-route-title"><h3>{trip.origin} → {trip.destination}</h3><small>{trips.length} départ(s)</small></div><div className="partner-hours" role="group" aria-label="Horaires disponibles">{trips.map(t=><button type="button" key={t.id} aria-pressed={t.id===trip.id} aria-label={dayText(t.starts_at)+' · '+timeText(t.starts_at)+' · '+t.bus_name+' · '+priceText(t.from_price)} onClick={()=>setChosen(t.id)}>{timeText(t.starts_at)}<small>{new Intl.DateTimeFormat('fr-FR',{day:'numeric',month:'short',timeZone:'Africa/Bamako'}).format(new Date(t.starts_at))}</small>{trips.filter(x=>x.starts_at===t.starts_at).length>1&&<small>{t.bus_name}</small>}</button>)}</div>
 <p className="partner-trip-date"><CalendarDays size={16}/>{dayText(trip.starts_at)}</p><div className="trip-timeline"><div className="trip-stop"><strong className="trip-time">{timeText(trip.starts_at)}</strong><b>{trip.origin}</b><small>{trip.boarding_point}</small></div><div className="trip-middle"><div className="trip-line"><i/><span/><i/></div><BusFront size={20}/><small>{durationText(trip.duration_minutes)}</small></div><div className="trip-stop arrival"><strong className="trip-time">{timeText(trip.ends_at)}</strong><b>{trip.destination}</b><small>{trip.arrival_point}</small>{dayText(trip.starts_at)!==dayText(trip.ends_at)&&<small>{dayText(trip.ends_at)}</small>}</div></div>
 <div className="partner-fares">{trip.standard_remaining>0&&<div><small>Standard</small><strong>{priceText(trip.price)}</strong></div>}{trip.premium_remaining>0&&<div><small>Premium</small><strong>{priceText(trip.premium_price)}</strong></div>}</div><div className="partner-route-meta"><small>{trip.bus_name} · {trip.remaining} places libres</small>{count>1&&<strong>Dès {priceText(minimumTripTotal(trip,count))}</strong>}</div><button className="primary" onClick={()=>onBook(trip,count)}><CalendarDays size={19}/> Réserver maintenant <ArrowRight size={18}/></button></article>;
}
export default function PartnerSpace({company,onBack,onBook,initialCount}:{company:PartnerCompany;onBack:()=>void;onBook:(trip:Trip,count:number)=>void;initialCount:number}){
 const [date,setDate]=useState(''),[query,setQuery]=useState(''),[count,setCount]=useState(initialCount),[page,setPage]=useState(1),[coverFailed,setCoverFailed]=useState(false);
 const data=useTravel<PartnerPage>(partnerPath(company.id,date,query,count,page));
 const info=partnerInfo(data.data?.company??company),mapUrl=partnerMapUrl(info),phones=partnerPhones(info);
 const groups=groupPartnerTrips(data.data?.items??[]);
 const validCompany=!data.error;
 return <section className="partner-space">
 <div className="partner-hero">{info?.cover&&!coverFailed&&<img className="partner-cover" src={info.cover} alt="" onError={()=>setCoverFailed(true)}/>}<div className="partner-hero-shade"/><div className="partner-hero-content"><div className="partner-hero-actions"><button type="button" className="partner-back" onClick={onBack}><ArrowLeft size={21}/> Retour</button>{mapUrl&&validCompany&&<a className="partner-map" href={mapUrl} target="_blank" rel="noopener noreferrer"><LocateFixed size={19}/> Localisation</a>}</div><div className="partner-identity"><PartnerLogo key={info?.logo||company.id} src={info?.logo} name={company.name}/><div><h1>{data.data?.company.name??company.name}</h1>{validCompany&&<><span><ShieldCheck size={16}/> Compagnie validée</span><span><MapPin size={16}/>{info?.address||company.city}</span>{phones.map(p=><a key={p} href={'tel:'+p}><Phone size={16}/>{p}</a>)}</>}</div></div></div></div>
 <div className="panel partner-filters"><SearchField value={query} onChange={v=>{setQuery(v);setPage(1)}} placeholder="Rechercher une ville…"/><div className="partner-filter-grid"><label>Date (facultatif)<div className="field"><CalendarDays size={18}/><input type="date" min={localToday()} value={date} onChange={e=>{setDate(e.target.value);setPage(1)}}/></div></label><label>Passagers<div className="field"><Users size={18}/><select value={count} onChange={e=>{setCount(Number(e.target.value));setPage(1)}}>{Array.from({length:100},(_,i)=><option key={i+1} value={i+1}>{i+1}</option>)}</select></div></label></div>{date?<button className="outline partner-all-days" onClick={()=>{setDate('');setPage(1)}}>Tous les jours</button>:<small className="partner-all-label">Tous les départs à venir</small>}</div>
 <div className="section-title"><h2 className="partner-section-title">Trajets disponibles</h2>{data.data&&<small>{data.data.total} départ(s)</small>}</div>
 {data.loading&&<p className="panel" role="status">Recherche…</p>}{data.error&&<div className="panel travel-empty" role="alert"><p>{data.error}</p><button className="outline" onClick={data.retry}>Réessayer</button></div>}
 {data.data?.total===0&&<div className="panel travel-empty"><BusFront size={28}/><strong>Aucun départ disponible</strong>{data.data.next_date?<button type="button" className="outline" onClick={()=>{setDate(data.data!.next_date!);setPage(1)}}>Prochain départ · {dayText(data.data.next_date)}</button>:<small>Modifiez les filtres.</small>}</div>}
 <div className="partner-routes">{groups.map(([key,rows])=><PartnerRoute key={key+'-'+date+'-'+page} trips={rows} count={count} onBook={onBook}/>)}</div>
 {data.data&&data.data.total>20&&<Pagination page={page} size={20} total={data.data.total} onChange={setPage}/>}
 </section>;
}

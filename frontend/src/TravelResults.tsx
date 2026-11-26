import {useState} from 'react';
import {ArrowLeft,ArrowRight,BusFront,ShieldCheck,SlidersHorizontal,Search,CheckCircle2,MapPin} from 'lucide-react';
import {useTravel,tripPath,defaultFilters,priceText,timeText,dayText,durationText,minimumTripTotal,compatible,type Trip,type TripPage,type Criteria,type Filters} from './travel-api';
import './travel.css';
import {PartnerLogo} from './PartnerSpace';
import {partnerInfo} from './partners';

export function TripCard({trip,count,onChoose}:{trip:Trip;count:number;onChoose:()=>void}){
 return <article className="panel trip-card">
 <div className="trip-company"><PartnerLogo key={trip.company_id} src={partnerInfo({id:trip.company_id,name:trip.company})?.logo} name={trip.company}/><div><strong>{trip.company}</strong><small><ShieldCheck size={14}/> Vérifiée</small></div></div>
 <div className="trip-timeline"><div className="trip-stop"><strong className="trip-time">{timeText(trip.starts_at)}</strong><b>{trip.origin}</b><small>{trip.boarding_point}</small></div><div className="trip-middle"><div className="trip-line"><i/><span/><i/></div><BusFront size={20}/><small>{durationText(trip.duration_minutes)}</small></div><div className="trip-stop arrival"><strong className="trip-time">{timeText(trip.ends_at)}</strong><b>{trip.destination}</b><small>{trip.arrival_point}</small>{trip.ends_at.slice(0,10)!==trip.starts_at.slice(0,10)&&<small>{dayText(trip.ends_at)}</small>}</div></div>
 <div className="trip-fare"><div><small>À partir de / passager</small><h3>{priceText(trip.from_price)}</h3>{count>1&&<small>Total min. : {priceText(minimumTripTotal(trip,count))}</small>}{trip.standard_remaining>0&&trip.premium_price>0&&<small>Standard : {priceText(trip.price)}</small>}{trip.premium_remaining>0&&<small>Premium : {priceText(trip.premium_price)}</small>}</div><div><span>{trip.remaining} places restantes</span>{trip.premium_price>0&&<small>{trip.standard_remaining} Std · {trip.premium_remaining} Premium</small>}<small>{trip.bus_name}</small></div></div>
 <button className="primary trip-choose" onClick={onChoose}>Choisir <ArrowRight size={18}/></button>
 </article>
}
function Status({loading,error,retry,empty}:{loading:boolean;error:string;retry:()=>void;empty:boolean}){
 if(loading)return <div className="panel travel-loading" role="status"><span className="travel-spinner"/> Recherche des départs…</div>;
 if(error)return <div className="panel travel-empty" role="alert"><p>{error}</p><button className="outline" onClick={retry}>Réessayer</button></div>;
 if(empty)return <div className="panel travel-empty"><Search size={28}/><strong>Aucun départ trouvé</strong><p>Essayez une autre date.</p></div>;
 return null;
}
export function LivePreview({criteria,valid,onOpen}:{criteria:Criteria;valid:boolean;onOpen:(trip?:Trip)=>void}){
 const live=useTravel<TripPage>(valid?tripPath(criteria):null);
 if(!valid)return null;
 return <section className="travel-live"><div className="section-title"><h2>Départs trouvés</h2><span className="travel-live-label">En direct</span></div>
 <Status loading={live.loading} error={live.error} retry={live.retry} empty={live.data?.total===0}/>
 {live.data&&live.data.total>0&&<><p className="muted">{live.data.total} départ(s) à l’aller · {dayText(criteria.date)}</p>{live.data.items.slice(0,2).map(t=><TripCard key={t.id} trip={t} count={criteria.count} onChoose={()=>onOpen(t)}/>)}<button className="outline" onClick={()=>onOpen()}>Comparer les offres <ArrowRight size={18}/></button></>}
 </section>
}
export default function TravelResults({criteria,initialTrip,onBack,onContinue}:{criteria:Criteria;initialTrip:Trip|null;onBack:()=>void;onContinue:(out:Trip,ret:Trip|null)=>void}){
 const [filters,setFilters]=useState<Filters>(defaultFilters),[show,setShow]=useState(false),[page,setPage]=useState(1),[out,setOut]=useState<Trip|null>(initialTrip),[ret,setRet]=useState<Trip|null>(null);
 const returnLeg=criteria.round&&!!out;
 const done=!!out&&(!criteria.round||!!ret);
 const query=useTravel<TripPage>(done?null:tripPath(criteria,filters,page,returnLeg,out?.ends_at));
 function filter(key:keyof Filters,value:string){setFilters(old=>({...old,[key]:value}));setPage(1)}
 function pick(t:Trip){if(returnLeg&&out){if(compatible(out,t))setRet(t)}else{setOut(t);setPage(1);setFilters(defaultFilters)}}
 function resetChoice(){if(ret)setRet(null);else{setOut(null);setRet(null)}setPage(1);setFilters(defaultFilters)}
 return <section className="travel-results">
 <div className="travel-heading"><div className="travel-heading-top"><button type="button" onClick={onBack}><ArrowLeft size={19}/> Résultats</button>{!done&&<button type="button" aria-label="Afficher les filtres" aria-expanded={show} title="Filtres" onClick={()=>setShow(v=>!v)}><SlidersHorizontal size={21}/></button>}</div><h1>{returnLeg?criteria.destination:criteria.origin} → {returnLeg?criteria.origin:criteria.destination}</h1><p>{dayText(returnLeg?criteria.back:criteria.date)} · {criteria.count} passager(s)</p>{criteria.round&&<small>{done?'Aller-retour sélectionné':returnLeg?'Étape 2 sur 2 · Retour':'Étape 1 sur 2 · Aller'}</small>}</div>
 {out&&<div className="panel travel-selection"><CheckCircle2 size={22}/><div><strong>Aller sélectionné</strong><p>{out.company} · {timeText(out.starts_at)} · {priceText(minimumTripTotal(out,criteria.count))}</p></div><button className="outline" onClick={()=>{setOut(null);setRet(null);setPage(1);setFilters(defaultFilters)}}>Modifier</button></div>}
 {done&&out?<section className="panel travel-summary"><h2>Votre voyage</h2><p><MapPin size={17}/> {out.origin} → {out.destination} · {dayText(out.starts_at)} · {timeText(out.starts_at)}</p>{ret&&<p><MapPin size={17}/> {ret.origin} → {ret.destination} · {dayText(ret.starts_at)} · {timeText(ret.starts_at)}</p>}<h3>Total indicatif : {priceText(minimumTripTotal(out,criteria.count)+(ret?minimumTripTotal(ret,criteria.count):0))}</h3><small>Places non bloquées.</small><button className="primary" onClick={()=>onContinue(out,ret)}>Réserver <ArrowRight size={18}/></button><button className="outline" onClick={resetChoice}>Modifier</button></section>:<>
 <div className="travel-result-bar"><strong aria-live="polite">{query.loading?'Recherche…':query.data?query.data.total+' départ(s) trouvé(s)':'Résultats'}</strong><label className="travel-sort"><span className="muted">Trier</span><select value={filters.sort} onChange={e=>filter('sort',e.target.value)}><option value="price">Prix croissant</option><option value="departure">Heure de départ</option><option value="duration">Durée du voyage</option></select></label></div>
 {query.data?.companies&&query.data.companies.length>0&&<section className="panel company-options"><h2>Compagnies disponibles ({query.data.companies.length})</h2><div className="company-option-list"><button type="button" aria-pressed={!filters.company_id} onClick={()=>filter('company_id','')}>Toutes</button>{query.data.companies.map(c=><button type="button" key={c.id} aria-pressed={filters.company_id===String(c.id)} onClick={()=>filter('company_id',String(c.id))}><BusFront size={17}/><span>{c.name}</span><small>{c.departures}</small></button>)}</div></section>}{show&&<div className="panel travel-filters"><label>Horaire<select value={filters.period} onChange={e=>filter('period',e.target.value)}><option value="">Toute la journée</option><option value="morning">Matin (avant 12 h)</option><option value="afternoon">Après-midi (12–18 h)</option><option value="evening">Soir (18–24 h)</option></select></label><label>Prix max. / passager<input type="number" min={1} max={1000000} value={filters.max_price} onChange={e=>filter('max_price',e.target.value)} placeholder="FCFA"/></label><button className="outline" onClick={()=>{setFilters(defaultFilters);setPage(1)}}>Réinitialiser</button></div>}
 <Status loading={query.loading} error={query.error} retry={query.retry} empty={query.data?.total===0}/>
 {query.data?.items.map(t=><TripCard key={t.id} trip={t} count={criteria.count} onChoose={()=>pick(t)}/>)}
 {query.data&&(page>1||query.data.has_next)&&<div className="travel-result-bar"><button className="outline" disabled={page===1} onClick={()=>setPage(v=>v-1)}>Précédent</button><small>Page {page}</small><button className="outline" disabled={!query.data.has_next} onClick={()=>setPage(v=>v+1)}>Suivant</button></div>}
 </>}
 </section>
}

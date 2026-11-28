import {t as tr} from './i18n';
import {useEffect,useState} from 'react';
import {localToday} from './search';
import {selectionQuery,type Quote} from './booking-api';
import {ArrowLeft,ArrowRight,BusFront,ShieldCheck,SlidersHorizontal,Search,CheckCircle2,MapPin} from 'lucide-react';
import {useTravel,tripPath,defaultFilters,priceText,timeText,dayText,durationText,minimumTripTotal,compatible,type Trip,type TripPage,type Criteria,type Filters,roundPath,type RoundPage,type RoundOffer} from './travel-api';
import {PartnerLogo} from './PartnerCard';
import {HomeCardCarousel} from './HomeCardCarousel';
import './company-options.css';
import './round-offers.css';

export function TripCard({trip,count,onChoose}:{trip:Trip;count:number;onChoose:()=>void}){
 return <article className="panel trip-card">
 <div className="trip-company"><PartnerLogo key={trip.company_id} src={'/api/v1/travel/partners/'+trip.company_id+'/logo/'} name={trip.company}/><div><strong>{trip.company}</strong><small><ShieldCheck size={14}/> Vérifiée</small></div></div>
 <div className="trip-timeline"><div className="trip-stop"><strong className="trip-time">{timeText(trip.starts_at)}</strong><b>{trip.origin}</b><small>{trip.boarding_point}</small></div><div className="trip-middle"><div className="trip-line"><i/><span/><i/></div><BusFront size={20}/><small>{durationText(trip.duration_minutes)}</small></div><div className="trip-stop arrival"><strong className="trip-time">{timeText(trip.ends_at)}</strong><b>{trip.destination}</b><small>{trip.arrival_point}</small>{trip.ends_at.slice(0,10)!==trip.starts_at.slice(0,10)&&<small>{dayText(trip.ends_at)}</small>}</div></div>
 <div className="trip-fare"><div><small>À partir de / passager</small><h3>{priceText(trip.from_price)}</h3>{count>1&&<small>Total min. : {priceText(minimumTripTotal(trip,count))}</small>}{trip.standard_remaining>0&&trip.premium_price>0&&<small>Standard : {priceText(trip.price)}</small>}{trip.premium_remaining>0&&<small>Premium : {priceText(trip.premium_price)}</small>}</div><div><span>{trip.remaining} places restantes</span>{trip.premium_price>0&&<small>{trip.standard_remaining} Std · {trip.premium_remaining} Premium</small>}<small>{trip.bus_name}</small></div></div>
 <button className="primary trip-choose" onClick={onChoose}>Choisir <ArrowRight size={18}/></button>
 </article>
}
export function RoundOfferCard({offer,count,onChoose}:{offer:RoundOffer;count:number;onChoose:()=>void}){return <article className="panel round-offer"><div className="trip-company"><PartnerLogo name={offer.company} src={'/api/v1/travel/partners/'+offer.company_id+'/logo/'}/><div><strong>{offer.company}</strong><small><ShieldCheck size={14}/> Aller et retour disponibles</small></div></div><div className="round-legs">{[{label:'Aller',trip:offer.out},{label:'Retour',trip:offer.ret}].map(({label,trip})=><div key={label}><small>{label} · {dayText(trip.starts_at)}</small><strong>{timeText(trip.starts_at)} → {timeText(trip.ends_at)}</strong><span>{trip.origin} → {trip.destination}</span><small>{trip.remaining} places restantes · {trip.bus_name}</small></div>)}</div><div className="round-total"><small>Total minimum pour {count} passager(s)</small><strong>{priceText(offer.total)}</strong></div><button type="button" className="primary" onClick={onChoose}>Choisir cette offre <ArrowRight size={18}/></button></article>}
export function CompanyOptions({companies,selected,onChoose}:{companies:NonNullable<TripPage['companies']>;selected:string;onChoose:(id:string)=>void}){return <section className="panel company-options company-options-premium"><div className="company-options-head"><h2>Compagnies disponibles ({companies.length})</h2><button type="button" className="company-all" aria-pressed={!selected} onClick={()=>onChoose('')}>Toutes</button></div><HomeCardCarousel kind="companies" label="Choisir une compagnie">{companies.map(c=><button type="button" key={c.id} className="company-filter-card" title={c.name} aria-label={c.name+" · "+c.departures+" départ(s) disponible(s)"} aria-pressed={selected===String(c.id)} onClick={()=>onChoose(String(c.id))}><PartnerLogo key={c.id} name={c.name} src={'/api/v1/travel/partners/'+c.id+'/logo/'}/><span className="company-filter-info"><strong>{c.name}</strong><small className="company-filter-count">{c.departures} départ{c.departures!==1?'s':''} disponible{c.departures!==1?'s':''}</small><small className="company-filter-verified"><ShieldCheck size={13}/> Vérifiée</small></span><CheckCircle2 className="company-filter-check" size={18} aria-hidden="true"/></button>)}</HomeCardCarousel>{companies.length>2&&<small className="company-slide-hint">Faites défiler pour comparer les compagnies.</small>}</section>}
function Status({loading,error,retry,empty}:{loading:boolean;error:string;retry:()=>void;empty:boolean}){
 if(loading)return <div className="panel travel-loading" role="status"><span className="travel-spinner"/> Recherche des départs…</div>;
 if(error)return <div className="panel travel-empty" role="alert"><p>{error}</p><button className="outline" onClick={retry}>{tr("Réessayer")}</button></div>;
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
export default function TravelResults({criteria,initialTrip,initialCompanyId='',onBack,onContinue}:{criteria:Criteria;initialTrip:Trip|null;initialCompanyId?:string;onBack:()=>void;onContinue:(out:Trip,ret:Trip|null)=>void}){
 const [filters,setFilters]=useState<Filters>({...defaultFilters,company_id:initialTrip?'':initialCompanyId}),[show,setShow]=useState(false),[page,setPage]=useState(1),[out,setOut]=useState<Trip|null>(initialTrip),[ret,setRet]=useState<Trip|null>(null);
 const [returnDate,setReturnDate]=useState(criteria.back);
 const [paired,setPaired]=useState(criteria.round&&!initialTrip),[offerPage,setOfferPage]=useState(1);
 const showOffers=paired&&!out;
 const offers=useTravel<RoundPage>(showOffers&&returnDate>=criteria.date&&returnDate<=localToday(new Date(Date.now()+365*86400000))?roundPath({...criteria,back:returnDate},offerPage):null);
 const returnLeg=criteria.round&&!!out;
 const earliest=out?localToday(new Date(out.ends_at)):criteria.date;
 const maxDate=localToday(new Date(Date.now()+365*86400000));
 const returnDateValid=!!returnDate&&returnDate>=earliest&&returnDate<=maxDate;
 const done=!!out&&(!criteria.round||!!ret);
 const query=useTravel<TripPage>(showOffers||done||(returnLeg&&!returnDateValid)?null:tripPath({...criteria,back:returnDate},filters,page,returnLeg,out?.ends_at));
 const companyKey=tripPath({...criteria,back:returnDate},{...filters,company_id:''},1,returnLeg,out?.ends_at);
 const [savedCompanies,setSavedCompanies]=useState<{key:string;items:NonNullable<TripPage['companies']>}>({key:'',items:[]});
 useEffect(()=>{if(query.data?.companies)setSavedCompanies({key:companyKey,items:query.data.companies})},[query.data,companyKey]);
 const companies=query.data?.companies??(savedCompanies.key===companyKey?savedCompanies.items:[]);
 const selection=done&&out?{out:out.id,count:criteria.count,...(ret?{ret:ret.id}:{})}:null;
 const quote=useTravel<Quote>(selection?'quote/'+selectionQuery(selection):null,100);
 const ready=!!selection&&!quote.loading&&!quote.error&&quote.data?.count===criteria.count&&quote.data?.trips[0]?.id===selection.out&&(!ret||quote.data?.trips[1]?.id===ret.id);
 function filter(key:keyof Filters,value:string){setFilters(old=>({...old,[key]:value}));setPage(1)}
 function pick(t:Trip){if(returnLeg&&out){if(compatible(out,t))setRet(t)}else{setOut(t);setPage(1);setFilters(defaultFilters)}}
 function resetChoice(){if(ret)setRet(null);else{setOut(null);setRet(null)}setPage(1);setFilters(defaultFilters)}
 return <section className="travel-results">
 <div className="travel-heading"><div className="travel-heading-top"><button type="button" onClick={onBack}><ArrowLeft size={19}/> Résultats</button>{!done&&!showOffers&&<button type="button" aria-label="Afficher les filtres" aria-expanded={show} title="Filtres" onClick={()=>setShow(v=>!v)}><SlidersHorizontal size={21}/></button>}</div><h1>{showOffers?criteria.origin:returnLeg?criteria.destination:criteria.origin} {showOffers?'⇄':'→'} {showOffers?criteria.destination:returnLeg?criteria.origin:criteria.destination}</h1><p>{dayText(returnLeg?(returnDate||earliest):criteria.date)}{showOffers&&returnDateValid?' – '+dayText(returnDate):''} · {criteria.count} passager(s)</p>{criteria.round&&<small>{showOffers?'Offres aller-retour par compagnie':done?'Aller-retour sélectionné':returnLeg?'Étape 2 sur 2 · Retour':'Étape 1 sur 2 · Aller'}</small>}</div>
 {showOffers?<><div className="panel travel-return-date"><label>Date de retour<input type="date" min={criteria.date} max={maxDate} value={returnDate} onChange={e=>{setReturnDate(e.target.value);setOfferPage(1)}}/></label>{!returnDateValid&&<small role="alert">Choisissez une date de retour valide.</small>}<small>Une combinaison recommandée par compagnie, selon les places et horaires réels.</small><button type="button" className="outline" onClick={()=>{setPaired(false);setPage(1);setFilters(defaultFilters)}}>Choisir l’aller et le retour séparément</button></div>
 <Status loading={offers.loading} error={offers.error} retry={offers.retry} empty={false}/>
 {offers.data&&<><h2>{offers.data.total} compagnie(s) avec aller-retour</h2>{offers.data.total===0&&<div className="panel travel-empty"><strong>Aucune offre aller-retour avec la même compagnie</strong><p>Changez la date ou combinez deux compagnies.</p></div>}{offers.data.items.map(offer=><RoundOfferCard key={offer.company_id} offer={offer} count={criteria.count} onChoose={()=>{setOut(offer.out);setRet(offer.ret);setPaired(false)}}/>)}{(offerPage>1||offers.data.has_next)&&<div className="travel-result-bar"><button className="outline" disabled={offerPage===1} onClick={()=>setOfferPage(v=>v-1)}>Précédent</button><small>Page {offerPage}</small><button className="outline" disabled={!offers.data.has_next} onClick={()=>setOfferPage(v=>v+1)}>Suivant</button></div>}</>}
 </>:<>
 {!out&&criteria.round&&<button type="button" className="outline" onClick={()=>{setPaired(true);setOfferPage(1)}}>Voir les offres aller-retour par compagnie</button>}
 {out&&<div className="panel travel-selection"><CheckCircle2 size={22}/><div><strong>Aller sélectionné</strong><p>{out.company} · {timeText(out.starts_at)} · {priceText(minimumTripTotal(out,criteria.count))}</p></div><button className="outline" onClick={()=>{setOut(null);setRet(null);setPage(1);setFilters(defaultFilters)}}>{tr("Modifier")}</button></div>}
 {returnLeg&&!done&&<div className="panel travel-return-date"><label>Date de retour<input type="date" min={earliest} max={maxDate} value={returnDate} onChange={e=>{setReturnDate(e.target.value);setRet(null);setPage(1)}}/></label>{!returnDateValid&&<small role="alert">Choisissez une date de retour à partir du {dayText(earliest)}.</small>}</div>}
 {done&&out?<section className="panel travel-summary"><h2>Votre voyage</h2><p><MapPin size={17}/> {out.origin} → {out.destination} · {dayText(out.starts_at)} · {timeText(out.starts_at)}</p>{ret&&<p><MapPin size={17}/> {ret.origin} → {ret.destination} · {dayText(ret.starts_at)} · {timeText(ret.starts_at)}</p>}<h3>Total minimum : {ready&&quote.data?priceText(quote.data.total):'—'}</h3>{quote.loading&&<small role="status">Vérification des places et du tarif…</small>}{quote.error&&<p role="alert">{quote.error} <button type="button" className="outline" onClick={quote.retry}>Réessayer</button></p>}<small>Places non bloquées.</small><button className="primary" disabled={!ready} onClick={()=>{if(ready&&quote.data)onContinue(quote.data.trips[0],ret?quote.data.trips[1]:null)}}>Réserver <ArrowRight size={18}/></button><button className="outline" onClick={resetChoice}>{tr("Modifier")}</button></section>:<>
 <div className="travel-result-bar"><strong aria-live="polite">{query.loading?'Recherche…':query.data?query.data.total+' départ(s) trouvé(s)':'Résultats'}</strong><label className="travel-sort"><span className="muted">Trier</span><select value={filters.sort} onChange={e=>filter('sort',e.target.value)}><option value="price">Prix croissant</option><option value="departure">Heure de départ</option><option value="duration">Durée du voyage</option></select></label></div>
 {companies.length>0&&<CompanyOptions companies={companies} selected={filters.company_id||''} onChoose={id=>filter('company_id',id)}/>} {show&&<div className="panel travel-filters"><label>Horaire<select value={filters.period} onChange={e=>filter('period',e.target.value)}><option value="">Toute la journée</option><option value="morning">Matin (avant 12 h)</option><option value="afternoon">Après-midi (12–18 h)</option><option value="evening">Soir (18–24 h)</option></select></label><label>Prix max. / passager<input type="number" min={1} max={1000000} value={filters.max_price} onChange={e=>filter('max_price',e.target.value)} placeholder="FCFA"/></label><button className="outline" onClick={()=>{setFilters(defaultFilters);setPage(1)}}>Réinitialiser</button></div>}
 <Status loading={query.loading} error={query.error} retry={query.retry} empty={query.data?.total===0}/>
 {query.data?.items.map(t=><TripCard key={t.id} trip={t} count={criteria.count} onChoose={()=>pick(t)}/>)}
 {query.data&&(page>1||query.data.has_next)&&<div className="travel-result-bar"><button className="outline" disabled={page===1} onClick={()=>setPage(v=>v-1)}>Précédent</button><small>Page {page}</small><button className="outline" disabled={!query.data.has_next} onClick={()=>setPage(v=>v+1)}>Suivant</button></div>}
 </>}
 </>}
 </section>
}

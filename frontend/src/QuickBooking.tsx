import {useEffect,useRef,useState} from 'react';
import {ArrowRight,BusFront,CalendarDays,Minus,Plus,Users,X} from 'lucide-react';
import {localToday,stepPassengerCount} from './search';
import {useTravel,tripPath,defaultFilters,dayText,timeText,priceText,compatible,type Trip,type TripPage} from './travel-api';
import {selectionQuery,type Quote} from './booking-api';
import {t,useLanguage} from './i18n';
import './quick-booking.css';

export function quickSelection(out:Trip|undefined,ret:Trip|undefined,round:boolean,count:number){
 if(!out||!Number.isInteger(count)||count<1||count>100||out.remaining<count)return null;
 if(round&&(!ret||ret.id===out.id||ret.remaining<count||out.origin!==ret.destination||out.destination!==ret.origin||!compatible(out,ret)))return null;
 return {out:out.id,count,...(round&&ret?{ret:ret.id}:{})};
}
export default function QuickBooking({trip,initialCount,onClose,onBook}:{trip:Trip;initialCount:number;onClose:()=>void;onBook:(trip:Trip,count:number,ret?:Trip)=>void}){
 useLanguage();
 const dialog=useRef<HTMLDialogElement>(null);
 const originalDate=localToday(new Date(trip.starts_at));
 const today=localToday();
 const maxDate=localToday(new Date(Date.now()+365*86400000));
 const [date,setDate]=useState(originalDate),[back,setBack]=useState(localToday(new Date(trip.ends_at))),[round,setRound]=useState(false),[count,setCount]=useState(initialCount),[outId,setOutId]=useState<number|null>(null),[retId,setRetId]=useState<number|null>(null);
 useEffect(()=>{const el=dialog.current;if(!el)return;el.showModal();const old=document.body.style.overflow;document.body.style.overflow='hidden';return()=>{if(el.open)el.close();document.body.style.overflow=old}},[]);
 const validDate=date>=today&&date<=maxDate;
 const criteria={origin:trip.origin,destination:trip.destination,date,back,round,count};
 const otherDate=date!==originalDate;
 const outgoing=useTravel<TripPage>(validDate&&otherDate?tripPath(criteria,{...defaultFilters,company_id:String(trip.company_id),sort:'departure'}):null,100);
 const out=validDate?(otherDate?outgoing.data?.items.find(x=>x.id===outId):trip):undefined;
 const earliest=out?localToday(new Date(out.ends_at)):date;
 const returnValid=round&&!!out&&back>=earliest&&back<=maxDate;
 const returns=useTravel<TripPage>(returnValid?tripPath(criteria,{...defaultFilters,sort:'departure'},1,true,out?.ends_at):null,100);
 const ret=returns.data?.items.find(x=>x.id===retId&&out&&compatible(out,x));
 const selected=quickSelection(out,ret,round,count);
 const quote=useTravel<Quote>(selected?'quote/'+selectionQuery(selected):null,100);
 const fresh=quote.data;
 const ready=!!selected&&!!fresh&&fresh.count===count&&fresh.trips[0]?.id===selected.out&&(!round||fresh.trips[1]?.id===selected.ret)&&!quote.loading&&!quote.error;
 function changeDate(value:string){setDate(value);setOutId(null);setRetId(null);if(back<value)setBack(value)}
 function changeCount(step:-1|1){setCount(n=>stepPassengerCount(n,step));setRetId(null)}
 function submit(){if(ready&&fresh){onBook(fresh.trips[0],count,round?fresh.trips[1]:undefined);onClose()}}
 return <dialog ref={dialog} className="quick-booking" aria-labelledby="quick-booking-title" onCancel={e=>{e.preventDefault();onClose()}} onClick={e=>{if(e.target===dialog.current)onClose()}}>
 <div className="quick-booking-content"><div className="quick-handle" aria-hidden="true"/><header className="quick-head"><div><h2 id="quick-booking-title">{t('Réserver ce trajet')}</h2><p>{trip.origin} → {trip.destination}</p></div><button type="button" className="quick-close" aria-label={t('Fermer')} onClick={onClose}><X size={21}/></button></header>
 <div className="quick-identity"><span><BusFront size={23}/></span><div><strong>{trip.company}</strong><small>{out?dayText(out.starts_at)+' · '+timeText(out.starts_at):t('Départs selon disponibilité')}</small></div></div>
 <fieldset className="quick-fieldset"><legend>{t('Type de trajet')}</legend><div className="quick-segments"><button type="button" aria-pressed={!round} onClick={()=>{setRound(false);setRetId(null)}}>{t('Aller simple')}</button><button type="button" aria-pressed={round} onClick={()=>{setRound(true);if(back<earliest)setBack(earliest)}}>{t('Aller-retour')}</button></div></fieldset>
 <div className="quick-dates"><label>{t('Date de départ')}<div className="quick-field"><CalendarDays size={19}/><input type="date" min={today} max={maxDate} value={date} onChange={e=>changeDate(e.target.value)}/></div></label>{round&&<label>{t('Date de retour')}<div className="quick-field"><CalendarDays size={19}/><input type="date" min={earliest} max={maxDate} value={back} onChange={e=>{setBack(e.target.value);setRetId(null)}}/></div></label>}</div>
 {otherDate&&<div className="quick-options">{outgoing.loading?<small role="status">{t('Chargement…')}</small>:outgoing.error?<div role="alert">{outgoing.error}<button type="button" className="outline" onClick={outgoing.retry}>{t('Réessayer')}</button></div>:<label>{t('Horaire de départ')}<select value={out?.id??''} onChange={e=>{setOutId(Number(e.target.value)||null);setRetId(null)}}><option value="">{t('Choisir un départ')}</option>{outgoing.data?.items.map(x=><option key={x.id} value={x.id}>{timeText(x.starts_at)} · {x.bus_name} · {priceText(x.from_price)}</option>)}</select>{outgoing.data?.items.length===0&&<small>{t('Aucun départ trouvé')}</small>}{outgoing.data?.has_next&&<small>{t('Autres horaires via la recherche principale.')}</small>}</label>}</div>}
 {round&&out&&<div className="quick-options">{returns.loading?<small role="status">{t('Chargement…')}</small>:returns.error?<div role="alert">{returns.error}<button type="button" className="outline" onClick={returns.retry}>{t('Réessayer')}</button></div>:<label>{t('Horaire de retour')}<select value={ret?.id??''} onChange={e=>setRetId(Number(e.target.value)||null)}><option value="">{t('Choisir un départ')}</option>{returns.data?.items.filter(x=>compatible(out,x)).map(x=><option key={x.id} value={x.id}>{timeText(x.starts_at)} · {x.company} · {priceText(x.from_price)}</option>)}</select>{returns.data?.items.length===0&&<small>{t('Aucun départ trouvé')}</small>}{returns.data?.has_next&&<small>{t('Autres horaires via la recherche principale.')}</small>}</label>}</div>}
 <fieldset className="quick-fieldset"><legend>{t('Passagers')}</legend><div className="quick-count"><Users size={20}/><span>{t('Nombre de places')}</span><button type="button" aria-label={t('Retirer un passager')} disabled={count<=1} onClick={()=>changeCount(-1)}><Minus size={19}/></button><strong aria-live="polite">{count}</strong><button type="button" aria-label={t('Ajouter un passager')} disabled={count>=100} onClick={()=>changeCount(1)}><Plus size={19}/></button></div></fieldset>
 {out&&out.remaining<count&&<p role="alert" className="quick-warning">{t('Places insuffisantes')}</p>}
 {quote.error&&<div className="quick-warning" role="alert">{quote.error}<button type="button" className="outline" onClick={quote.retry}>{t('Réessayer')}</button></div>}
 <footer className="quick-footer"><div><small>{t('Total minimum')}</small><strong aria-live="polite">{ready&&fresh?priceText(fresh.total):'—'}</strong></div><button type="button" className="primary" disabled={!ready} onClick={submit}>{t('Continuer')}<ArrowRight size={18}/></button><small>{t('Places non bloquées.')}</small></footer>
 </div></dialog>
}

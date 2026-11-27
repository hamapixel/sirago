import {useEffect,useRef,useState} from 'react';
import {ArrowRight,BusFront,CalendarDays,Users,X} from 'lucide-react';
import {localToday,validSearch} from './search';
import {PassengerCounter} from './PassengerCounter';
import {dayText,type Trip,type Criteria} from './travel-api';
import {t,useLanguage} from './i18n';
import './quick-booking.css';

export function featuredCriteria(trip:Trip,date:string,back:string,round:boolean,count:number,today:string,maxDate:string):Criteria|null{
 if(!validSearch(trip.origin,trip.destination,date,back,round,count,today)||date>maxDate||(round&&back>maxDate))return null;
 return {origin:trip.origin,destination:trip.destination,date,back:round?back:'',round,count};
}
export default function QuickBooking({trip,initialCount,onClose,onSearch}:{trip:Trip;initialCount:number;onClose:()=>void;onSearch:(criteria:Criteria,companyId:number)=>void}){
 useLanguage();
 const dialog=useRef<HTMLDialogElement>(null);
 const today=localToday();
 const maxDate=localToday(new Date(Date.now()+365*86400000));
 const [date,setDate]=useState(localToday(new Date(trip.starts_at))),[back,setBack]=useState(localToday(new Date(trip.ends_at))),[round,setRound]=useState(false),[count,setCount]=useState(initialCount);
 useEffect(()=>{const el=dialog.current;if(!el)return;el.showModal();const old=document.body.style.overflow;document.body.style.overflow='hidden';return()=>{if(el.open)el.close();document.body.style.overflow=old}},[]);
 const criteria=featuredCriteria(trip,date,back,round,count,today,maxDate);
 function changeDate(value:string){setDate(value);if(value&&back<value)setBack(value)}
 function submit(){if(criteria){onSearch(criteria,trip.company_id);onClose()}}
 return <dialog ref={dialog} className="quick-booking" aria-labelledby="quick-booking-title" onCancel={e=>{e.preventDefault();onClose()}} onClick={e=>{if(e.target===dialog.current)onClose()}}>
 <form className="quick-booking-content" onSubmit={e=>{e.preventDefault();submit()}}><div className="quick-handle" aria-hidden="true"/><header className="quick-head"><div><h2 id="quick-booking-title">{t('Réserver ce trajet')}</h2><p>{trip.origin} → {trip.destination}</p></div><button type="button" className="quick-close" aria-label={t('Fermer')} onClick={onClose}><X size={21}/></button></header>
 <div className="quick-identity"><span><BusFront size={23}/></span><div><strong>{trip.company}</strong><small>{dayText(trip.starts_at)}</small></div></div>
 <fieldset className="quick-fieldset"><legend>{t('Type de trajet')}</legend><div className="quick-segments"><button type="button" aria-pressed={!round} onClick={()=>setRound(false)}>{t('Aller simple')}</button><button type="button" aria-pressed={round} onClick={()=>{setRound(true);if(back<date)setBack(date)}}>{t('Aller-retour')}</button></div></fieldset>
 <div className="quick-dates"><label>{t('Ville de départ')}<div className="quick-field quick-city">{trip.origin}</div></label><label>{t('Ville d’arrivée')}<div className="quick-field quick-city">{trip.destination}</div></label>
 <label>{t('Date de départ')}<div className="quick-field"><CalendarDays size={19}/><input type="date" required min={today} max={maxDate} value={date} onChange={e=>changeDate(e.target.value)}/></div></label>
 {round&&<label>{t('Date de retour')}<div className="quick-field"><CalendarDays size={19}/><input type="date" required min={date||today} max={maxDate} value={back} onChange={e=>setBack(e.target.value)}/></div></label>}</div>
 <fieldset className="quick-fieldset"><legend>{t('Passagers')}</legend><div className="quick-count"><Users size={20}/><span>{t('Nombre de places')}</span><PassengerCounter count={count} onChange={setCount}/></div></fieldset>
 <p className="quick-search-note">Choisissez les horaires parmi les départs disponibles après la recherche.</p>
 <button type="submit" className="primary quick-search-submit" disabled={!criteria}>{t('Rechercher')}<ArrowRight size={18}/></button>
 </form></dialog>;
}

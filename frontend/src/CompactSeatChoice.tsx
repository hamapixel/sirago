import {Armchair,Crown,Check} from 'lucide-react';
import {priceText,type Trip} from './travel-api';
import {t,useLanguage} from './i18n';
export function canChangeSeat(trip:Pick<Trip,'premium_price'|'premium_remaining'|'standard_remaining'>,premium:boolean,count:number,premiumCount:number){
 return premium?count-premiumCount<trip.standard_remaining:trip.premium_price>0&&premiumCount<trip.premium_remaining;
}
export default function CompactSeatChoice({trip,premium,count,premiumCount,disabled,passenger,leg,onChange}:{trip:Trip;premium:boolean;count:number;premiumCount:number;disabled:boolean;passenger:number;leg:string;onChange:(value:boolean)=>void}){
 useLanguage();
 const options=[{value:false,title:'Standard',Icon:Armchair,price:trip.price,remaining:trip.standard_remaining,offered:true},{value:true,title:'Premium',Icon:Crown,price:trip.premium_price,remaining:trip.premium_remaining,offered:trip.premium_price>0}];
 return <div role="group" aria-label={t('Changer de catégorie')+' · '+t('Passager')+' '+passenger+' '+leg} className="explicit-seat-grid">{options.map(o=>{const selected=premium===o.value;const available=o.offered&&(selected?o.remaining>0:canChangeSeat(trip,premium,count,premiumCount));return <button key={o.title} type="button" className={'explicit-seat '+(o.value?'is-premium':'is-standard')+(selected?' selected':'')} aria-pressed={selected} disabled={disabled||!available} onClick={()=>onChange(o.value)}><span className="explicit-seat-heading"><o.Icon size={19}/><strong>{t(o.title)}</strong>{selected&&<Check size={15}/>}</span><strong>{o.offered?priceText(o.price):'—'}</strong><small>{!o.offered?'Non proposé':!available?'Complet pour votre groupe':o.remaining+' places disponibles'}</small></button>})}</div>
}

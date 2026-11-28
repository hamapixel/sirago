import {Armchair,Crown,ArrowUpDown} from 'lucide-react';
import {priceText,type Trip} from './travel-api';
import {t,useLanguage} from './i18n';
export function canChangeSeat(trip:Pick<Trip,'premium_price'|'premium_remaining'|'standard_remaining'>,premium:boolean,count:number,premiumCount:number){
 return premium?count-premiumCount<trip.standard_remaining:trip.premium_price>0&&premiumCount<trip.premium_remaining;
}
export default function CompactSeatChoice({trip,premium,count,premiumCount,disabled,passenger,leg,onChange}:{trip:Trip;premium:boolean;count:number;premiumCount:number;disabled:boolean;passenger:number;leg:string;onChange:(value:boolean)=>void}){
 useLanguage();
 const available=canChangeSeat(trip,premium,count,premiumCount);
 const hasAlternative=trip.premium_price>0||premium;
 const Icon=premium?Crown:Armchair;
 const next=premium?'Standard':'Premium';
 return <div className={'compact-seat '+(premium?'is-premium':'is-standard')}>
 <span className="compact-seat-icon"><Icon size={22}/></span><div className="compact-seat-info"><strong>{t(premium?'Premium':'Standard')}</strong><small>{hasAlternative?(available?t(next)+' · '+priceText(premium?trip.price:trip.premium_price):t(next)+' · Complet pour votre groupe'):'Premium non proposé'}</small></div>
 <strong className="compact-seat-price">{priceText(premium?trip.premium_price:trip.price)}</strong>
 {hasAlternative&&<button type="button" className="compact-seat-switch" disabled={disabled||!available} aria-label={t('Changer de catégorie')+' · '+t('Passager')+' '+passenger+' '+leg+' · '+t(next)} title={t('Changer de catégorie')+' : '+t(next)} onClick={()=>onChange(!premium)}><ArrowUpDown size={20}/></button>}
 </div>
}

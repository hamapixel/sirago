import {Armchair,Crown,Check} from 'lucide-react';
import {priceText,type Trip} from './travel-api';

type Props={trip:Pick<Trip,'price'|'premium_price'|'standard_remaining'|'premium_remaining'>;premium:boolean;disabled:boolean;label:string;onChange:(premium:boolean)=>void};

export default function SeatCategoryCards({trip,premium,disabled,label,onChange}:Props){
 const options=[{premium:false,title:'Standard',price:trip.price,remaining:trip.standard_remaining,Icon:Armchair},...(trip.premium_price>0?[{premium:true,title:'Premium',price:trip.premium_price,remaining:trip.premium_remaining,Icon:Crown}]:[])];
 return <div className="seat-category-group" role="group" aria-label={label}>

 <div className={'seat-category-grid'+(options.length===1?' single':'')}>
 {options.map(o=><button key={o.title} type="button" className={'seat-category-card '+(o.premium?'premium':'standard')+(premium===o.premium?' selected':'')} aria-label={o.title+' · '+priceText(o.price)+(o.remaining===0?' · Complet':'')} aria-pressed={premium===o.premium} disabled={disabled||o.remaining<=0} onClick={()=>onChange(o.premium)}>
 {premium===o.premium&&<Check className="seat-selected-check" size={15} aria-hidden="true"/>}
 <o.Icon size={23} aria-hidden="true"/><strong>{o.title}</strong><span>{priceText(o.price)}</span>{o.remaining<=0&&<small>Complet</small>}
 </button>)}
 </div></div>
}

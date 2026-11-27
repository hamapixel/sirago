import {useState} from 'react';
import {Minus,Plus} from 'lucide-react';
import {stepPassengerCount} from './search';
import './passenger-counter.css';
export function parsePassengerInput(raw:string):number|null{
 if(!/^\d+$/.test(raw))return null;
 return Math.max(1,Math.min(100,Number(raw)));
}
export function PassengerCounter({count,onChange}:{count:number;onChange:(value:number)=>void}){
 const [blank,setBlank]=useState(false);
 function step(delta:-1|1){setBlank(false);onChange(stepPassengerCount(count,delta))}
 return <div className="passenger-counter" role="group" aria-label="Nombre de passagers">
  <button type="button" className="counter" disabled={count<=1} aria-label="Retirer un passager" onClick={()=>step(-1)}><Minus size={18}/></button>
  <input type="text" inputMode="numeric" autoComplete="off" aria-label="Nombre de passagers" value={blank?'':String(count)} onFocus={e=>e.currentTarget.select()} onBlur={()=>setBlank(false)} onChange={e=>{const raw=e.target.value;if(raw===''){setBlank(true);return}const next=parsePassengerInput(raw);if(next!==null){setBlank(false);onChange(next)}}} onKeyDown={e=>{if(e.key==='ArrowUp'||e.key==='ArrowDown'){e.preventDefault();step(e.key==='ArrowUp'?1:-1)}if(e.key==='Enter')setBlank(false)}}/>
  <button type="button" className="counter" disabled={count>=100} aria-label="Ajouter un passager" onClick={()=>step(1)}><Plus size={18}/></button>
 </div>
}

import {localities,localityMetadata} from './localities';
export const cities=localities;
export function localToday(now=new Date()){const parts=new Intl.DateTimeFormat('en-CA',{timeZone:'Africa/Bamako',calendar:'gregory',numberingSystem:'latn',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);const get=(key:string)=>parts.find(p=>p.type===key)?.value??'';return get('year')+'-'+get('month')+'-'+get('day');}
export function validSearch(from:string,to:string,date:string,returnDate:string,round:boolean,count:number,today:string){return cities.includes(from)&&cities.includes(to)&&from!==to&&!!date&&date>=today&&(!round||(!!returnDate&&returnDate>=date))&&Number.isInteger(count)&&count>=1&&count<=100;}

export function stepPassengerCount(count:number,step:-1|1){return Math.min(100,Math.max(1,count+step));}

export const normalizeCity=(value:string)=>value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('fr').trim();
export const canonicalCity=(value:string)=>cities.find(c=>normalizeCity(c)===normalizeCity(value))??value;
export const matchingCities=(value:string)=>{const q=normalizeCity(value);if(!q)return [];return cities.filter(c=>normalizeCity(c).includes(q)).sort((a,b)=>Number(normalizeCity(b).startsWith(q))-Number(normalizeCity(a).startsWith(q))||Number(localityMetadata[b]?.country==='ML')-Number(localityMetadata[a]?.country==='ML')||a.localeCompare(b,'fr')).slice(0,20)};

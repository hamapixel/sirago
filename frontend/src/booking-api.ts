import {type Trip} from './travel-api';
export type Selection={out:number;ret?:number;count:number};
export type Quote={trips:Trip[];count:number;total:number};
export type Booking={id:number;reference:string;count:number;status:'HELD'|'EXPIRED'|'CANCELLED'|'TEST_PAID'|'REPORTED';replacement_id?:number|null;retained_id?:number|null;ticket_mode?:'group'|'individual';simulation_enabled?:boolean;sandbox_checkout_enabled?:boolean;sandbox_checkout?:{status:string;amount:number;checkout_url:string}|null;simulated_payment?:{amount:number;network:string;created_at:string}|null;expires_at:string;created_at:string;passenger_names:string[];total:number;trips:{id:number;company:string;origin:string;destination:string;starts_at:string;ends_at:string;boarding_point:string;arrival_point:string;bus_name:string;price:number;premium_price:number;premium_positions:number[];total:number}[]};
export type ReportResult=Booking&{retained_booking?:Booking|null};
export function parseSelection(search:string):Selection|null{
 const p=new URLSearchParams(search);
 const out=Number(p.get('out')),ret=Number(p.get('ret')),count=Number(p.get('count'));
 if(!Number.isSafeInteger(out)||out<=0||!Number.isSafeInteger(count)||count<1||count>100||!Number.isSafeInteger(ret)||ret<0||ret===out)return null;
 return {out,...(ret?{ret}:{}),count};
}
export function selectionQuery(s:Selection){const p=new URLSearchParams({out:String(s.out),count:String(s.count)});if(s.ret)p.set('ret',String(s.ret));return '?'+p.toString()}
export const bookingUrl=(s:Selection)=>'/booking/'+selectionQuery(s);
export const authUrl=(register:boolean,s:Selection)=> (register?'/register/':'/login/')+selectionQuery(s);
export async function bookingPost<T>(path:string,values:Record<string,unknown>):Promise<T>{
 const csrf=await fetch('/api/v1/auth/csrf/',{credentials:'same-origin',cache:'no-store'});
 if(!csrf.ok)throw new Error('Session indisponible.');
 const {csrfToken}=await csrf.json();
 const response=await fetch('/api/v1/travel/'+path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':csrfToken},body:JSON.stringify(values)});
 const result=await response.json().catch(()=>null);
 if(!response.ok)throw new Error(result?.detail||'Réservation indisponible.');
 return result as T;
}
export const bookingLabel=(status:Booking['status'])=>status==='HELD'?'En attente de paiement':status==='EXPIRED'?'Expirée':status==='TEST_PAID'?'Paiement simulé':status==='REPORTED'?'Reportée':'Annulée';
export function attemptKey(s:Selection){
 const key='sirago-booking:'+selectionQuery(s);
 try{const previous=sessionStorage.getItem(key);if(previous)return previous;const fresh=crypto.randomUUID();sessionStorage.setItem(key,fresh);return fresh}catch{return crypto.randomUUID()}
}
export function clearAttempt(s:Selection){try{sessionStorage.removeItem('sirago-booking:'+selectionQuery(s))}catch{/* storage unavailable */}}

export function effectiveBookingStatus(b:Pick<Booking,'status'|'expires_at'>,now=Date.now()):Booking['status']{return b.status==='HELD'&&Date.parse(b.expires_at)<=now?'EXPIRED':b.status}

export const normalizePassengerName=(name:string)=>name.trim().replace(/\s+/g,' ');
export function validPassengerNames(names:string[],count:number){return names.length===count&&names.every(raw=>{const n=normalizePassengerName(raw);return n.length>=2&&n.length<=100&&/\p{L}/u.test(n)&&!/[\x00-\x08\x0A-\x1F]/.test(raw)})}

export const defaultPremiumPositions=(t:Trip,count:number)=>Array.from({length:Math.max(0,count-t.standard_remaining)},(_,i)=>count-1-i).sort((a,b)=>a-b);
export const categoryTotal=(t:Trip,count:number,positions:number[])=>t.price*(count-positions.length)+t.premium_price*positions.length;
export const validCategories=(t:Trip,count:number,positions:number[])=>positions.length<=t.premium_remaining&&count-positions.length<=t.standard_remaining&&new Set(positions).size===positions.length&&positions.every(p=>Number.isInteger(p)&&p>=0&&p<count);

export const historyFilters=[['','Toutes les réservations'],['HELD','En attente de paiement'],['SASPAY_PENDING','SasPay à vérifier'],['SASPAY_PAID','SasPay confirmé (TEST)'],['TEST_PAID','Billets de test émis'],['EXPIRED','Expirées'],['CANCELLED','Annulées'],['REPORTED','Reportées'],['LATE_PAID','Paiements tardifs'],['REVIEW','Sessions à examiner']] as const;
export function historyPath(query:string,status:string,page:number){return 'bookings/?'+new URLSearchParams({q:query.trim(),status,page:String(page),page_size:'10'})}
export function historyLabel(b:Booking,now=Date.now()){
 const a=b.sandbox_checkout;
 if(a?.status==='PAID')return 'Paiement SasPay confirmé (TEST)';
 if(a?.status==='REVIEW_PAID')return 'Paiement SasPay à examiner (TEST)';
 if(a?.status==='LATE_PAID')return 'Paiement tardif (TEST)';
 if(a?.status==='PENDING')return 'Paiement SasPay à vérifier';
 if(a?.status==='EXPIRED')return 'Session SasPay expirée';
 if(a?.status==='CANCELLED')return 'Session SasPay annulée';
 if(a&&['UNKNOWN','CREATING'].includes(a.status))return 'Session SasPay à examiner';
 return bookingLabel(effectiveBookingStatus(b,now));
}
export const canVerifySasPay=(b:Booking)=>!!b.sandbox_checkout_enabled&&b.sandbox_checkout?.status==='PENDING';

export const sandboxTicketsIssued=(b:Booking)=>b.status==='TEST_PAID'&&b.sandbox_checkout?.status==='PAID';
export function returnedBookingId(search:string){const raw=new URLSearchParams(search).get('booking');if(!raw||!/^\d+$/.test(raw))return null;const id=Number(raw);return Number.isSafeInteger(id)&&id>0?id:null}

import {useEffect,useState} from 'react';
export type Trip={id:number;company_id:number;company:string;bus_name:string;origin:string;destination:string;boarding_point:string;arrival_point:string;starts_at:string;ends_at:string;duration_minutes:number;price:number;capacity:number;remaining:number;standard_remaining:number;premium_remaining:number;premium_price:number;from_price:number};
export type Criteria={origin:string;destination:string;date:string;back:string;round:boolean;count:number};
export type Filters={company:string;period:string;max_price:string;sort:string};
export type TripPage={items:Trip[];total:number;page:number;has_next:boolean};
export type HomeData={routes:{origin:string;destination:string;price:number}[];companies:{id:number;name:string;city:string}[]};
export const defaultFilters:Filters={company:'',period:'',max_price:'',sort:'price'};
export function tripPath(c:Criteria,filters:Filters=defaultFilters,page=1,returnLeg=false,after=''){
 const params=new URLSearchParams({origin:returnLeg?c.destination:c.origin,destination:returnLeg?c.origin:c.destination,date:returnLeg?c.back:c.date,passengers:String(c.count),page:String(page),sort:filters.sort});
 for(const key of ['company','period','max_price'] as const)if(filters[key].trim())params.set(key,filters[key].trim());
 if(returnLeg&&after)params.set('after',after);
 return 'search/?'+params.toString();
}
type Load<T>={key:string;data:T|null;error:string;loading:boolean};
export function useTravel<T>(path:string|null,delay=250){
 const [state,setState]=useState<Load<T>>({key:'',data:null,error:'',loading:false});
 const [revision,setRevision]=useState(0);
 const key=path?path+'#'+revision:'';
 useEffect(()=>{
  if(!path)return;
  const controller=new AbortController();
  const timer=window.setTimeout(async()=>{
   try{
    const response=await fetch('/api/v1/travel/'+path,{cache:'no-store',signal:controller.signal});
    const data=await response.json();
    if(!response.ok)throw new Error(data.detail||'Recherche indisponible.');
    if(!controller.signal.aborted)setState({key,data,error:'',loading:false});
   }catch(e){if(!controller.signal.aborted)setState({key,data:null,error:e instanceof Error?e.message:'Connexion indisponible.',loading:false});}
  },delay);
  return()=>{window.clearTimeout(timer);controller.abort()};
 },[path,delay,key]);
 return {...(state.key===key?state:{key,data:null,error:'',loading:!!path}),retry:()=>setRevision(v=>v+1)};
}
export const durationText=(minutes:number)=>Math.floor(minutes/60)+' h '+String(minutes%60).padStart(2,'0')+' min';
export const priceText=(price:number)=>price.toLocaleString('fr-FR')+' FCFA';
export const timeText=(iso:string)=>new Intl.DateTimeFormat('fr-FR',{hour:'2-digit',minute:'2-digit',timeZone:'Africa/Bamako'}).format(new Date(iso));
export const dayText=(iso:string)=>new Intl.DateTimeFormat('fr-FR',{dateStyle:'full',timeZone:'Africa/Bamako'}).format(new Date(iso.length===10?iso+'T12:00:00Z':iso));
export const compatible=(out:Trip,back:Trip)=>Date.parse(back.starts_at)>=Date.parse(out.ends_at);

export const minimumTripTotal=(t:Trip,count:number)=>{const premium=Math.max(0,count-t.standard_remaining);return (count-premium)*t.price+premium*t.premium_price};

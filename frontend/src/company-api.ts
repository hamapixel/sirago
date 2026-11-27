export type Bus={id:number;name:string;plate:string;capacity:number;premium_capacity:number;active:boolean;capacity_locked?:boolean;driver_first_name?:string;driver_last_name?:string;driver_phone?:string};
export type RouteItem={id:number;origin:string;destination:string;boarding_point:string;arrival_point:string;duration_minutes:number;price:number;active:boolean};
export type Departure={id:number;bus_id:number;bus_name:string;route_id:number;origin:string;destination:string;starts_at:string;ends_at:string;capacity:number;premium_capacity:number;premium_price:number;price:number;remaining?:number;standard_remaining?:number;premium_remaining?:number;status:'DRAFT'|'PUBLISHED'|'SUSPENDED'|'CANCELLED'};
export type Dashboard={status:'PENDING'|'VERIFIED'|'REJECTED'|'SUSPENDED';active_buses:number;active_routes:number;today_departures:number;today_capacity:number;today_total_capacity?:number;today_draft?:number;today_suspended?:number;today_cancelled?:number};
export type Page<T>={items:T[];page:number;has_next:boolean;total?:number;page_size?:number};
export async function companyGet<T>(path:string,signal?:AbortSignal):Promise<T>{
 const response=await fetch('/api/v1/company/'+path,{credentials:'same-origin',cache:'no-store',signal});
 const result=await response.json().catch(()=>null);
 if(!response.ok)throw new Error(result?.detail||'Impossible de charger les données.');
 return result as T;
}
export async function companyPost<T>(path:string,values:Record<string,unknown>):Promise<T>{
 const csrf=await fetch('/api/v1/auth/csrf/',{credentials:'same-origin',cache:'no-store'});
 if(!csrf.ok)throw new Error('Session indisponible.');
 const {csrfToken}=await csrf.json();
 const response=await fetch('/api/v1/company/'+path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':csrfToken},body:JSON.stringify(values)});
 const result=await response.json().catch(()=>null);
 if(!response.ok)throw new Error(result?.detail||'Enregistrement impossible.');
 return result as T;
}
export const allowedStatus=(status:Departure['status'],verified:boolean):Departure['status'][]=>status==='DRAFT'?verified?['PUBLISHED','CANCELLED']:['CANCELLED']:status==='PUBLISHED'?['SUSPENDED','CANCELLED']:status==='SUSPENDED'?verified?['PUBLISHED','CANCELLED']:['CANCELLED']:[];

export type DepartureFilters={date_from:string;date_to:string;route_id:string;status:string};
export const emptyFilters:DepartureFilters={date_from:'',date_to:'',route_id:'',status:''};
export function departurePath(page:number,filters:DepartureFilters){
 const params=new URLSearchParams({page:String(page)});
 for(const [key,value] of Object.entries(filters))if(value)params.set(key,value);
 return 'departures/?'+params.toString();
}
export function selectableDrafts(rows:Departure[],verified:boolean,now=Date.now()){
 return verified?rows.filter(d=>d.status==='DRAFT'&&Date.parse(d.starts_at)>now).map(d=>d.id):[];
}

export function selectableDepartures(rows:Departure[],verified:boolean,target:'PUBLISHED'|'SUSPENDED',now=Date.now()){return verified?rows.filter(d=>Date.parse(d.starts_at)>now&&(target==='PUBLISHED'?(d.status==='DRAFT'||d.status==='SUSPENDED'):d.status==='PUBLISHED')).map(d=>d.id):[]}

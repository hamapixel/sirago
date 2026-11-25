export type Bus={id:number;name:string;plate:string;capacity:number;active:boolean};
export type RouteItem={id:number;origin:string;destination:string;boarding_point:string;arrival_point:string;duration_minutes:number;price:number;active:boolean};
export type Departure={id:number;bus_id:number;bus_name:string;route_id:number;origin:string;destination:string;starts_at:string;ends_at:string;capacity:number;price:number;status:'DRAFT'|'PUBLISHED'|'SUSPENDED'|'CANCELLED'};
export type Dashboard={status:'PENDING'|'VERIFIED'|'REJECTED'|'SUSPENDED';active_buses:number;active_routes:number;today_departures:number;today_capacity:number};
export type Page<T>={items:T[];page:number;has_next:boolean};
export async function companyGet<T>(path:string):Promise<T>{
 const response=await fetch('/api/v1/company/'+path,{credentials:'same-origin',cache:'no-store'});
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

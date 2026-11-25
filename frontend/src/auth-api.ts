export type Account = {first_name:string;last_name:string;phone:string|null;email:string;role:'TRAVELER'|'COMPANY'|'ADMIN';company_role?:'OWNER'|'CLERK'|'CONTROLLER';company:null|{name:string;status:'PENDING'|'VERIFIED'|'REJECTED'|'SUSPENDED';city:string}};
export function destination(account:Account){return account.role==='ADMIN'?'/admin/':account.role==='COMPANY'?'/company/':'/app/'}
export async function currentAccount():Promise<Account|null>{
 const controller=new AbortController();
 const timer=setTimeout(()=>controller.abort(),10000);
 try{
  const response=await fetch('/api/v1/auth/me/',{credentials:'same-origin',cache:'no-store',signal:controller.signal});
  if(response.status===401)return null;
  if(!response.ok)throw new Error('Impossible de vérifier la session.');
  return await response.json();
 }finally{clearTimeout(timer)}
}
export async function authPost<T>(path:string,values:Record<string,unknown>):Promise<T>{
 const csrf=await fetch('/api/v1/auth/csrf/',{credentials:'same-origin',cache:'no-store'});
 if(!csrf.ok)throw new Error('Connexion au serveur indisponible.');
 const {csrfToken}=await csrf.json();
 const response=await fetch('/api/v1/auth/'+path+'/',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':csrfToken},body:JSON.stringify(values)});
 const result=await response.json().catch(()=>null);
 if(!response.ok)throw new Error(result?.detail||'Une erreur est survenue. Réessayez.');
 return result as T;
}

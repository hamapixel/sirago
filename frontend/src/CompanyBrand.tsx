import {useState,type ChangeEvent} from 'react';
import {BusFront,ImagePlus,Trash2} from 'lucide-react';
import {authPost,type Account} from './auth-api';

export function BrandLogo({logo}:{logo?:string}){
 return <span className="company-brand-logo">{logo?<img src={logo} alt="Logo compagnie"/>:<BusFront size={30}/>}</span>
}
export function BrandCover({banner}:{banner?:string}){
 return banner?<img className="company-brand-cover" src={banner} alt=""/>:null
}
export default function CompanyBrand({account,onUpdated}:{account:Account;onUpdated:(a:Account)=>void}){
 const [busy,setBusy]=useState(false),[message,setMessage]=useState(''),[error,setError]=useState('');
 async function save(kind:'logo'|'banner',image:string){
  setBusy(true);setError('');setMessage('');
  try{onUpdated(await authPost<Account>('company/branding',{kind,image}));setMessage('Image enregistrée.')}
  catch(e){setError(e instanceof Error?e.message:'Image indisponible.')}finally{setBusy(false)}
 }
 function choose(kind:'logo'|'banner',e:ChangeEvent<HTMLInputElement>){
  const file=e.target.files?.[0];e.target.value='';if(!file||busy)return;
  if(file.size>800*1024||!['image/png','image/jpeg','image/webp'].includes(file.type)){setError('PNG, JPEG ou WebP · 800 Ko maximum.');return}
  setBusy(true);setError('');const reader=new FileReader();
  reader.onload=()=>{if(typeof reader.result==='string')void save(kind,reader.result);else setBusy(false)};
  reader.onerror=()=>{setBusy(false);setError('Lecture impossible.')};reader.readAsDataURL(file)
 }
 const allowed=account.company?.status==='VERIFIED'||account.company?.status==='PENDING';
 return <section className="company-brand-editor"><h3>Identité visuelle</h3>{(['logo','banner'] as const).map(kind=><div className="brand-upload" key={kind}><div><strong>{kind==='logo'?'Logo':'Bannière'}</strong><small>{kind==='logo'?'Image carrée':'Image horizontale'} · 800 Ko maximum</small></div><label className="outline brand-file-label"><ImagePlus size={18}/>{kind==='logo'?'Choisir un logo':'Choisir une bannière'}<input aria-label={kind==='logo'?'Choisir un logo':'Choisir une bannière'} type="file" accept="image/png,image/jpeg,image/webp" disabled={busy||!allowed} onChange={e=>choose(kind,e)}/></label>{account.company?.[kind]&&<button className="outline" type="button" disabled={busy||!allowed} onClick={()=>save(kind,'')}><Trash2 size={16}/>Retirer</button>}</div>)}{message&&<p role="status" className="profile-success">{message}</p>}{error&&<p role="alert" className="auth-error">{error}</p>}</section>
}

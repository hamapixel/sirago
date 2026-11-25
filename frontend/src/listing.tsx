import {useState,useEffect} from 'react';
import {Search,ChevronLeft,ChevronRight,X} from 'lucide-react';
import {companyGet} from './company-api';
import './listing.css';
export const normalizeSearch=(s:string)=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('fr').trim();
export const matchesSearch=(query:string,...fields:unknown[])=>normalizeSearch(query).split(/\s+/).every(word=>normalizeSearch(fields.join(' ')).includes(word));
export function SearchField({value,onChange,placeholder='Rechercher…'}:{value:string;onChange:(v:string)=>void;placeholder?:string}){
 return <label className="list-search"><Search size={19}/><input type="search" aria-label={placeholder} placeholder={placeholder} value={value} maxLength={150} onChange={e=>onChange(e.target.value)}/>{value&&<button type="button" aria-label="Effacer la recherche" onClick={()=>onChange('')}><X size={17}/></button>}</label>
}
export function Pagination({page,size,total,onChange,disabled=false}:{page:number;size:number;total:number;onChange:(page:number)=>void;disabled?:boolean}){
 const pages=Math.max(1,Math.ceil(total/size));return <div className="list-pagination"><small aria-live="polite">{total?((page-1)*size+1)+'–'+Math.min(page*size,total)+' sur '+total:'0 résultat'}</small><nav aria-label="Pagination"><button type="button" className="outline" disabled={disabled||page<=1} onClick={()=>onChange(page-1)} aria-label="Page précédente"><ChevronLeft size={18}/></button><span>Page {page}/{pages}</span><button type="button" className="outline" disabled={disabled||page>=pages} onClick={()=>onChange(page+1)} aria-label="Page suivante"><ChevronRight size={18}/></button></nav></div>
}
export function useLocalPage<T>(rows:T[],size=10){
 const [requested,setPage]=useState(1);const page=Math.min(requested,Math.max(1,Math.ceil(rows.length/size)));
 return {rows:rows.slice((page-1)*size,page*size),page,setPage,size,total:rows.length};
}
export type ResultPage<T>={items:T[];page:number;page_size:number;total:number;has_next:boolean};
export function useCompanyList<T>(path:string,query:string,page:number,revision=0,date=''){
 const [data,setData]=useState<ResultPage<T>|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState('');
 useEffect(()=>{let active=true;setLoading(true);setError('');setData(null);const timer=window.setTimeout(()=>{const params=new URLSearchParams({q:query.trim(),page:String(page),page_size:'10'});if(date)params.set('date',date);companyGet<ResultPage<T>>(path+'?'+params).then(r=>{if(active)setData(r)}).catch(e=>{if(active)setError(e instanceof Error?e.message:'Chargement impossible.')}).finally(()=>{if(active)setLoading(false)})},200);return()=>{active=false;window.clearTimeout(timer)}},[path,query,page,revision,date]);
 return {data,loading,error};
}

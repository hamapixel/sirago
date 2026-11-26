import {useState} from 'react';
import {BusFront,MapPin,Phone,ShieldCheck} from 'lucide-react';
import {partnerInfo,partnerPhones} from './partners';
import type {PartnerCompany} from './travel-api';
import './partner-card.css';
export function PartnerLogo({src,name}:{src?:string;name:string}){
 const [failed,setFailed]=useState(false);
 return <span className="partner-logo"><BusFront size={27} aria-hidden="true"/>{src&&!failed&&<img src={src} alt={name} onError={()=>setFailed(true)}/>}</span>;
}
export function PartnerCard({company,onOpen}:{company:PartnerCompany;onOpen:()=>void}){
 const info=partnerInfo(company);
 const phones=partnerPhones(info);
 return <button type="button" className="partner-card" aria-label={'Voir les trajets de '+company.name} onClick={onOpen}><PartnerLogo key={info?.logo||company.id} src={info?.logo} name={company.name}/><span className="partner-card-info"><strong>{company.name}</strong><span><MapPin size={15}/>{info?.address||company.city}</span>{phones.length>0&&<span><Phone size={15}/>{phones[0]}</span>}<small><ShieldCheck size={14}/> Compagnie validée</small></span></button>;
}

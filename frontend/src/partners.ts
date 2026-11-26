// Fiche publique : modifier ici dans VS Code. Aucun secret ni téléphone privé.
import type {PartnerCompany} from './travel-api';
import {normalizeCity} from './search';

export type PartnerInfo={companyId?:number;name:string;city:string;logo?:string;cover?:string;address?:string;phones?:string[];location?:{latitude:number;longitude:number}};
export const PARTNERS:PartnerInfo[]=[
 {
  // companyId: 1, // recommandé : identifiant réel de la compagnie dans Django Admin
  name:'Diarra Transport',
  city:'Bamako',
  logo:'', // '/images/partners/diarra-logo.webp'
  cover:'', // '/images/partners/diarra-cover.webp'
  address:'', // Adresse publique confirmée de la gare
  phones:[], // Numéros publics confirmés, format +223XXXXXXXX
  // location:{latitude: ..., longitude: ...}, // coordonnées GPS vérifiées
 },
 // Ajouter les autres fiches ici. La compagnie doit aussi exister et être validée en base.
];

export function partnerInfo(company:Pick<PartnerCompany,'id'|'name'> & Partial<Pick<PartnerCompany,'city'>>){
 const exact=PARTNERS.find(p=>p.companyId===company.id);
 if(exact)return exact;
 const matches=PARTNERS.filter(p=>p.companyId===undefined&&normalizeCity(p.name)===normalizeCity(company.name)&&(!company.city||normalizeCity(p.city)===normalizeCity(company.city)));
 return matches.length===1?matches[0]:undefined;
}
export function partnerMapUrl(info?:PartnerInfo){
 if(!info)return '';
 const loc=info.location;
 const valid=loc&&Number.isFinite(loc.latitude)&&Number.isFinite(loc.longitude)&&Math.abs(loc.latitude)<=90&&Math.abs(loc.longitude)<=180;
 const query=valid?loc.latitude+','+loc.longitude:info.address?.trim()?[info.address,info.city,'Mali'].join(', '):'';
 return query?'https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(query):'';
}
export function partnerPhones(info?:PartnerInfo){return (info?.phones??[]).map(p=>p.replace(/[\s-]/g,'')).filter(p=>/^\+223\d{8}$/.test(p))}

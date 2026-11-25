import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {ReportAmounts,type ReportOption} from './TicketReport';
import {bookingLabel} from './booking-api';
it('affiche le supplément uniquement en mode simulé',()=>{const html=renderToStaticMarkup(<ReportAmounts previous={16000} option={{total:18000,difference:2000} as ReportOption}/>);expect(html).toContain('Supplément simulé');expect(html).toContain('Aucun argent');expect(bookingLabel('REPORTED')).toBe('Reportée')});
it('affiche un tarif inférieur sans promettre de remboursement réel',()=>{const html=renderToStaticMarkup(<ReportAmounts previous={16000} option={{total:14000,difference:-2000} as ReportOption}/>);expect(html).toContain('de moins');expect(html).toContain('Aucun argent ne sera débité ou remboursé')});

import TicketReport from './TicketReport';
import type {Booking} from './booking-api';

const outbound:Booking['trips'][number]={id:1,origin:'Bamako',destination:'Sikasso',company:'Transport',starts_at:'2026-11-26T06:00:00Z',ends_at:'2026-11-26T13:00:00Z',boarding_point:'Gare A',arrival_point:'Gare B',bus_name:'Car 01',price:8000,premium_price:12000,premium_positions:[],total:8000};
const base:Booking={id:1,reference:'test-report',status:'TEST_PAID',expires_at:outbound.starts_at,created_at:'2026-11-25T12:00:00Z',count:1,passenger_names:['Awa Test'],total:8000,trips:[outbound],ticket_mode:'group',simulation_enabled:true};

it('permet de sélectionner les passagers et prévient du remplacement de tous les QR',()=>{
 const b:Booking={...base,count:2,passenger_names:['Awa Test','Moussa Test'],total:20000,trips:[{...outbound,premium_positions:[1],total:20000}]};
 const html=renderToStaticMarkup(<TicketReport booking={b} onBack={()=>{}} onReported={()=>{}}/>);
 for(const value of ['Passagers à reporter','Awa Test','Moussa Test','Premium','Tout désélectionner','tous les anciens QR'])expect(html).toContain(value);
});

it('propose de reporter séparément l’aller ou le retour',()=>{
 const b:Booking={...base,id:2,total:15000,trips:[outbound,{...outbound,id:2,origin:'Sikasso',destination:'Bamako',boarding_point:'Gare B',arrival_point:'Gare A',starts_at:'2026-11-29T06:00:00Z',ends_at:'2026-11-29T13:00:00Z',price:7000,total:7000}]};
 const html=renderToStaticMarkup(<TicketReport booking={b} onBack={()=>{}} onReported={()=>{}}/>);
 for(const v of ['Trajet à reporter','Aller','Retour','Un seul trajet par opération'])expect(html).toContain(v);
});

import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {ReportAmounts,type ReportOption} from './TicketReport';
import {bookingLabel} from './booking-api';
it('affiche le supplément uniquement en mode simulé',()=>{const html=renderToStaticMarkup(<ReportAmounts previous={16000} option={{total:18000,difference:2000} as ReportOption}/>);expect(html).toContain('Supplément simulé');expect(html).toContain('Aucun argent');expect(bookingLabel('REPORTED')).toBe('Reportée')});
it('affiche un tarif inférieur sans promettre de remboursement réel',()=>{const html=renderToStaticMarkup(<ReportAmounts previous={16000} option={{total:14000,difference:-2000} as ReportOption}/>);expect(html).toContain('de moins');expect(html).toContain('Aucun argent ne sera débité ou remboursé')});

import TicketReport from './TicketReport';
import type {Booking} from './booking-api';
it('permet de sélectionner les passagers et prévient du remplacement de tous les QR',()=>{const b={id:1,count:2,passenger_names:['Awa Test','Moussa Test'],trips:[{origin:'Bamako',destination:'Sikasso',company:'Transport',starts_at:'2026-11-26T06:00:00Z',premium_positions:[1]}]} as Booking;const html=renderToStaticMarkup(<TicketReport booking={b} onBack={()=>{}} onReported={()=>{}}/>);for(const value of ['Passagers à reporter','Awa Test','Moussa Test','Premium','Tout désélectionner','tous les anciens QR'])expect(html).toContain(value)});

it('propose de reporter séparément l’aller ou le retour',()=>{const trip={origin:'Bamako',destination:'Sikasso',company:'Transport',starts_at:'2026-11-26T06:00:00Z',premium_positions:[]};const b={id:2,count:1,passenger_names:['Awa Test'],trips:[trip,{...trip,origin:'Sikasso',destination:'Bamako',starts_at:'2026-11-29T06:00:00Z'}]} as Booking;const html=renderToStaticMarkup(<TicketReport booking={b} onBack={()=>{}} onReported={()=>{}}/>);for(const v of ['Trajet à reporter','Aller','Retour','Un seul trajet par opération'])expect(html).toContain(v)});

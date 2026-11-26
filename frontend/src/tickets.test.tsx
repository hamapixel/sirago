import {describe,it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {TicketCard,type TestTicket} from './TestTickets';
const t:TestTicket={code:'SRG-TEST-ABC',leg:0,passenger:1,name:'Awa Test',category:'Premium',amount:12000,company:'Transport Test',origin:'Bamako',destination:'Mopti',starts_at:'2026-11-27T06:00:00Z',ends_at:'2026-11-27T13:00:00Z',boarding_point:'Gare A',arrival_point:'Gare B',qr:['010','101','010']};
describe('Billet de test',()=>{
 it('affiche les informations et le QR avec avertissement visible',()=>{const html=renderToStaticMarkup(<TicketCard ticket={t} bookingId={3}/>);for(const v of ['Awa Test','Premium','Bamako','Mopti','06:00','13:00','SRG-TEST-ABC','Non valable pour voyager','QR code de test individuel'])expect(html).toContain(v)});
 it('propose le PDF individuel et le partage',()=>{const html=renderToStaticMarkup(<TicketCard ticket={t} bookingId={3}/>);expect(html).toContain('/api/v1/travel/bookings/3/tickets/0/1/pdf/');expect(html).toContain('Télécharger');expect(html).toContain('Partager')});
});

it('affiche un billet collectif avec liste et QR collectif',()=>{const html=renderToStaticMarkup(<TicketCard ticket={{...t,count:3,names:['Awa Test','Awa Test','Baba Test'],unit_price:8000,amount:24000,category:'Standard'}} bookingId={3}/>);for(const v of ['3 personnes','Liste des 3 passagers','QR code collectif','Baba Test','Prix unitaire'])expect(html).toContain(v)});

import ReportAction,{reportUnavailableReason} from './ReportAction';
import type {Booking} from './booking-api';
const reportBooking:Booking={id:1,reference:'test-report',status:'TEST_PAID',count:1,simulation_enabled:true,passenger_names:['Awa Test'],created_at:'2026-11-25T12:00:00Z',expires_at:'2026-11-27T06:00:00Z',total:8000,trips:[{id:1,company:'Transport',origin:'Bamako',destination:'Mopti',starts_at:'2026-11-27T06:00:00Z',ends_at:'2026-11-27T13:00:00Z',boarding_point:'Gare A',arrival_point:'Gare B',bus_name:'Car 01',price:8000,premium_price:12000,premium_positions:[],total:8000}]};
it('rend le report visible pour un départ futur payé en simulation',()=>{const now=Date.parse('2026-11-25T12:00:00Z');expect(reportUnavailableReason(reportBooking,now)).toBeNull();const html=renderToStaticMarkup(<ReportAction booking={reportBooking} now={now} onReport={()=>{}}/>);expect(html).toContain('Reporter le voyage');expect(html).not.toContain('disabled')});
it('explique un départ dépassé au lieu de masquer le report',()=>{const html=renderToStaticMarkup(<ReportAction booking={reportBooking} now={Date.parse('2026-11-28T12:00:00Z')} onReport={()=>{}}/>);expect(html).toContain('Reporter le voyage');expect(html).toContain('disabled');expect(html).toContain('date de départ est dépassée')});
it('interdit le report d’une réservation non payée ou déjà reportée',()=>{expect(reportUnavailableReason({...reportBooking,status:'HELD'})).toContain('paiement simulé');expect(reportUnavailableReason({...reportBooking,status:'REPORTED'})).toContain('déjà été reportée');expect(reportUnavailableReason({...reportBooking,simulation_enabled:false})).toContain('désactivé')});

it('affiche les données de la compagnie et du car sans identifiants privés',()=>{const html=renderToStaticMarkup(<TicketCard ticket={{...t,company_city:'Bamako',bus_name:'Car 001'}} bookingId={3}/>);for(const v of ['COMPAGNIE DE TRANSPORT','Transport Test','Bamako · Car 001','BILLET TEST','Gare A','Gare B'])expect(html).toContain(v)});

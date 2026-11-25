import {describe,it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {TicketCard,type TestTicket} from './TestTickets';
const t:TestTicket={code:'SRG-TEST-ABC',leg:0,passenger:1,name:'Awa Test',category:'Premium',amount:12000,company:'Transport Test',origin:'Bamako',destination:'Mopti',starts_at:'2026-11-27T06:00:00Z',ends_at:'2026-11-27T13:00:00Z',boarding_point:'Gare A',arrival_point:'Gare B',qr:['010','101','010']};
describe('Billet de test',()=>{
 it('affiche les informations et le QR avec avertissement visible',()=>{const html=renderToStaticMarkup(<TicketCard ticket={t} bookingId={3}/>);for(const v of ['Awa Test','Premium','Bamako','Mopti','06:00','13:00','SRG-TEST-ABC','Non valable pour voyager','QR code de test individuel'])expect(html).toContain(v)});
 it('propose le PDF individuel et le partage',()=>{const html=renderToStaticMarkup(<TicketCard ticket={t} bookingId={3}/>);expect(html).toContain('/api/v1/travel/bookings/3/tickets/0/1/pdf/');expect(html).toContain('Télécharger');expect(html).toContain('Partager')});
});

it('affiche un billet collectif avec liste et QR collectif',()=>{const html=renderToStaticMarkup(<TicketCard ticket={{...t,count:3,names:['Awa Test','Awa Test','Baba Test'],unit_price:8000,amount:24000,category:'Standard'}} bookingId={3}/>);for(const v of ['3 personnes','Liste des 3 passagers','QR code collectif','Baba Test','Prix unitaire'])expect(html).toContain(v)});

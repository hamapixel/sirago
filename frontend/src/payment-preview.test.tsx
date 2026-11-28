import {describe,it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import PaymentPreview from './PaymentPreview';
import type {Booking} from './booking-api';
const b:Booking={id:1,reference:'TEST-01',count:2,status:'HELD',expires_at:new Date(Date.now()+600000).toISOString(),created_at:new Date().toISOString(),passenger_names:['Awa Test','Moussa Test'],total:20000,trips:[{id:1,company:'Transport Test',origin:'Bamako',destination:'Mopti',starts_at:'2026-12-01T06:00:00Z',ends_at:'2026-12-01T13:00:00Z',boarding_point:'Gare',arrival_point:'Gare',bus_name:'Car 01',price:8000,premium_price:12000,premium_positions:[1],total:20000}]};
const render=(booking:Booking=b)=>renderToStaticMarkup(<PaymentPreview booking={booking} onBack={()=>{}}/>);
describe('Préparation du paiement',()=>{
 it('affiche les catégories, passagers et moyens indicatifs',()=>{const html=render();for(const v of ['Awa Test','Moussa Test','Standard','Premium','Orange Money','Moov Money','Total à payer'])expect(html).toContain(v)});
 it('interdit tout paiement avant intégration',()=>{const html=render();expect(html).toMatch(/<button[^>]*disabled[^>]*>/);expect(html).toContain('Aucun débit possible');expect(html).not.toMatch(/portefeuille|parrainage|code promo/i)});
 it('affiche clairement la simulation uniquement si autorisée',()=>{const html=render({...b,simulation_enabled:true});expect(html).toContain('Simuler le paiement');expect(html).toContain('MODE TEST');expect(html).not.toMatch(/<button[^>]*disabled[^>]*>/)});
 it('distingue le succès simulé du paiement réel',()=>{const html=render({...b,status:'TEST_PAID'});expect(html).toContain('Aucun argent débité');expect(html).not.toContain('Confirmer et payer')});
 it('refuse les réservations annulées ou expirées',()=>{for(const booking of [{...b,status:'CANCELLED' as const},{...b,expires_at:'2000-01-01T00:00:00Z'}]){const html=render(booking);expect(html).toContain('ne peut plus être payée');expect(html).not.toContain('Confirmer et payer')}});
});

it('affiche le logo de la compagnie et les tarifs par catégorie dans le résumé',()=>{const html=render({...b,trips:[{...b.trips[0],company_id:17}],sandbox_checkout_enabled:true});for(const v of ['/api/v1/travel/partners/17/logo/','payment-category premium','payment-category standard','Gare','06:00','13:00','Total à payer','SANDBOX · TEST'])expect(html).toContain(v)});

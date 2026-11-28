import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {historyPath,historyLabel,canVerifySasPay,type Booking} from './booking-api';
import VerifySasPay from './VerifySasPay';
import PaymentPreview from './PaymentPreview';
import {BookingPassengerList} from './BookingSpace';
const b:Booking={id:25,reference:'test',status:'HELD',count:1,passenger_names:['Awa Test'],total:8000,created_at:'2026-11-26T10:32:00Z',expires_at:'2026-11-26T10:47:00Z',trips:[],sandbox_checkout_enabled:true,simulation_enabled:true,sandbox_checkout:{status:'PENDING',amount:8000,checkout_url:'https://sandbox-checkout.saspay.me/example'}};
it('recherche toutes les pages avec un filtre serveur et dix résultats',()=>{const p=new URLSearchParams(historyPath('  Traoré Sikasso  ','SASPAY_PENDING',2).split('?')[1]);expect(Object.fromEntries(p)).toEqual({q:'Traoré Sikasso',status:'SASPAY_PENDING',page:'2',page_size:'10'})});
it('permet la vérification même après expiration du blocage',()=>{expect(canVerifySasPay(b)).toBe(true);expect(historyLabel(b,Date.parse('2026-11-27T00:00:00Z'))).toContain('à vérifier');expect(renderToStaticMarkup(<VerifySasPay booking={b} onUpdate={()=>{}}/>)).toContain('Vérifier le paiement SasPay')});
it('distingue la confirmation SasPay du billet et masque le paiement local concurrent',()=>{const paid:Booking={...b,sandbox_checkout:{status:'PAID',amount:8000,checkout_url:''}};expect(canVerifySasPay(paid)).toBe(false);expect(historyLabel(paid)).toContain('confirmé (TEST)');const html=renderToStaticMarkup(<PaymentPreview booking={paid} onBack={()=>{}}/>);expect(html).toContain('Paiement Sandbox confirmé par Django');expect(html).not.toContain('Simuler le paiement')});

it('distingue les catégories par trajet et affiche le prix individuel',()=>{
 const trip={id:1,company_id:2,company:'Transport Démo',origin:'Bamako',destination:'Ségou',starts_at:b.created_at,ends_at:b.expires_at,boarding_point:'Gare A',arrival_point:'Gare B',bus_name:'Car 01',price:6000,premium_price:10000,premium_positions:[1],total:16000};
 const booking:Booking={...b,count:2,passenger_names:['Awa Standard','Moussa Premium'],total:32000,trips:[trip,{...trip,id:2,premium_positions:[0]}]};
 const html=renderToStaticMarkup(<BookingPassengerList booking={booking}/>);
 for(const value of ['traveler-category standard','traveler-category premium','Aller : Standard','Retour : Premium','Aller : Premium','Retour : Standard','Awa Standard','Moussa Premium','FCFA'])expect(html).toContain(value);
 expect(html.match(/traveler-passenger-price/g)?.length).toBe(2);
 expect(html).toContain('16');
});

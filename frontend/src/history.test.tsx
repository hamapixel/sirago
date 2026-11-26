import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {historyPath,historyLabel,canVerifySasPay,type Booking} from './booking-api';
import VerifySasPay from './VerifySasPay';
import PaymentPreview from './PaymentPreview';
const b:Booking={id:25,reference:'test',status:'HELD',count:1,passenger_names:['Awa Test'],total:8000,created_at:'2026-11-26T10:32:00Z',expires_at:'2026-11-26T10:47:00Z',trips:[],sandbox_checkout_enabled:true,simulation_enabled:true,sandbox_checkout:{status:'PENDING',amount:8000,checkout_url:'https://sandbox-checkout.saspay.me/example'}};
it('recherche toutes les pages avec un filtre serveur et dix résultats',()=>{const p=new URLSearchParams(historyPath('  Traoré Sikasso  ','SASPAY_PENDING',2).split('?')[1]);expect(Object.fromEntries(p)).toEqual({q:'Traoré Sikasso',status:'SASPAY_PENDING',page:'2',page_size:'10'})});
it('permet la vérification même après expiration du blocage',()=>{expect(canVerifySasPay(b)).toBe(true);expect(historyLabel(b,Date.parse('2026-11-27T00:00:00Z'))).toContain('à vérifier');expect(renderToStaticMarkup(<VerifySasPay booking={b} onUpdate={()=>{}}/>)).toContain('Vérifier le paiement SasPay')});
it('distingue la confirmation SasPay du billet et masque le paiement local concurrent',()=>{const paid:Booking={...b,sandbox_checkout:{status:'PAID',amount:8000,checkout_url:''}};expect(canVerifySasPay(paid)).toBe(false);expect(historyLabel(paid)).toContain('confirmé (TEST)');const html=renderToStaticMarkup(<PaymentPreview booking={paid} onBack={()=>{}}/>);expect(html).toContain('Paiement Sandbox confirmé par Django');expect(html).not.toContain('Simuler le paiement')});

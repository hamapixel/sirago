import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import SandboxCheckoutPanel from './SandboxCheckoutPanel';
import type {Booking} from './booking-api';
const booking:Booking={id:1,reference:'test',count:1,status:'HELD',expires_at:'2026-11-29T06:00:00Z',created_at:'2026-11-26T09:00:00Z',passenger_names:['Awa Test'],total:8000,trips:[]};
it('propose le Checkout Sandbox sans promettre un billet',()=>{const html=renderToStaticMarkup(<SandboxCheckoutPanel booking={booking} expired={false} onUpdate={()=>{}}/>);expect(html).toContain('Payer avec SasPay (TEST)');expect(html).toContain('Aucun débit réel ni billet émis')});
it('refuse un lien LIVE et affiche la confirmation sans billet',()=>{const pending:Booking={...booking,sandbox_checkout:{status:'PENDING',amount:8000,checkout_url:'https://pay.saspay.me/checkout/x'}};const html=renderToStaticMarkup(<SandboxCheckoutPanel booking={pending} expired={false} onUpdate={()=>{}}/>);expect(html).not.toContain('Ouvrir le paiement SasPay');expect(html).toContain('Vérifier le paiement');const paid:Booking={...pending,sandbox_checkout:{status:'PAID',amount:8000,checkout_url:''}};expect(renderToStaticMarkup(<SandboxCheckoutPanel booking={paid} expired={true} onUpdate={()=>{}}/>)).toContain('Paiement Sandbox confirmé par Django')});

it('présente les réseaux comme des exemples et conserve le paiement hébergé',()=>{const html=renderToStaticMarkup(<SandboxCheckoutPanel booking={booking} expired={false} onUpdate={()=>{}}/>);for(const v of ['payment-network orange','payment-network moov','payment-network wave','Exemples de moyens de paiement','réseaux effectivement disponibles','SANDBOX · TEST'])expect(html).toContain(v);expect(html.match(/<button /g)?.length).toBe(1)});

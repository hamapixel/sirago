import {describe,it,expect} from 'vitest';
import {parseSelection,bookingUrl,authUrl,bookingLabel,effectiveBookingStatus} from './booking-api';
describe('Réservation',()=>{
 it('reprend un aller simple après connexion',()=>expect(bookingUrl(parseSelection('?out=12&count=2')!)).toBe('/booking/?out=12&count=2'));
 it('conserve le retour pendant la création du compte',()=>expect(authUrl(true,{out:12,ret:19,count:3})).toBe('/register/?out=12&count=3&ret=19'));
 it('refuse une quantité invalide',()=>expect(parseSelection('?out=1&count=11')).toBeNull());
 it('refuse un retour identique',()=>expect(parseSelection('?out=1&ret=1&count=1')).toBeNull());
 it('ne transmet jamais une URL de redirection externe',()=>expect(authUrl(false,parseSelection('?out=1&count=1&next=https://example.org')!)).toBe('/login/?out=1&count=1'));
 it('distingue réservation expirée et paiement',()=>expect(bookingLabel('EXPIRED')).toBe('Expirée'));
 it('actualise le statut à expiration sans écriture serveur',()=>{const b={status:'HELD' as const,expires_at:'2026-11-26T10:15:00Z'};expect(effectiveBookingStatus(b,Date.parse('2026-11-26T10:14:59Z'))).toBe('HELD');expect(effectiveBookingStatus(b,Date.parse(b.expires_at))).toBe('EXPIRED');expect(effectiveBookingStatus({...b,status:'CANCELLED'},Date.parse(b.expires_at))).toBe('CANCELLED')});
});

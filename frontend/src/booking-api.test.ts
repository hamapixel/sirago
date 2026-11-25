import {describe,it,expect} from 'vitest';
import {parseSelection,bookingUrl,authUrl,bookingLabel,effectiveBookingStatus,validPassengerNames,normalizePassengerName} from './booking-api';
describe('Réservation',()=>{
 it('reprend un aller simple après connexion',()=>expect(bookingUrl(parseSelection('?out=12&count=2')!)).toBe('/booking/?out=12&count=2'));
 it('conserve le retour pendant la création du compte',()=>expect(authUrl(true,{out:12,ret:19,count:3})).toBe('/register/?out=12&count=3&ret=19'));
 it('refuse une quantité invalide',()=>expect(parseSelection('?out=1&count=101')).toBeNull());
 it('refuse un retour identique',()=>expect(parseSelection('?out=1&ret=1&count=1')).toBeNull());
 it('ne transmet jamais une URL de redirection externe',()=>expect(authUrl(false,parseSelection('?out=1&count=1&next=https://example.org')!)).toBe('/login/?out=1&count=1'));
 it('distingue réservation expirée et paiement',()=>expect(bookingLabel('EXPIRED')).toBe('Expirée'));
 it('actualise le statut à expiration sans écriture serveur',()=>{const b={status:'HELD' as const,expires_at:'2026-11-26T10:15:00Z'};expect(effectiveBookingStatus(b,Date.parse('2026-11-26T10:14:59Z'))).toBe('HELD');expect(effectiveBookingStatus(b,Date.parse(b.expires_at))).toBe('EXPIRED');expect(effectiveBookingStatus({...b,status:'CANCELLED'},Date.parse(b.expires_at))).toBe('CANCELLED')});
 it('valide un nom par passager et conserve les doublons',()=>expect(validPassengerNames(['Awa Test','Awa Test'],2)).toBe(true));
 it('refuse les noms incomplets et le mauvais nombre',()=>{expect(validPassengerNames(['Awa Test',''],2)).toBe(false);expect(validPassengerNames(['Awa Test'],2)).toBe(false);expect(validPassengerNames(['123'],1)).toBe(false)});
 it('normalise les espaces sans modifier les accents',()=>expect(normalizePassengerName('  Aïssata   Traoré ')).toBe('Aïssata Traoré'));
});

import {describe,it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import TravelerProfile from './TravelerProfile';
import {initials,validProfileName} from './profile-validation';
import type {Account} from './auth-api';
const a:Account={first_name:'Awa',last_name:'Traoré',phone:'+22370000000',email:'demo@example.com',role:'TRAVELER',company:null};
const render=(account:Account|null)=>renderToStaticMarkup(<TravelerProfile account={account} onUpdated={()=>{}} onTickets={()=>{}} onLogout={async()=>{}}/>);
describe('Profil voyageur',()=>{
 it('affiche les informations et les menus du compte',()=>{const html=render(a);expect(html).toContain('Awa Traoré');expect(html).toContain('Mes réservations');expect(html).toContain('Paramètres');expect(html).toContain('Notifications');expect(html).toContain('Déconnexion')});
 it('n’affiche pas les modules exclus',()=>{expect(render(a)).not.toMatch(/portefeuille|parrainage|code promo/i)});
 it('invite les visiteurs à se connecter',()=>{const html=render(null);expect(html).toContain('Créer mon compte');expect(html).toContain('Se connecter');expect(html).not.toContain('Déconnexion')});
 it('calcule les initiales',()=>{expect(initials(' awa ','Traoré')).toBe('AT');expect(initials('','')).toBe('SG')});
 it('valide les noms',()=>{expect(validProfileName('Aïssata')).toBe(true);expect(validProfileName(' ')).toBe(false);expect(validProfileName('A'.repeat(151))).toBe(false)});
});

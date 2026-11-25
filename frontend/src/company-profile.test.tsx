import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import CompanyProfile from './CompanyProfile';
import type {Account} from './auth-api';
const account:Account={first_name:'Awa',last_name:'Test',phone:null,email:'test@example.com',role:'COMPANY',company:{name:'Transport Test',status:'VERIFIED',city:'Bamako'}};
it('affiche le profil professionnel et distingue les fonctions à venir',()=>{const html=renderToStaticMarkup(<CompanyProfile account={account} onUpdated={()=>{}} onLogout={()=>{}}/>);for(const v of ['Transport Test','Compagnie vérifiée','Informations de la compagnie','Informations du responsable','Sécurité du compte','Agents de la compagnie','Réservations et embarquements','Déconnexion'])expect(html).toContain(v)});

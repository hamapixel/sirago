import {describe,it,expect} from 'vitest';
import {phoneValid,emailValid,passwordValid,passwordChecks} from './auth-validation';
import {destination,type Account} from './auth-api';
describe('Inscription',()=>{
 it('normalise les formats de téléphone maliens',()=>{expect(phoneValid('70 00 00 01')).toBe(true);expect(phoneValid('+22370000001')).toBe(true);expect(phoneValid('123')).toBe(false)});
 it('accepte un email facultatif',()=>{expect(emailValid('')).toBe(true);expect(emailValid('demo@example.com')).toBe(true);expect(emailValid('bad')).toBe(false)});
 it('vérifie les deux mots de passe',()=>{expect(passwordValid('abcdefgh','abcdefgh')).toBe(true);expect(passwordValid('abcdefgh','different')).toBe(false);expect(passwordValid('abc','abc')).toBe(false)});
 it('explique un mot de passe de sept caractères',()=>expect(passwordChecks('Sirago1','Sirago1')).toEqual({length:false,matching:true}));
 it('explique une confirmation différente',()=>expect(passwordChecks('Sirago123','Sirago124')).toEqual({length:true,matching:false}));
 it('ne valide pas deux champs vides',()=>expect(passwordChecks('','')).toEqual({length:false,matching:false}));
 it('refuse une longueur supérieure à 128',()=>expect(passwordValid('a'.repeat(129),'a'.repeat(129))).toBe(false));
 it('redirige selon le rôle serveur',()=>{expect(destination({role:'TRAVELER'} as Account)).toBe('/app/');expect(destination({role:'COMPANY'} as Account)).toBe('/company/');expect(destination({role:'ADMIN'} as Account)).toBe('/admin/')});
});

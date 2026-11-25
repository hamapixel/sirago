import { describe,it,expect } from 'vitest';
import {validSearch} from './search';
describe('recherche',()=>{
const check=(from='Bamako',to='Sikasso',date='2026-12-01',ret='',round=false,count=1)=>validSearch(from,to,date,ret,round,count,'2026-11-25');
it('accepte un aller simple',()=>expect(check()).toBe(true));
it('refuse les villes identiques',()=>expect(check('Bamako','Bamako')).toBe(false));
it('refuse une date passée',()=>expect(check('Bamako','Kayes','2026-01-01')).toBe(false));
it('refuse un retour antérieur',()=>expect(check('Bamako','Kayes','2026-12-01','2026-11-30',true)).toBe(false));
it('refuse une quantité invalide',()=>expect(check('Bamako','Kayes','2026-12-01','',false,0)).toBe(false));
});

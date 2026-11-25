import {describe,it,expect} from 'vitest';
import {tripPath,defaultFilters,durationText,compatible,type Trip} from './travel-api';
const c={origin:'Bamako',destination:'Ségou',date:'2026-11-26',back:'2026-11-28',round:true,count:2};
describe('Recherche réelle',()=>{
 it('encode les villes et passagers',()=>{const p=new URLSearchParams(tripPath(c).split('?')[1]);expect(p.get('destination')).toBe('Ségou');expect(p.get('passengers')).toBe('2')});
 it('inverse le trajet retour',()=>{const p=new URLSearchParams(tripPath(c,defaultFilters,1,true,'2026-11-26T13:00:00Z').split('?')[1]);expect(p.get('origin')).toBe('Ségou');expect(p.get('date')).toBe(c.back);expect(p.get('after')).toBe('2026-11-26T13:00:00Z')});
 it('transmet les filtres et la page',()=>{const p=new URLSearchParams(tripPath(c,{...defaultFilters,company:'Diarra',period:'morning',max_price:'8000'},2).split('?')[1]);expect(p.get('company')).toBe('Diarra');expect(p.get('page')).toBe('2');expect(p.get('max_price')).toBe('8000')});
 it('formate les durées',()=>expect(durationText(425)).toBe('7 h 05 min'));
 it('refuse un retour avant arrivée',()=>expect(compatible({ends_at:'2026-11-26T13:00:00Z'} as Trip,{starts_at:'2026-11-26T12:00:00Z'} as Trip)).toBe(false));
});

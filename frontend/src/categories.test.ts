import {describe,it,expect} from 'vitest';
import {defaultPremiumPositions,categoryTotal,validCategories} from './booking-api';
import {minimumTripTotal,type Trip} from './travel-api';
const t={price:8000,premium_price:12000,standard_remaining:1,premium_remaining:2} as Trip;
describe('Catégories de places',()=>{
 it('propose le minimum selon les disponibilités',()=>{expect(defaultPremiumPositions(t,3)).toEqual([1,2]);expect(minimumTripTotal(t,3)).toBe(32000)});
 it('calcule le total mixte',()=>expect(categoryTotal(t,2,[1])).toBe(20000));
 it('refuse une catégorie épuisée',()=>expect(validCategories(t,2,[])).toBe(false));
 it('accepte une répartition valide',()=>expect(validCategories(t,2,[0])).toBe(true));
 it('refuse les doublons',()=>expect(validCategories(t,2,[0,0])).toBe(false));
});

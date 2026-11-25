import {describe,it,expect} from 'vitest';
import {allowedStatus,departurePath,emptyFilters,selectableDrafts,type Departure} from './company-api';
describe('Départs',()=>{
 it('bloque publication avant validation',()=>expect(allowedStatus('DRAFT',false)).toEqual(['CANCELLED']));
 it('permet publication après validation',()=>expect(allowedStatus('DRAFT',true)).toContain('PUBLISHED'));
 it('interdit la réactivation d’un départ annulé',()=>expect(allowedStatus('CANCELLED',true)).toEqual([]));
 it('permet de suspendre un départ publié',()=>expect(allowedStatus('PUBLISHED',true)).toContain('SUSPENDED'));
 it('conserve les filtres dans la pagination',()=>expect(departurePath(2,{...emptyFilters,status:'DRAFT',route_id:'3'})).toBe('departures/?page=2&route_id=3&status=DRAFT'));
 it('omet les filtres vides',()=>expect(departurePath(1,emptyFilters)).toBe('departures/?page=1'));
 it('sélectionne uniquement les brouillons futurs',()=>{const rows=[{id:1,status:'DRAFT',starts_at:'2027-01-01T06:00:00Z'},{id:2,status:'PUBLISHED',starts_at:'2027-01-01T06:00:00Z'},{id:3,status:'DRAFT',starts_at:'2026-01-01T06:00:00Z'}] as Departure[];expect(selectableDrafts(rows,true,Date.parse('2026-11-25'))).toEqual([1]);expect(selectableDrafts(rows,false,0)).toEqual([])});
});

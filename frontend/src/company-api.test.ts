import {describe,it,expect} from 'vitest';
import {allowedStatus} from './company-api';
describe('Départs',()=>{
 it('bloque publication avant validation',()=>expect(allowedStatus('DRAFT',false)).toEqual(['CANCELLED']));
 it('permet publication après validation',()=>expect(allowedStatus('DRAFT',true)).toContain('PUBLISHED'));
 it('interdit la réactivation d’un départ annulé',()=>expect(allowedStatus('CANCELLED',true)).toEqual([]));
 it('permet de suspendre un départ publié',()=>expect(allowedStatus('PUBLISHED',true)).toContain('SUSPENDED'));
});

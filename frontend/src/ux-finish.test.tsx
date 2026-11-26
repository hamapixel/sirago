import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {CityField} from './CityField';
import {canonicalCity,matchingCities,validSearch} from './search';
import {selectableDepartures,type Departure} from './company-api';
import {tripPath,defaultFilters} from './travel-api';
it('recherche les villes sans accents ni majuscules',()=>{expect(matchingCities('seg')).toContain('Ségou');expect(canonicalCity('SEGOU')).toBe('Ségou');expect(matchingCities('xyz')).toEqual([]);expect(validSearch('Bam','Kayes','2026-11-27','',false,1,'2026-11-26')).toBe(false)});
it('présente un champ de recherche et non un select',()=>{const html=renderToStaticMarkup(<CityField label="Ville de départ" value="" onChange={()=>{}}/>);expect(html).toContain('role="combobox"');expect(html).toContain('Rechercher une ville');expect(html).not.toContain('<select')});
it('sélectionne les départs futurs selon l’action groupée',()=>{const rows=[{id:1,status:'DRAFT',starts_at:'2026-11-27T06:00:00Z'},{id:2,status:'SUSPENDED',starts_at:'2026-11-27T06:00:00Z'},{id:3,status:'PUBLISHED',starts_at:'2026-11-27T06:00:00Z'},{id:4,status:'CANCELLED',starts_at:'2026-11-27T06:00:00Z'},{id:5,status:'SUSPENDED',starts_at:'2026-11-25T06:00:00Z'}] as Departure[];const now=Date.parse('2026-11-26');expect(selectableDepartures(rows,true,'PUBLISHED',now)).toEqual([1,2]);expect(selectableDepartures(rows,true,'SUSPENDED',now)).toEqual([3]);expect(selectableDepartures(rows,false,'PUBLISHED',now)).toEqual([])});
it('filtre les résultats par identifiant de compagnie',()=>{const url=tripPath({origin:'Bamako',destination:'Sikasso',date:'2026-11-27',back:'',round:false,count:1},{...defaultFilters,company_id:'42'});expect(url).toContain('company_id=42')});

it('ne propose rien sans saisie et reconnaît les nouvelles localités',()=>{expect(matchingCities('   ')).toEqual([]);expect(matchingCities('gao')).toContain('Gao');expect(canonicalCity('KATI')).toBe('Kati');expect(matchingCities('kalaban')).toContain('Kalabancoro')});

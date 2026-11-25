import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {matchesSearch,Pagination} from './listing';
it('recherche instantanée locale multi-mots sans distinction de casse ou accents',()=>{expect(matchesSearch('segou  premium','Ségou','Premium')).toBe(true);expect(matchesSearch('Mopti','Bamako','Sikasso')).toBe(false)});
it('affiche le compteur et les bornes de pagination',()=>{const html=renderToStaticMarkup(<Pagination page={2} size={10} total={13} onChange={()=>{}}/>);expect(html).toContain('11–13 sur 13');expect(html).toContain('Page 2/2');expect(html).toContain('disabled')});

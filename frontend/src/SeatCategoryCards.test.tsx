import {describe,it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import SeatCategoryCards from './SeatCategoryCards';

const render=(premium=false, premiumPrice=12000, remaining=10)=>renderToStaticMarkup(<SeatCategoryCards trip={{price:8000,premium_price:premiumPrice,standard_remaining:50,premium_remaining:remaining}} premium={premium} disabled={false} label="Passager 1" onChange={()=>{}}/>);

describe('Cartes de catégorie',()=>{
 it('affiche deux boutons et non une liste déroulante',()=>{const html=render();expect(html.match(/<button/g)).toHaveLength(2);expect(html).toContain('Standard');expect(html).toContain('Premium');expect(html).not.toContain('<select')});
 it('signale la catégorie sélectionnée',()=>{expect(render(true)).toContain('seat-category-card premium selected');expect(render()).toContain('seat-category-card standard selected')});
 it('masque Premium si non proposé',()=>{const html=render(false,0,0);expect(html.match(/<button/g)).toHaveLength(1);expect(html).not.toContain('Premium')});
 it('désactive Premium si complet',()=>{const html=render(false,12000,0);expect(html).toMatch(/<button[^>]*aria-label="Premium[^"]*Complet"[^>]*disabled/);expect(html).toContain('Complet')});
});

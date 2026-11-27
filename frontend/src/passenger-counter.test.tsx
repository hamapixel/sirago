import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {PassengerCounter,parsePassengerInput} from './PassengerCounter';
it('permet la saisie numérique sans liste déroulante et garde les boutons',()=>{const html=renderToStaticMarkup(<PassengerCounter count={12} onChange={()=>{}}/>);expect(html).toContain('inputMode="numeric"');expect(html).toContain('value="12"');expect(html).toContain('Retirer un passager');expect(html).toContain('Ajouter un passager');expect(html).not.toContain('<select')});
it('limite les saisies entières de 1 à 100 et refuse les caractères invalides',()=>{expect(parsePassengerInput('15')).toBe(15);expect(parsePassengerInput('0')).toBe(1);expect(parsePassengerInput('101')).toBe(100);for(const input of ['', '-1','1.5','1e2','abc'])expect(parsePassengerInput(input)).toBeNull()});
it('désactive le bouton de diminution à un passager',()=>{const html=renderToStaticMarkup(<PassengerCounter count={1} onChange={()=>{}}/>);expect(html).toMatch(/<button[^>]*disabled[^>]*aria-label="Retirer un passager"/)});

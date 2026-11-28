import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {HomeJourney,HomeServices} from './HomeJourney';
it('présente quatre étapes originales avec un vrai bouton de recherche',()=>{const html=renderToStaticMarkup(<HomeJourney onSearch={()=>{}}/>);for(const s of ['Tracez votre itinéraire','Comparez les départs','Préparez votre réservation','Gardez votre billet à portée de main','Trouvez votre voyage'])expect(html).toContain(s);expect(html.match(/<li>/g)?.length).toBe(4);expect(html).toContain('<button type="button"')});
it('rend les quatre services accessibles par bouton et signale le paiement de test',()=>{const html=renderToStaticMarkup(<HomeServices onSearch={()=>{}} onTickets={()=>{}} onSupport={()=>{}}/>);expect(html.match(/<button /g)?.length).toBe(4);for(const s of ['Paiement SasPay','Simulation','Billet numérique','Report de voyage','Assistance','aria-expanded="false"'])expect(html).toContain(s);expect(html).not.toContain('24/7')});

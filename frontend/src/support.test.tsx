import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import SupportCenter,{SupportCard,type SupportRequest} from './SupportCenter';
const t:SupportRequest={id:1,reference:'SG-TEST',category:'BOOKING',subject:'Billet absent',message:'Je ne trouve pas mon billet.',status:'RESOLVED',reply:'Votre billet est disponible.',created_at:'2026-11-25T12:00:00Z',updated_at:'2026-11-25T13:00:00Z'};
it('affiche le suivi et la réponse du support',()=>{const html=renderToStaticMarkup(<SupportCard item={t}/>);for(const v of ['SG-TEST','Résolue','Réponse BTDIGIT','Votre billet est disponible.'])expect(html).toContain(v)});
it('propose une FAQ publique sans envoi anonyme',()=>{const html=renderToStaticMarkup(<SupportCenter signedIn={false}/>);expect(html).toContain('Questions fréquentes');expect(html).toContain('Se connecter');expect(html).not.toContain('Nouvelle demande')});
it('propose les demandes et leur recherche pour un compte connecté',()=>{const html=renderToStaticMarkup(<SupportCenter/>);expect(html).toContain('Nouvelle demande');expect(html).toContain('Mes demandes');expect(html).toContain('Sujet ou référence')});

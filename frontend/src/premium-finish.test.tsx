import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {Donut} from './PremiumMetrics';
import {ReservationCard} from './CompanyReservations';
import {translateText,LanguageSelect} from './i18n';
it('calcule les parts à partir des données et rend les zéros lisibles',()=>{const html=renderToStaticMarkup(<Donut title="Places" items={[{label:'Libres',value:4},{label:'Occupées',value:6}]} center="places"/>);expect(html).toContain('stroke-dasharray="40 60"');expect(html).toContain('stroke-dasharray="60 40"');expect(renderToStaticMarkup(<Donut title="Places" items={[{label:'Libres',value:0}]} center="places"/>)).toContain('Aucune donnée')});
it('affiche le statut, le trajet et le montant séparément',()=>{const html=renderToStaticMarkup(<ReservationCard row={{id:1,reference:'REF',origin:'Bamako',destination:'Mopti',starts_at:'2026-11-27T06:00:00Z',expires_at:'2026-11-27T05:00:00Z',count:2,premium_count:0,total:16000,status:'TEST_PAID'}}/>);for(const value of ['Bamako','Mopti','Paiement simulé','FCFA','REF','2 passager(s)'])expect(html).toContain(value)});
it('propose les trois langues et conserve les libellés inconnus',()=>{expect(translateText('Accueil','en')).toBe('Home');expect(translateText('Accueil','bm')).toBe('So');expect(translateText('Bamako','bm')).toBe('Bamako');const html=renderToStaticMarkup(<LanguageSelect/>);for(const value of ['Français','English','Bamanankan'])expect(html).toContain(value)});

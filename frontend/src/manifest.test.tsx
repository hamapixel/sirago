import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {ManifestSummary,type ManifestData} from './CompanyManifest';
it('sépare les simulations, recettes et paiements en attente',()=>{const data={capacity:10,reserved:4,standard:3,premium:1,pending:1,simulated:3,boarded:2,waiting:1,absent:0,remaining:6,real_amount:0,simulated_amount:28000,pending_amount:8000} as ManifestData;const html=renderToStaticMarkup(<ManifestSummary data={data}/>);for(const v of ['Recettes réelles','Montants simulés (TEST)','Paiements en attente','Embarqués TEST','Absents TEST','Places libres','0 FCFA'])expect(html).toContain(v)});

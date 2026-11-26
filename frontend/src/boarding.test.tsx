import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {BoardingResult,validTicketCode,type BoardingTicket} from './CompanyBoarding';
const t:BoardingTicket={code:'SRG-TEST-'+'A'.repeat(32),origin:'Bamako',destination:'Mopti',starts_at:'2026-11-27T06:00:00Z',boarding_point:'Gare',category:'Standard',count:2,boarded:1,remaining:1,can_board:true,passengers:[{index:0,name:'Awa Test',boarded_at:'2026-11-27T05:00:00Z'},{index:1,name:'Baba Test',boarded_at:null}]};
it('accepte seulement une référence TEST',()=>{expect(validTicketCode(t.code)).toBe(true);expect(validTicketCode('https://example.org')).toBe(false)});
it('montre la validation par passager et les embarquements existants',()=>{const html=renderToStaticMarkup(<BoardingResult ticket={t} selected={[1]} onToggle={()=>{}} onAll={()=>{}} onValidate={()=>{}} busy={false}/>);for(const v of ['Awa Test','Baba Test','Déjà embarqué','Embarqués','Restants','1/1'])expect(html).toContain(v);expect(html).toContain('disabled')});

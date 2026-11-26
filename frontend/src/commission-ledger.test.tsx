import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {LedgerSummary,LedgerLine} from './CommissionLedger';
const line={id:1,company:'Diarra Transport',reference:'test-ref',route:'Bamako → Sikasso',issued_at:'2026-11-26T12:00:00Z',gross:24000,rate_bps:500,commission:1200,company_share:22800};
it('sépare les montants de test',()=>{const html=renderToStaticMarkup(<LedgerSummary summary={{gross:24000,commission:1200,company_share:22800,unconfigured:0,unconfigured_count:0}}/>);for(const s of ['Billets TEST','BTDIGIT TEST','Part compagnies TEST','Sans taux'])expect(html).toContain(s)});
it('distingue un taux figé, zéro et non configuré',()=>{expect(renderToStaticMarkup(<LedgerLine line={line}/>)).toContain('5 %');expect(renderToStaticMarkup(<LedgerLine line={{...line,rate_bps:0,commission:0,company_share:24000}}/>)).toContain('0 %');expect(renderToStaticMarkup(<LedgerLine line={{...line,rate_bps:null,commission:null,company_share:null}}/>)).toContain('Taux non configuré')});

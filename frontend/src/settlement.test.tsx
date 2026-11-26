import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {SettlementMetrics,SettlementCard,SettlementReceipt,CompanySettlements} from './SettlementSpace';
const balance={id:1,name:'Diarra Transport',city:'Bamako',status:'VERIFIED',gross:8000,commission:400,share:7600,settled:1000,remaining:6600};
it('sépare les montants TEST',()=>{const html=renderToStaticMarkup(<SettlementMetrics totals={balance}/>);for(const v of ['À reverser TEST','Commission TEST','Reversé TEST','Part compagnie TEST'])expect(html).toContain(v)});
it('désactive la préparation sans solde ou hors Sandbox',()=>{expect(renderToStaticMarkup(<SettlementCard balance={balance} enabled onSaved={()=>{}}/>)).not.toContain('disabled');expect(renderToStaticMarkup(<SettlementCard balance={{...balance,remaining:0}} enabled onSaved={()=>{}}/>)).toContain('disabled');expect(renderToStaticMarkup(<SettlementCard balance={balance} enabled={false} onSaved={()=>{}}/>)).toContain('disabled')});
it('propose un justificatif TEST et une consultation compagnie',()=>{expect(renderToStaticMarkup(<SettlementReceipt receipt={{id:1,company:'Diarra Transport',reference:'test',amount:1000,created_at:'2026-11-26T12:00:00Z'}}/>)).toContain('/api/v1/auth/settlements/1/pdf/');expect(renderToStaticMarkup(<CompanySettlements revision={0}/>)).toContain('Reversements TEST')});

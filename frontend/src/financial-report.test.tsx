import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import FinancialReport,{FinancialMetrics,FinancialRow,financialDates} from './FinancialReport';
it('calcule les périodes en dates civiles',()=>{expect(financialDates('today','2026-11-26')).toEqual({from:'2026-11-26',to:'2026-11-26'});expect(financialDates('week','2026-11-26')).toEqual({from:'2026-11-23',to:'2026-11-29'});expect(financialDates('month','2026-02-10')).toEqual({from:'2026-02-01',to:'2026-02-28'})});
it('sépare les montants et les recettes réelles',()=>{const html=renderToStaticMarkup(<FinancialMetrics summary={{sandbox:16000,local:3000,commission:800,share:15200,settled:5000,unallocated:0,real:0}}/>);for(const text of ['SasPay TEST','BTDIGIT TEST','Simulation locale','Recettes réelles','Non réparti TEST'])expect(html).toContain(text)});
it('affiche les filtres, les deux exports et les historiques',()=>{const html=renderToStaticMarkup(<FinancialReport revision={0}/>);for(const text of ['Aujourd’hui','Semaine','Mois','Période','PDF','Excel','Commissions','Reversements','Compagnie ou ville'])expect(html).toContain(text)});
it('affiche les taux non configurés sans inventer de commission',()=>{const html=renderToStaticMarkup(<FinancialRow row={{id:1,name:'Transport',gross:8000,rate_bps:null}} view="commissions" rank={1}/>);expect(html).toContain('Taux non configuré')});

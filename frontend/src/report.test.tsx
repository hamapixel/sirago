import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {ReportAmounts,type ReportOption} from './TicketReport';
import {bookingLabel} from './booking-api';
it('affiche le supplément uniquement en mode simulé',()=>{const html=renderToStaticMarkup(<ReportAmounts previous={16000} option={{total:18000,difference:2000} as ReportOption}/>);expect(html).toContain('Supplément simulé');expect(html).toContain('Aucun argent');expect(bookingLabel('REPORTED')).toBe('Reportée')});
it('affiche un tarif inférieur sans promettre de remboursement réel',()=>{const html=renderToStaticMarkup(<ReportAmounts previous={16000} option={{total:14000,difference:-2000} as ReportOption}/>);expect(html).toContain('de moins');expect(html).toContain('Aucun argent ne sera débité ou remboursé')});

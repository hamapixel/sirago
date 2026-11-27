import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {ReservationCard} from './CompanyReservations';
import {ReservationDetailContent,type ReservationDetailData} from './CompanyReservationDetail';
const data:ReservationDetailData={id:1,reference:'REF-DEMO',company:'Transport Démo',status:'TEST_PAID',departure_status:'PUBLISHED',created_at:'2026-11-26T08:00:00Z',expires_at:'2026-11-26T08:15:00Z',position:0,origin:'Bamako',destination:'Sikasso',boarding_point:'Gare A',arrival_point:'Gare B',starts_at:'2026-11-27T06:00:00Z',ends_at:'2026-11-27T13:00:00Z',bus_name:'Car 01',plate:'AA 001',ticket_mode:'group',payment_method:'LOCAL_SIMULATION',count:2,premium_count:1,boarded_count:1,total:20000,simulated_amount:20000,real_amount:0,passengers:[{index:0,name:'Awa Démo',category:'Standard',state:'BOARDED',boarded_at:'2026-11-27T05:50:00Z',amount:8000},{index:1,name:'Moussa Démo',category:'Premium',state:'WAITING',boarded_at:null,amount:12000}]};
it('affiche un bouton accessible pour ouvrir la réservation',()=>{const html=renderToStaticMarkup(<ReservationCard row={{id:1,reference:'REF',origin:'Bamako',destination:'Sikasso',starts_at:data.starts_at,expires_at:data.expires_at,count:2,premium_count:1,total:20000,status:'TEST_PAID'}} onDetails={()=>{}}/>);expect(html).toContain('Voir les détails');expect(html).toContain('reservation-details-button');expect(html).toContain('aria-label=')});
it('présente les noms, catégories, horaires et validation simulée',()=>{const html=renderToStaticMarkup(<ReservationDetailContent data={data}/>);for(const s of ['Awa Démo','Moussa Démo','Standard','Premium','Embarqué (simulation)','Non embarqué','Gare A','Gare B','Billets collectifs','FCFA','Aucun encaissement ni embarquement réel.'])expect(html).toContain(s)});
it('ne rend aucun montant si les données financières sont absentes',()=>{const html=renderToStaticMarkup(<ReservationDetailContent data={{...data,total:undefined,simulated_amount:undefined,real_amount:undefined,passengers:data.passengers.map(({amount,...p})=>p)}}/>);expect(html).toContain('Awa Démo');expect(html).not.toContain('FCFA');expect(html).not.toContain('Montant du trajet')});

it('échappe le HTML injecté dans les noms des passagers et de la compagnie',()=>{
 const marker='<img src=x onerror="void(0)">';
 const html=renderToStaticMarkup(<ReservationDetailContent data={{...data,company:marker,passengers:data.passengers.map(p=>({...p,name:marker}))}}/>);
 expect(html).toContain('&lt;img src=x onerror=&quot;void(0)&quot;&gt;');
 expect(html).not.toContain(marker);
 expect(html).not.toMatch(/<img[^>]+onerror\s*=/i);
});

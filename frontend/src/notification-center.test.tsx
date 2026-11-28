import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {NotificationItem} from './NotificationCenter';
const item={id:1,kind:'TEST_PAYMENT',title:'Billets de test disponibles',message:'Aucun argent débité.',created_at:'2026-11-25T12:00:00Z',read_at:null};
it('distingue une notification non lue et une notification lue',()=>{const unread=renderToStaticMarkup(<NotificationItem item={item} onRead={()=>{}} busy={false}/>);expect(unread).toContain('Marquer comme lu');expect(unread).toContain('Aucun argent débité.');const read=renderToStaticMarkup(<NotificationItem item={{...item,read_at:item.created_at}} onRead={()=>{}} busy={false}/>);expect(read).not.toContain('Marquer comme lu');expect(read).toContain('> Lu')});

it('propose un détail accessible pour chaque notification',()=>{const html=renderToStaticMarkup(<NotificationItem item={item} onRead={()=>{}} busy={false}/>);expect(html).toContain('Voir le détail');expect(html).toContain('aria-expanded="false"');expect(html).toContain('aria-controls="notice-detail-1"')});

it('ouvre la réservation exacte depuis la notification et propose ses PDF',()=>{
 const html=renderToStaticMarkup(<NotificationItem item={{...item,booking_id:42}} onRead={()=>{}} busy={false}/>);
 expect(html).toContain('/app/?view=tickets&amp;booking=42');
 expect(html).toContain('Télécharger les billets');
 expect(html).toContain('notice-tickets-1');
});
it('ne propose pas de PDF ciblé pour une ancienne notification sans référence',()=>{
 const html=renderToStaticMarkup(<NotificationItem item={item} onRead={()=>{}} busy={false}/>);
 expect(html).toContain('/app/?view=tickets');
 expect(html).not.toContain('Télécharger les billets');
});
it('ne propose pas de lien de billet pour une notification sans paiement',()=>{
 const html=renderToStaticMarkup(<NotificationItem item={{...item,kind:'CANCELLED',booking_id:42}} onRead={()=>{}} busy={false}/>);
 expect(html).not.toContain('Voir mes billets');
 expect(html).not.toContain('Télécharger les billets');
});

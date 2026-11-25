import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {NotificationItem} from './NotificationCenter';
const item={id:1,kind:'TEST_PAYMENT',title:'Billets de test disponibles',message:'Aucun argent débité.',created_at:'2026-11-25T12:00:00Z',read_at:null};
it('distingue une notification non lue et une notification lue',()=>{const unread=renderToStaticMarkup(<NotificationItem item={item} onRead={()=>{}} busy={false}/>);expect(unread).toContain('Marquer comme lu');expect(unread).toContain('Aucun argent débité.');const read=renderToStaticMarkup(<NotificationItem item={{...item,read_at:item.created_at}} onRead={()=>{}} busy={false}/>);expect(read).not.toContain('Marquer comme lu');expect(read).toContain('> Lu')});

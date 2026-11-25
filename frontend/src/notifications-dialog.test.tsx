import {describe,it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {readFileSync} from 'node:fs';
import NotificationsDialog from './NotificationsDialog';

describe('Fenêtre des notifications',()=>{
 it('affiche une fenêtre accessible avec le logo et les actions de fermeture',()=>{
  const html=renderToStaticMarkup(<NotificationsDialog onClose={()=>{}}/>);
  expect(html).toContain('<dialog');expect(html).toContain('aria-labelledby="notification-dialog-title"');expect(html).toContain('src="/logo.svg"');expect(html).toContain('Fermer les notifications');expect(html).toContain('Compris');
 });
 it('indique que les notifications ne sont pas encore disponibles',()=>{
  const html=renderToStaticMarkup(<NotificationsDialog onClose={()=>{}}/>);
  expect(html).toContain('Bientôt disponible');expect(html).toContain('prochainement');
 });
 it('relie la cloche à la fenêtre sans alerte navigateur',()=>{
  const app=readFileSync('src/App.tsx','utf8');
  expect(app).toContain('aria-haspopup="dialog"');expect(app).toContain('<NotificationsDialog');expect(app).not.toMatch(/\balert\s*\(/);
 });
});

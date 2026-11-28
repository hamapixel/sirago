import {describe,it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {readFileSync} from 'node:fs';
import NotificationsDialog from './NotificationsDialog';

describe('Fenêtre des notifications',()=>{
 it('affiche une fenêtre accessible avec le logo et les actions de fermeture',()=>{
  const html=renderToStaticMarkup(<NotificationsDialog onClose={()=>{}}/>);
  expect(html).toContain('<dialog');expect(html).toContain('aria-labelledby="notification-dialog-title"');expect(html).toContain('src="/logo.svg"');expect(html).toContain('Fermer les notifications');expect(html).toContain('Fermer');
 });
 it('sépare le header permanent du contenu défilant et garde les filtres accessibles',()=>{
  const html=renderToStaticMarkup(<NotificationsDialog onClose={()=>{}} signedIn/>);
  expect(html).toContain('<header class="notification-fixed-header"');
  expect(html).toContain('class="notification-scroll-body"');
  expect(html.indexOf('Fermer les notifications')).toBeLessThan(html.indexOf('notification-scroll-body'));
  expect(html).toContain('<details class="notice-device-settings"');
  expect(html).toContain('>Lues</button>');
  expect(html).toContain('Billets disponibles');
  const css=readFileSync('src/notifications-dialog.css','utf8');
  expect(css).toContain('.notification-scroll-body{flex:1 1 auto;min-height:0;overflow:auto');
  expect(css).toContain('.notice-compact .notice-filter-area{position:sticky');
 });
 it('invite les visiteurs à se connecter',()=>{
  const html=renderToStaticMarkup(<NotificationsDialog onClose={()=>{}}/>);
  expect(html).toContain('Connectez-vous');expect(html).toContain('Se connecter');
 });
 it('relie la cloche à la fenêtre sans alerte navigateur',()=>{
  const app=readFileSync('src/App.tsx','utf8');
  expect(app).toContain('aria-haspopup="dialog"');expect(app).toContain('<NotificationsDialog');expect(app).not.toMatch(/\balert\s*\(/);
 });
});

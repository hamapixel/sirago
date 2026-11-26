import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {readFileSync} from 'node:fs';
import PushPreferences,{vapidBytes} from './PushPreferences';
it('rend un réglage explicite sans demander de permission au rendu',()=>{expect(renderToStaticMarkup(<PushPreferences/>)).toContain('Notifications sur cet appareil')});
it('convertit une clé publique et rejette les clés de longueur invalide',()=>{const key=Buffer.alloc(65);key[0]=4;expect(vapidBytes(key.toString('base64url')).length).toBe(65);expect(()=>vapidBytes('AA')).toThrow()});
it('conserve un message externe générique et une navigation limitée aux trois espaces',()=>{const sw=readFileSync('public/push-events.js','utf8');expect(sw).toContain('showNotification');expect(sw).toContain('notificationclick');expect(sw).toContain('/superadmin/');expect(sw).not.toContain('payload.message');expect(readFileSync('vite.config.ts','utf8')).toContain("importScripts:['/push-events.js']")});

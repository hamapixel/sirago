import {describe,it,expect,vi,afterEach} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {readFileSync} from 'node:fs';
import SplashScreen from './SplashScreen';
import {currentAccount} from './auth-api';

afterEach(()=>{vi.unstubAllGlobals();vi.useRealTimers()});
describe('Démarrage SiraGo',()=>{
 it('affiche le logo et le statut de chargement avant React',()=>{
  const html=readFileSync('index.html','utf8');
  expect(html).toContain('<div id="root"><main class="sirago-splash"');
  expect(html).toContain('sirago-splash-logo');
  expect(html).toContain('role="status">Chargement…');
  expect(html).toContain('prefers-reduced-motion:reduce');
  expect(html.indexOf('sirago-splash-content')).toBeLessThan(html.indexOf('src="/src/main.tsx"'));
 });
 it('conserve la marque pendant la vérification de session',()=>{
  const html=renderToStaticMarkup(<SplashScreen/>);
  expect(html).toContain('src="/logo.svg"');expect(html).toContain('role="status">Chargement…');expect(html).toContain('Propulsé par BTDIGIT');
 });
 it('annonce une redirection',()=>expect(renderToStaticMarkup(<SplashScreen message="Redirection…"/>)).toContain('role="status">Redirection…'));
 it('laisse passer un visiteur non connecté sans délai ajouté',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({status:401,ok:false}));
  await expect(currentAccount()).resolves.toBeNull();
 });
 it('interrompt une vérification de session bloquée après 10 secondes',async()=>{
  vi.useFakeTimers();
  vi.stubGlobal('fetch',vi.fn((_url:string,options:RequestInit)=>new Promise((_resolve,reject)=>options.signal!.addEventListener('abort',()=>reject(new Error('aborted')),{once:true}))));
  const pending=expect(currentAccount()).rejects.toThrow('aborted');
  await vi.advanceTimersByTimeAsync(10000);
  await pending;
 });
});

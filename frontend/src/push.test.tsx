import {it,expect} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import PushPreferences,{vapidBytes} from './PushPreferences';
it('rend un réglage explicite sans demander de permission au rendu',()=>{expect(renderToStaticMarkup(<PushPreferences/>)).toContain('Notifications sur cet appareil')});
it('convertit une clé publique et rejette les clés de longueur invalide',()=>{const key=Buffer.alloc(65);key[0]=4;expect(vapidBytes(key.toString('base64url')).length).toBe(65);expect(()=>vapidBytes('AA')).toThrow()});
it('conserve un message externe générique et une navigation limitée aux trois espaces',()=>{const sw=readFileSync('public/push-events.js','utf8');expect(sw).toContain('showNotification');expect(sw).toContain('notificationclick');expect(sw).toContain('/superadmin/');expect(sw).not.toContain('payload.message');expect(readFileSync('vite.config.ts','utf8')).toContain("importScripts:['/push-events.js']")});

it('affiche le type de notification, distingue le contrôle compagnie et ne divulgue aucun message privé',async()=>{
 const handlers:Record<string,(event:any)=>void>={};
 const seen:{title:string;body:string;icon:string;tag:string}[]=[];
 const self={addEventListener:(name:string,fn:(event:any)=>void)=>{handlers[name]=fn},registration:{showNotification:async(title:string,options:any)=>{seen.push({title,...options})}},clients:{matchAll:async()=>[]}};
 runInNewContext(readFileSync('public/push-events.js','utf8'),{self});
 async function push(kind:string,path:string){
  let result:Promise<unknown>=Promise.resolve();
  handlers.push({data:{json:()=>({kind,path,id:7,message:'SECRET'})},waitUntil:(p:Promise<unknown>)=>{result=p}});
  await result;
  return seen[seen.length-1];
 }
 const booking=await push('RESERVATION','/app/');
 expect(booking.title).toContain('🎫 Réservation enregistrée');
 expect(booking.icon).toBe('/icons/icon-192.png');
 const traveler=await push('TEST_BOARDING','/app/');
 expect(traveler.title).toContain('Embarquement enregistré · Simulation');
 expect(traveler.body).not.toContain('SECRET');
 expect(traveler.tag).toBe('sirago-7');
 const company=await push('TEST_BOARDING','/company/');
 expect(company.title).toContain('Contrôle de billet · Simulation');
 expect((await push('UNKNOWN','/app/')).body).toContain('nouvelle notification');
});

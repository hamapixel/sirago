/* Imported by Workbox's existing service worker; never cache API responses. */
self.addEventListener('push', event => {
 let payload={};
 try{payload=event.data?event.data.json():{}}catch{}
 const path=['/app/','/company/','/superadmin/'].includes(payload.path)?payload.path:'/app/';
 const id=Number.isSafeInteger(payload.id)?payload.id:0;
 event.waitUntil(Promise.all([
  self.registration.showNotification('SiraGo', {
   body:'Vous avez une nouvelle notification. Ouvrez SiraGo pour la consulter.',
   icon:'/icons/icon-192.png',badge:'/icons/icon-192.png',tag:'sirago-'+id,
   data:{path},renotify:false
  }),
  self.clients.matchAll({type:'window',includeUncontrolled:true}).then(clients=>clients.forEach(client=>client.postMessage({type:'SIRAGO_PUSH_RECEIVED'})))
 ]));
});
self.addEventListener('notificationclick',event=>{
 event.notification.close();
 const path=['/app/','/company/','/superadmin/'].includes(event.notification.data?.path)?event.notification.data.path:'/app/';
 event.waitUntil((async()=>{
  const windows=await self.clients.matchAll({type:'window',includeUncontrolled:true});
  for(const client of windows){
   const url=new URL(client.url);
   if(url.origin===self.location.origin&&url.pathname===path){
    await client.focus();client.postMessage({type:'SIRAGO_OPEN_NOTIFICATIONS'});return;
   }
  }
  await self.clients.openWindow(path+'?notifications=1');
 })());
});

/* Imported by Workbox's existing service worker; never cache API responses. */
// Fixed copy per event, not arbitrary server text. Keep simulation explicit.
function notificationCopy(kind,path){
 const company=path==='/company/';
 switch(kind){
  case 'RESERVATION':return ['🎫 Réservation enregistrée','Votre demande de réservation est enregistrée. Consultez SiraGo pour finaliser votre réservation.'];
  case 'CANCELLED':return ['ℹ️ Réservation annulée','Une réservation a été annulée. Consultez SiraGo.'];
  case 'DEPARTURE':return ['🚌 Information de départ','Un départ a été mis à jour. Consultez les détails dans SiraGo.'];
  case 'TEST_PAYMENT':return ['🎫 Billet disponible · Simulation','Votre billet de test est disponible. Aucun débit réel.'];
  case 'TEST_BOOKING':return ['🎫 Nouvelle réservation · Simulation','Une réservation simulée est disponible dans votre espace compagnie.'];
  case 'TEST_BOARDING':return company
   ?['✅ Contrôle de billet · Simulation','Un contrôle de billet a été validé en simulation.']
   :['✅ Embarquement enregistré · Simulation','Votre embarquement de test a été validé. Consultez SiraGo.'];
  case 'TEST_REPORT':return ['📅 Report de voyage · Simulation','Un report de voyage a été enregistré en simulation.'];
  case 'COMPANY_REVIEW':return ['🏢 Compagnie à vérifier','Une inscription de compagnie attend votre vérification.'];
  case 'SUPPORT_NEW':return ['💬 Nouvelle demande d’assistance','Une demande est disponible dans votre espace assistance.'];
  case 'SUPPORT':return ['💬 Assistance SiraGo','Votre demande d’assistance a été mise à jour.'];
  default:return ['SiraGo','Vous avez une nouvelle notification. Ouvrez SiraGo pour la consulter.'];
 }
}
self.addEventListener('push', event => {
 let payload={};
 try{payload=event.data?event.data.json():{}}catch{}
 if(!payload||typeof payload!=='object')payload={};
 const path=['/app/','/company/','/superadmin/'].includes(payload.path)?payload.path:'/app/';
 const id=Number.isSafeInteger(payload.id)?payload.id:0;
 const [title,body]=notificationCopy(payload.kind,path);
 event.waitUntil(Promise.all([
  self.registration.showNotification('SiraGo · '+title, {
   body,
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

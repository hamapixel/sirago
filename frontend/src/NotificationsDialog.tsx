import {useEffect,useRef} from 'react';
import {X} from 'lucide-react';
import NotificationCenter from './NotificationCenter';
import './notifications-dialog.css';

export default function NotificationsDialog({onClose,signedIn=false}:{onClose:()=>void;signedIn?:boolean}){
 const ref=useRef<HTMLDialogElement>(null);
 useEffect(()=>{
  const dialog=ref.current;
  const previous=document.activeElement instanceof HTMLElement?document.activeElement:null;
  const overflow=document.body.style.overflow;
  if(dialog&&!dialog.open)dialog.showModal();
  document.body.style.overflow='hidden';
  return ()=>{
   if(dialog?.open)dialog.close();
   document.body.style.overflow=overflow;
   if(previous?.isConnected)previous.focus({preventScroll:true});
  };
 },[]);
 return <dialog ref={ref} className="sirago-notifications-dialog" aria-labelledby="notification-dialog-title" aria-describedby="notification-dialog-description" onCancel={e=>{e.preventDefault();onClose()}} onClick={e=>{if(e.target===e.currentTarget){const r=e.currentTarget.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)onClose()}}}>
  <header className="notification-fixed-header">
  <div className="notification-sheet-handle" aria-hidden="true"/>
  <div className="notification-dialog-top"><div className="notification-heading-brand" style={{display:"flex",alignItems:"center"}}><img src="/logo.svg" width={32} height={32} alt=""/><div className="notification-heading-copy"><h2 id="notification-dialog-title">Notifications</h2><span id="notification-dialog-description">Vos alertes SiraGo</span></div></div><button type="button" className="notification-close" aria-label="Fermer les notifications" onClick={onClose}><X size={21}/></button></div>
  </header>
  <div className="notification-scroll-body">
   <NotificationCenter signedIn={signedIn} compact/>
  </div>
 </dialog>
}

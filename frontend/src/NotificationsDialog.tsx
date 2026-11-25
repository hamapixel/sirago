import {useEffect,useRef} from 'react';
import {Bell, X, Clock3} from 'lucide-react';
import './notifications-dialog.css';

export default function NotificationsDialog({onClose}:{onClose:()=>void}){
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
  <div className="notification-sheet-handle" aria-hidden="true"/>
  <div className="notification-dialog-top"><span><img src="/logo.svg" width={28} height={28} alt=""/> SiraGo</span><button type="button" className="notification-close" aria-label="Fermer les notifications" onClick={onClose}><X size={21}/></button></div>
  <div className="notification-illustration" aria-hidden="true"><Bell size={34} strokeWidth={1.8}/><span><Clock3 size={14}/></span></div>
  <h2 id="notification-dialog-title">Notifications</h2>
  <p className="notification-soon"><Clock3 size={15} aria-hidden="true"/> Bientôt disponible</p>
  <p id="notification-dialog-description">Vos alertes de voyage et messages SiraGo seront disponibles prochainement.</p>
  <button type="button" className="primary notification-dismiss" autoFocus onClick={onClose}>Compris</button>
 </dialog>
}

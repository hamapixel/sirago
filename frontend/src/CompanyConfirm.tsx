import {useEffect,useRef} from 'react';
import {AlertTriangle,ShieldCheck,X} from 'lucide-react';
export type Confirmation={title:string;message:string;label:string;danger?:boolean;run:()=>Promise<void>};
export default function CompanyConfirm({confirmation,busy,onClose}:{confirmation:Confirmation;busy:boolean;onClose:()=>void}){
 const ref=useRef<HTMLDialogElement>(null);
 useEffect(()=>{const dialog=ref.current;if(dialog&&!dialog.open)dialog.showModal();return()=>{if(dialog?.open)dialog.close()}},[]);
 return <dialog ref={ref} className="company-confirm" aria-labelledby="company-confirm-title" aria-describedby="company-confirm-description" onCancel={e=>{e.preventDefault();if(!busy)onClose()}}>
 <div className="confirm-heading"><div className={'confirm-icon '+(confirmation.danger?'danger':'')}>{confirmation.danger?<AlertTriangle size={25}/>:<ShieldCheck size={25}/>}</div><button className="icon-button" type="button" disabled={busy} aria-label="Fermer" onClick={onClose}><X/></button></div>
 <h2 id="company-confirm-title">{confirmation.title}</h2><p id="company-confirm-description">{confirmation.message}</p>
 <div className="confirm-actions"><button autoFocus className="outline" disabled={busy} onClick={onClose}>Retour</button><button className={'primary '+(confirmation.danger?'danger-action':'')} disabled={busy} onClick={()=>void confirmation.run()}>{busy?'Traitement…':confirmation.label}</button></div>
 </dialog>
}

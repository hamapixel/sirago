import {CalendarDays} from 'lucide-react';
import type {Booking} from './booking-api';

export function reportUnavailableReason(b:Booking,now=Date.now()):string|null{
 if(b.sandbox_checkout)return 'Le report des billets SasPay TEST sera disponible dans une étape suivante.';
 if(b.status==='REPORTED')return 'Cette réservation a déjà été reportée.';
 if(b.status!=='TEST_PAID')return 'Le report nécessite un paiement simulé réussi.';
 if(!b.simulation_enabled)return 'Le report de test est désactivé.';
 if(!b.trips.length||b.trips.some(t=>!Number.isFinite(Date.parse(t.starts_at))))return 'Informations de départ indisponibles.';
 if(b.trips.some(t=>Date.parse(t.starts_at)<=now))return 'Le voyage a déjà commencé ou sa date de départ est dépassée.';
 return null;
}
export default function ReportAction({booking,onReport,now=Date.now()}:{booking:Booking;onReport:()=>void;now?:number}){
 const reason=reportUnavailableReason(booking,now);
 return <div className="ticket-report-action"><button className="outline" type="button" disabled={reason!==null} onClick={onReport}><CalendarDays size={19}/><span>Reporter le voyage</span></button>{reason?<small>{reason}</small>:<small>Changer la date de départ de tout ou partie des passagers · TEST</small>}</div>
}

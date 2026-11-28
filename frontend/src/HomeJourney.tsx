import {useId,useState} from 'react';
import {ArrowRight,ArrowUpRight,CalendarClock,CheckCircle2,CircleHelp,MapPin,Route,Search,ShieldCheck,Ticket,Wallet,BusFront} from 'lucide-react';
import {t,useLanguage} from './i18n';
import './home-journey.css';

const steps=[
 {title:'Tracez votre itinéraire',body:'Indiquez vos villes, vos dates et les personnes qui voyagent avec vous.',Icon:MapPin,Visual:Route},
 {title:'Comparez les départs',body:'Consultez les compagnies, les horaires, les places et les tarifs disponibles.',Icon:BusFront,Visual:Search},
 {title:'Préparez votre réservation',body:'Choisissez votre offre, renseignez les passagers et vérifiez le montant avant le paiement.',Icon:Wallet,Visual:ShieldCheck},
 {title:'Gardez votre billet à portée de main',body:'Retrouvez le billet numérique et son QR code dans votre compte après confirmation.',Icon:Ticket,Visual:CheckCircle2}
] as const;
export function HomeJourney({onSearch}:{onSearch:()=>void}){
 useLanguage();const id=useId();
 return <section className="home-journey" aria-labelledby={id}>
  <header className="home-journey-head"><span className="home-gold-eyebrow"><Route size={15}/>{t('LE PARCOURS SIRAGO')}</span><h2 id={id}>{t('De votre départ à votre arrivée, tout commence ici.')}</h2><p>{t('Organisez votre voyage en quelques étapes, à votre rythme.')}</p></header>
  <ol className="home-journey-steps">{steps.map(({title,body,Icon,Visual},i)=><li key={title}><span className="home-step-number" aria-hidden="true">{String(i+1).padStart(2,'0')}</span><div className="home-step-copy"><h3>{t(title)}</h3><p>{t(body)}</p></div><span className="home-step-art" aria-hidden="true"><Icon size={29}/><Visual className="home-step-mini" size={17}/></span></li>)}</ol>
  <div className="home-journey-foot"><span><ShieldCheck size={19}/>{t('Vous choisissez. SiraGo vous accompagne.')}</span><button type="button" className="primary home-gold-cta" onClick={onSearch}>{t('Trouvez votre voyage')}<ArrowRight size={18}/></button></div>
 </section>
}
export function HomeServices({onSearch,onTickets,onSupport}:{onSearch:()=>void;onTickets:()=>void;onSupport:()=>void}){
 useLanguage();const id=useId();const [paymentOpen,setPaymentOpen]=useState(false);
 const cards=[
  {key:'payment',Icon:ShieldCheck,title:'Paiement SasPay',description:'Simulation',action:()=>setPaymentOpen(v=>!v)},
  {key:'tickets',Icon:Ticket,title:'Billet numérique',description:'QR individuel ou collectif',action:onTickets},
  {key:'report',Icon:CalendarClock,title:'Report de voyage',description:'Selon les conditions',action:onTickets},
  {key:'support',Icon:CircleHelp,title:'Assistance',description:'Centre d’aide',action:onSupport}
 ] as const;
 return <section className="home-services" aria-labelledby={id+'-title'}><header><span className="home-gold-eyebrow">{t('À VOTRE SERVICE')}</span><h2 id={id+'-title'}>{t('Vos essentiels de voyage')}</h2><p>{t('Accédez directement aux services SiraGo.')}</p></header>
  <div className="home-service-grid">{cards.map(({key,Icon,title,description,action})=><button type="button" key={key} className="home-service-card" onClick={action} aria-expanded={key==='payment'?paymentOpen:undefined} aria-controls={key==='payment'?id+'-payment':undefined}><span className="home-service-icon"><Icon size={23}/></span><ArrowUpRight className="home-service-arrow" size={16} aria-hidden="true"/><strong>{t(title)}</strong><small>{t(description)}</small></button>)}</div>
  {paymentOpen&&<div className="home-payment-info" id={id+'-payment'}><strong>{t('Paiement SasPay')}</strong><p>{t('Les paiements sont actuellement en simulation. Aucun paiement réel ni billet valable pour voyager ne peut être obtenu dans ce mode.')}</p><button type="button" className="outline" onClick={onSearch}>{t('Trouvez votre voyage')}<ArrowRight size={16}/></button></div>}
 </section>
}

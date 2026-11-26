import {t, t as translate,useLanguage,LanguageSelect} from './i18n';
import {lazy,Suspense,useEffect,useState} from 'react';
const AuthPage=lazy(()=>import('./AuthPage'));
import SplashScreen from './SplashScreen';
const NotificationsDialog=lazy(()=>import('./NotificationsDialog'));
import {useNotificationCount} from './NotificationCenter';
const TravelerProfile=lazy(()=>import('./TravelerProfile'));
const SupportCenter=lazy(()=>import('./SupportCenter'));
const SuperadminSpace=lazy(()=>import('./SuperadminSpace'));
const CompanySpace=lazy(()=>import('./CompanySpace'));
const CompanyAgentSpace=lazy(()=>import('./CompanyAgentSpace'));
const TravelResults=lazy(()=>import('./TravelResults'));
import {CityField} from './CityField';
import {PartnerCard} from './PartnerCard';
import FeaturedTrips from './FeaturedTrips';
const PartnerSpace=lazy(()=>import('./PartnerSpace'));
const BookingSpace=lazy(()=>import('./BookingSpace'));
const MyBookings=lazy(()=>import('./BookingSpace').then(m=>({default:m.MyBookings})));
import {parseSelection,bookingUrl,authUrl,type Selection} from './booking-api';
import {useTravel,type HomeData,type Trip,type PartnerCompany} from './travel-api';
import {authPost,currentAccount,destination,type Account} from './auth-api';
import InstallApp from './InstallApp';
import './install-app.css';
import {ArrowLeftRight, ArrowRight, Bell, CalendarDays, CalendarClock, LogOut, CircleHelp, House, Minus, Plus, Search, ShieldCheck, Ticket, UserRound, Users} from 'lucide-react';
import {Swiper,SwiperSlide} from 'swiper/react';
import {Autoplay,Pagination,A11y} from 'swiper/modules';
import {stepPassengerCount,localToday,validSearch} from './search';
const slides=[['Ka billet ta fô i sigi yorola.','Réservez votre billet sans vous déplacer.'],['Voyagez en toute simplicité.','Comparez les offres.'],['Votre billet dans votre téléphone.','Vos billets à portée de main.'],['Vos projets changent ?','Report selon les conditions de la compagnie.']];
export default function App(){
 useLanguage();
 const [from,SFrom]=useState(''),[to,STo]=useState(''),[date,SD]=useState(localToday()),[back,SB]=useState(''),[round,SR]=useState(false),[count,SC]=useState(1),[tab,STab]=useState(new URLSearchParams(window.location.search).get('view')==='tickets'?'tickets':new URLSearchParams(window.location.search).get('view')==='profile'?'profile':'home'),[result,SResult]=useState(false),[paused,SP]=useState(false);
 const reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 const path=window.location.pathname;
 const [account,setAccount]=useState<Account|null>(null),[loading,setLoading]=useState(true),[sessionError,setSessionError]=useState('');
 const [notificationsOpen,setNotificationsOpen]=useState(()=>new URLSearchParams(window.location.search).get('notifications')==='1');
 useEffect(()=>{if(!('serviceWorker' in navigator))return;const onMessage=(event:MessageEvent)=>{if(event.data?.type==='SIRAGO_OPEN_NOTIFICATIONS')setNotificationsOpen(true)};navigator.serviceWorker.addEventListener('message',onMessage);return()=>navigator.serviceWorker.removeEventListener('message',onMessage)},[]);
 function closeNotifications(){setNotificationsOpen(false);const url=new URL(window.location.href);if(url.searchParams.has('notifications')){url.searchParams.delete('notifications');window.history.replaceState(window.history.state,'',url)}}
 const unreadCount=useNotificationCount(!!account);
 const preview=path==='/company/';
 const supervision=path==='/superadmin/';
 const selection=parseSelection(window.location.search);
 const booking=path==='/booking/';
 const protectedPath=booking||preview||supervision||path==='/app/'||path==='/preview/company/';
 const auth=path==='/login/'||path==='/register/';
 useEffect(()=>{let active=true;currentAccount().then(a=>{if(active){setAccount(a);setLoading(false)}}).catch(()=>{if(active){setSessionError('Impossible de vérifier votre session. Vérifiez votre connexion.');setLoading(false)}});return()=>{active=false}},[]);
 useEffect(()=>{if(loading||sessionError)return;if(!account&&protectedPath){window.location.replace(booking&&selection?authUrl(false,selection):'/login/');return}if(account&&(auth||path==='/preview/company/'||(preview&&account.role!=='COMPANY')||(supervision&&account.role!=='ADMIN')||((path==='/app/'||booking)&&account.role!=='TRAVELER')||(path==='/'&&account.role!=='TRAVELER'))){window.location.replace(auth&&selection&&account.role==='TRAVELER'?bookingUrl(selection):destination(account))}},[account,loading,sessionError,auth,path,preview,protectedPath,booking,selection?.out,selection?.ret,selection?.count]);
 async function signOut(){try{await authPost('logout',{});window.location.assign('/')}catch(e){setSessionError(e instanceof Error?e.message:'Déconnexion impossible.')}}
 const auto=paused||reduce?false:{delay:5000,disableOnInteraction:true,pauseOnMouseEnter:true};
 const key=paused?'paused':'playing';
 const [partner,setPartner]=useState<PartnerCompany|null>(null);
 const choose=(v:string)=>{if(booking){window.location.assign(v==='tickets'?'/app/?view=tickets':v==='profile'?'/app/?view=profile':'/app/');return}STab(v);SResult(false);setPartner(null)};
 const [initialTrip,setInitialTrip]=useState<Trip|null>(null);
 const criteria={origin:from,destination:to,date,back,round,count};
 const searchValid=validSearch(from,to,date,back,round,count,localToday());
 const homeData=useTravel<HomeData>(!auth&&!preview&&!supervision&&!booking&&tab==='home'&&!result&&!partner?'home/':null,0);
 const popular=homeData.data?.departures||[],companies=homeData.data?.companies||[];
 function openResults(trip?:Trip){if(searchValid){setInitialTrip(trip||null);SResult(true);window.scrollTo({top:0,behavior:'instant'})}}
 function continueBooking(out:Trip,ret:Trip|null){const s:Selection={out:out.id,...(ret?{ret:ret.id}:{}),count};window.location.assign(account?.role==='TRAVELER'?bookingUrl(s):authUrl(false,s))}
 function openPartner(company:PartnerCompany){setPartner(company);SResult(false);window.scrollTo({top:0,behavior:'instant'})}
 function closePartner(){setPartner(null);requestAnimationFrame(()=>document.getElementById('home-partners')?.scrollIntoView({block:'start'}))}
 function bookPartner(trip:Trip,passengers:number){const s:Selection={out:trip.id,count:passengers};window.location.assign(account?.role==='TRAVELER'?bookingUrl(s):authUrl(false,s))}
 function closeResults(){SResult(false);requestAnimationFrame(()=>document.querySelector('.search-section')?.scrollIntoView({block:'start'}))}

 if(loading)return <SplashScreen message="Chargement…"/>;
 if((protectedPath||auth)&&sessionError)return <main className="layout"><p role="alert">{sessionError}</p><button className="primary" onClick={()=>window.location.reload()}>{t("Réessayer")}</button></main>;
 if(!sessionError&&((protectedPath&&!account)||(account&&(auth||path==='/preview/company/'||(preview&&account.role!=='COMPANY')||(supervision&&account.role!=='ADMIN')||((path==='/app/'||booking)&&account.role!=='TRAVELER')||(path==='/'&&account.role!=='TRAVELER')))))return <SplashScreen message="Redirection…"/>;
 if(supervision&&account?.role==='ADMIN')return <Suspense fallback={<SplashScreen message="Chargement de l’administration…"/>}><SuperadminSpace account={account} onUpdated={setAccount} onLogout={signOut} sessionError={sessionError} unreadCount={unreadCount} notificationsOpen={notificationsOpen} onNotifications={()=>setNotificationsOpen(true)}/>{notificationsOpen&&<NotificationsDialog signedIn onClose={closeNotifications}/>}</Suspense>;
 return <><header className="header"><div className="header-inner"><a className="brand" href="/"><img src="/logo.svg" alt=""/><span>SiraGo</span></a><div className="header-actions"><LanguageSelect/>{account?<button type="button" className="outline header-logout" aria-label={t("Déconnexion")} onClick={signOut}><span>{t("Déconnexion")}</span><LogOut size={18} aria-hidden="true"/></button>:<a href="/login/" className="login" aria-current={path==='/login/'?'page':undefined}>{t("Connexion")}</a>}<button type="button" className="icon-button notification-bell" aria-label={unreadCount?`Notifications, ${unreadCount} non lues`:"Notifications"} aria-haspopup="dialog" aria-expanded={notificationsOpen} onClick={()=>setNotificationsOpen(true)}><Bell size={21}/>{unreadCount>0&&<span className="notification-count" aria-hidden="true">{unreadCount>99?'99+':unreadCount}</span>}</button></div></div></header>
 <main className={preview?"layout company-layout":auth?"layout auth-layout":"layout"}><Suspense fallback={<div className="sirago-inline-loading" role="status"><span className="sirago-splash-loader" aria-hidden="true"/>{t("Chargement…")}</div>}>
 {sessionError&&<p role="alert" className="auth-error">{sessionError}</p>}{auth?<AuthPage register={path==='/register/'} selection={selection}/>:preview&&account?(account.company_role==="CLERK"||account.company_role==="CONTROLLER"?<CompanyAgentSpace account={account} onLogout={signOut}/>:<CompanySpace account={account} onLogout={signOut} onUpdated={setAccount}/>):booking&&account?<>{selection?<BookingSpace selection={selection} account={account} onHistory={()=>choose('tickets')}/>:<section className="panel empty"><p>Sélection de voyage invalide.</p><a href="/app/" className="primary">Rechercher un voyage</a></section>}</>:tab==='home'&&partner?<PartnerSpace key={partner.id} company={partner} initialCount={count} onBack={closePartner} onBook={bookPartner}/>:tab==='home'&&result?<TravelResults criteria={criteria} initialTrip={initialTrip} onBack={closeResults} onContinue={continueBooking}/>:tab==='home'?<>
 {account?.role==="TRAVELER"&&<p className="welcome-user">{t("Bienvenue")}, {account.first_name} !</p>}
 <section className="hero" aria-label="Présentation SiraGo"><div className="hero-top"><span>SIRAGO</span><button onClick={()=>SP(!paused)} className="pause">{t(paused?'Reprendre':'Pause')}</button></div><Swiper key={key} modules={[Autoplay,Pagination,A11y]} autoplay={auto} pagination={{clickable:true}} loop slidesPerView={1} speed={reduce?0:450}>{slides.map(([title,desc],i)=><SwiperSlide key={title}><div className="hero-slide"><h1>{t(title)}</h1><p>{t(desc)}</p><img src={`/images/slides/slide-0${i+1}.webp`} alt={["Autocar SiraGo sur une route africaine","Intérieur illustratif d’un autocar confortable","Voyageur présentant son billet numérique illustratif","Autocar SiraGo dans un paysage africain"][i]} loading={i===0?'eager':'lazy'} onError={e=>{if(!e.currentTarget.src.endsWith("/coach.svg"))e.currentTarget.src="/coach.svg"}}/></div></SwiperSlide>)}</Swiper></section>
 <InstallApp/>
 <section className="search-section"><h2>{t("Trouvez votre voyage")}</h2><form className="panel search-form" onSubmit={e=>{e.preventDefault();openResults()}}><div className="segments"><button type="button" className={!round?'active':''} aria-pressed={!round} onClick={()=>SR(false)}>{t("Aller simple")}</button><button type="button" className={round?'active':''} aria-pressed={round} onClick={()=>SR(true)}>{t("Aller-retour")}</button></div><div className="locations"><CityField label={t("Ville de départ")} value={from} onChange={v=>{SFrom(v);SResult(false)}}/><button type="button" aria-label="Inverser les destinations" className="swap" onClick={()=>{SFrom(to);STo(from);SResult(false)}}><ArrowLeftRight size={20}/></button><CityField label={t("Ville d’arrivée")} value={to} onChange={v=>{STo(v);SResult(false)}}/></div><div className="dates"><label>{t("Date de départ")}<div className="field"><CalendarDays size={19}/><input type="date" min={localToday()} value={date} onChange={e=>{SD(e.target.value);SResult(false)}} required/></div></label>{round&&<label>{t("Date de retour")}<div className="field"><CalendarDays size={19}/><input type="date" min={date} value={back} onChange={e=>{SB(e.target.value);SResult(false)}} required/></div></label>}</div><div className="passengers"><Users size={20}/><strong>{t("Passagers")}</strong><button type="button" className="counter" disabled={count<=1} aria-label="Retirer un passager" onClick={()=>SC(n=>stepPassengerCount(n,-1))}><Minus size={18}/></button><select className="passenger-count-select" aria-label="Nombre de passagers" value={count} onChange={e=>{SC(Number(e.target.value));SResult(false)}}>{Array.from({length:100},(_,i)=><option key={i+1} value={i+1}>{i+1}</option>)}</select><button type="button" className="counter" disabled={count>=100} aria-label="Ajouter un passager" onClick={()=>SC(n=>stepPassengerCount(n,1))}><Plus size={18}/></button></div><button className="primary" disabled={!searchValid}><Search size={20}/> {t("Rechercher")}</button></form></section>
 
 <section>{homeData.error?<><div className="section-title"><h2>{t("Trajets proposés")}</h2></div><div className="panel travel-home-empty">{homeData.error} <button className="outline" onClick={homeData.retry}>{t("Réessayer")}</button></div></>:homeData.loading?<><div className="section-title"><h2>{t("Trajets proposés")}</h2></div><p className="muted" role="status">{t("Chargement des trajets…")}</p></>:<FeaturedTrips trips={popular} logos={homeData.data?.company_logos??{}} count={count} onBook={bookPartner}/>}</section>
 <section id="home-partners" style={{scrollMarginTop:80}}><div className="section-title"><h2>{t("Compagnies partenaires")}</h2></div>{homeData.error?<p className="panel travel-home-empty">Impossible de charger les compagnies.</p>:homeData.loading?<p className="muted">Chargement des compagnies…</p>:!companies.length?<p className="panel travel-home-empty">Aucune compagnie disponible.</p>:<Swiper key={'partner-'+key+'-'+companies.length} modules={[Autoplay,Pagination,A11y]} autoplay={companies.length>2?auto:false} pagination={{clickable:true}} loop={companies.length>3} spaceBetween={12} slidesPerView={1.15} breakpoints={{640:{slidesPerView:2},1024:{slidesPerView:2}}} className="partners">{companies.map(c=><SwiperSlide key={c.id}><PartnerCard company={c} onOpen={()=>openPartner(c)}/></SwiperSlide>)}</Swiper>}</section>
 <section className="stats benefits">{[[ShieldCheck,'Paiement SasPay','Simulation'],[Ticket,'Billet numérique','QR individuel ou collectif'],[CalendarClock,'Report de voyage','Selon les conditions'],[CircleHelp,'Assistance','Centre d’aide']].map(([I,t,status])=>{const Icon=I as typeof ShieldCheck;return t==='Assistance'?<button type="button" className="panel menu" key={String(t)} onClick={()=>{choose('support');window.scrollTo({top:0,behavior:'instant'})}}><Icon size={23}/>{translate(String(t))}<small>{translate(String(status))}</small></button>:<article className="panel menu" key={String(t)}><Icon size={23}/>{translate(String(t))}<small>{translate(String(status))}</small></article>})}</section>
 {!account&&!loading&&<section className="panel join"><h2>Rejoignez SiraGo</h2><a className="primary" href="/register/">Créer mon compte <ArrowRight size={18}/></a></section>}
 </>:tab==='support'?<section className="booking-space"><button className="outline" onClick={()=>choose('home')}>Retour à l’accueil</button><Suspense fallback={<p role="status">Chargement de l’assistance…</p>}><SupportCenter signedIn={!!account}/></Suspense></section>:tab==='tickets'?<MyBookings account={account} onSearch={()=>choose('home')}/>:<TravelerProfile account={account?.role==='TRAVELER'?account:null} onUpdated={setAccount} onTickets={()=>choose('tickets')} onLogout={signOut}/>}
 </Suspense><footer>Propulsé par BTDIGIT</footer></main>
 {!auth&&!preview&&<nav className="bottom" aria-label="Navigation principale">{preview?<a href="/"><House size={22}/>{t("Accueil")}</a>:[[House,'Accueil','home'],[Ticket,'Mes billets','tickets'],[UserRound,'Profil','profile']].map(([I,label,v])=>{const Icon=I as typeof House;return <button key={String(v)} className={tab===v?'selected':''} onClick={()=>choose(String(v))} aria-current={tab===v?'page':undefined}><Icon size={23}/>{t(String(label))}</button>})}</nav>}{notificationsOpen&&<Suspense fallback={<div className="sirago-inline-loading" role="status"><span className="sirago-splash-loader" aria-hidden="true"/>{t("Chargement…")}</div>}><NotificationsDialog signedIn={!!account} onClose={closeNotifications}/></Suspense>}</>;
}

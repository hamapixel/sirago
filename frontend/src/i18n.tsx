import {useEffect,useSyncExternalStore} from 'react';
export type Language='fr'|'en'|'bm';
const words:Record<string,{en:string;bm:string}>={
  "Accueil": {
    "en": "Home",
    "bm": "So"
  },
  "Mes billets": {
    "en": "My tickets",
    "bm": "N ka biyɛtininw"
  },
  "Profil": {
    "en": "Profile",
    "bm": "N kunnafoni"
  },
  "Mon profil": {
    "en": "My profile",
    "bm": "N kunnafoni"
  },
  "Déconnexion": {
    "en": "Sign out",
    "bm": "Bɔ"
  },
  "Connexion": {
    "en": "Sign in",
    "bm": "Don"
  },
  "Se connecter": {
    "en": "Sign in",
    "bm": "Don"
  },
  "S’inscrire": {
    "en": "Sign up",
    "bm": "Tɔgɔ sɛbɛn"
  },
  "Créer un compte": {
    "en": "Create an account",
    "bm": "Jate da"
  },
  "Retour": {
    "en": "Back",
    "bm": "Segin"
  },
  "Réessayer": {
    "en": "Try again",
    "bm": "A lajɛ kokura"
  },
  "Actualiser": {
    "en": "Refresh",
    "bm": "A kura"
  },
  "Rechercher": {
    "en": "Search",
    "bm": "Ɲini"
  },
  "Ajouter": {
    "en": "Add",
    "bm": "Fara a kan"
  },
  "Modifier": {
    "en": "Edit",
    "bm": "A sɛmɛntiya"
  },
  "Enregistrer": {
    "en": "Save",
    "bm": "A mara"
  },
  "Annuler": {
    "en": "Cancel",
    "bm": "A dabila"
  },
  "Confirmer": {
    "en": "Confirm",
    "bm": "A sɛmɛntiya"
  },
  "Tableau de bord": {
    "en": "Dashboard",
    "bm": "Kunnafoni walada"
  },
  "Mes cars": {
    "en": "My coaches",
    "bm": "N ka bisiw"
  },
  "Mes trajets": {
    "en": "My routes",
    "bm": "N ka siraw"
  },
  "Mes départs": {
    "en": "My departures",
    "bm": "N ka boli waatiw"
  },
  "Réservations": {
    "en": "Bookings",
    "bm": "Biyɛti taɲininiw"
  },
  "Contrôle des billets": {
    "en": "Ticket inspection",
    "bm": "Biyɛti lajɛli"
  },
  "Recettes": {
    "en": "Revenue",
    "bm": "Wari donni"
  },
  "Finances": {
    "en": "Finances",
    "bm": "Wari ko"
  },
  "Compagnies": {
    "en": "Companies",
    "bm": "Bisi baaradaɲɛw"
  },
  "Voyageurs": {
    "en": "Travelers",
    "bm": "Taga bagaw"
  },
  "Commissions": {
    "en": "Commissions",
    "bm": "Cɛɲɛwari"
  },
  "Reversements": {
    "en": "Settlements",
    "bm": "Wari seginni"
  },
  "Assistance": {
    "en": "Support",
    "bm": "Dɛmɛ"
  },
  "Administration Django": {
    "en": "Django administration",
    "bm": "Django ɲɛmɔgɔya"
  },
  "Trajets proposés": {
    "en": "Suggested routes",
    "bm": "Sira sugandilenw"
  },
  "Compagnies partenaires": {
    "en": "Partner companies",
    "bm": "Bisi baarakɛɲɔgɔnw"
  },
  "À partir de": {
    "en": "From",
    "bm": "A bɛ daminɛ"
  },
  "Voir les trajets": {
    "en": "View routes",
    "bm": "Siraw lajɛ"
  },
  "Trouvez votre voyage": {
    "en": "Find your trip",
    "bm": "I ka taama ɲini"
  },
  "Ville de départ": {
    "en": "Departure city",
    "bm": "Bɔyɔrɔ dugu"
  },
  "Ville d’arrivée": {
    "en": "Arrival city",
    "bm": "Seyɔrɔ dugu"
  },
  "Date de départ": {
    "en": "Departure date",
    "bm": "Bɔ don"
  },
  "Date de retour": {
    "en": "Return date",
    "bm": "Segindon"
  },
  "Aller simple": {
    "en": "One way",
    "bm": "Taama kelen"
  },
  "Aller-retour": {
    "en": "Round trip",
    "bm": "Taama ni segin"
  },
  "Passagers": {
    "en": "Passengers",
    "bm": "Taga bagaw"
  },
  "Passager": {
    "en": "Passenger",
    "bm": "Taga baga"
  },
  "Rechercher une ville": {
    "en": "Search for a city",
    "bm": "Dugu ɲini"
  },
  "Aucune ville trouvée": {
    "en": "No city found",
    "bm": "Dugu ma sɔrɔ"
  },
  "Détails de la réservation": {
    "en": "Booking details",
    "bm": "Biyɛti taɲinini kunnafoni"
  },
  "Paiement": {
    "en": "Payment",
    "bm": "Wari sara"
  },
  "Réservation": {
    "en": "Booking",
    "bm": "Biyɛti taɲinini"
  },
  "Départ": {
    "en": "Departure",
    "bm": "Bɔyɔrɔ"
  },
  "Arrivée": {
    "en": "Arrival",
    "bm": "Seyɔrɔ"
  },
  "Date": {
    "en": "Date",
    "bm": "Don"
  },
  "Montant": {
    "en": "Amount",
    "bm": "Wari hakɛ"
  },
  "Catégorie": {
    "en": "Category",
    "bm": "Suguya"
  },
  "Télécharger": {
    "en": "Download",
    "bm": "A telesarse"
  },
  "Partager": {
    "en": "Share",
    "bm": "A tila"
  },
  "Billets numériques": {
    "en": "Digital tickets",
    "bm": "Telefɔni biyɛtininw"
  },
  "Voir mes billets": {
    "en": "View my tickets",
    "bm": "N ka biyɛtininw lajɛ"
  },
  "Voir les détails": {
    "en": "View details",
    "bm": "Kunnafoni lajɛ"
  },
  "Reporter le voyage": {
    "en": "Reschedule trip",
    "bm": "Taama don yɛlɛma"
  },
  "Statut": {
    "en": "Status",
    "bm": "A cogoya"
  },
  "Activité du jour": {
    "en": "Today’s activity",
    "bm": "Bi ka baara"
  },
  "Cars actifs": {
    "en": "Active coaches",
    "bm": "Bisi baara la"
  },
  "Trajets actifs": {
    "en": "Active routes",
    "bm": "Sira baara la"
  },
  "Départs du jour": {
    "en": "Today’s departures",
    "bm": "Bi ka boli"
  },
  "Places libres du jour": {
    "en": "Available seats today",
    "bm": "Bi sigiyɔrɔ lakolonw"
  },
  "Informations de la compagnie": {
    "en": "Company information",
    "bm": "Baarada kunnafoni"
  },
  "Informations du responsable": {
    "en": "Manager information",
    "bm": "Ɲɛmɔgɔ kunnafoni"
  },
  "Sécurité du compte": {
    "en": "Account security",
    "bm": "Jate lakana"
  },
  "Agents de la compagnie": {
    "en": "Company agents",
    "bm": "Baarada baarakɛlaw"
  },
  "Notifications": {
    "en": "Notifications",
    "bm": "Kibaruya"
  },
  "Assistance SiraGo": {
    "en": "SiraGo support",
    "bm": "SiraGo dɛmɛ"
  },
  "Nom de la compagnie": {
    "en": "Company name",
    "bm": "Baarada tɔgɔ"
  },
  "Ville": {
    "en": "City",
    "bm": "Dugu"
  },
  "Adresse": {
    "en": "Address",
    "bm": "Sigiyɔrɔ"
  },
  "Immatriculation": {
    "en": "Registration number",
    "bm": "Matirikili"
  },
  "Prénom": {
    "en": "First name",
    "bm": "Tɔgɔ"
  },
  "Nom": {
    "en": "Last name",
    "bm": "Jamu"
  },
  "Téléphone": {
    "en": "Phone",
    "bm": "Telefɔni"
  },
  "Email": {
    "en": "Email",
    "bm": "Imɛli"
  },
  "Mot de passe": {
    "en": "Password",
    "bm": "Gundo daɲɛ"
  },
  "Mot de passe actuel": {
    "en": "Current password",
    "bm": "Gundo daɲɛ kɔrɔ"
  },
  "Nouveau mot de passe": {
    "en": "New password",
    "bm": "Gundo daɲɛ kura"
  },
  "Confirmer le mot de passe": {
    "en": "Confirm password",
    "bm": "Gundo daɲɛ sɛmɛntiya"
  },
  "Recettes et finances": {
    "en": "Revenue and finances",
    "bm": "Wari donni ni jate"
  },
  "Période": {
    "en": "Period",
    "bm": "Waati"
  },
  "Aujourd’hui": {
    "en": "Today",
    "bm": "Bi"
  },
  "Semaine": {
    "en": "Week",
    "bm": "Dɔgɔkun"
  },
  "Mois": {
    "en": "Month",
    "bm": "Kalo"
  },
  "Du": {
    "en": "From",
    "bm": "Ka bɔ"
  },
  "Au": {
    "en": "To",
    "bm": "Ka se"
  },
  "Détail par départ": {
    "en": "Departure details",
    "bm": "Boli kunnafoni"
  },
  "Recettes réelles": {
    "en": "Actual revenue",
    "bm": "Wari donnen tiɲɛ"
  },
  "Réservations en attente": {
    "en": "Pending bookings",
    "bm": "Biyɛtininw makɔnɔ"
  },
  "Caméra": {
    "en": "Camera",
    "bm": "Kamera"
  },
  "Image": {
    "en": "Image",
    "bm": "Ja"
  },
  "Manuel": {
    "en": "Manual",
    "bm": "Bolo la"
  },
  "Ouvrir la caméra": {
    "en": "Open camera",
    "bm": "Kamera dayɛlɛ"
  },
  "Historique des embarquements": {
    "en": "Boarding history",
    "bm": "Bisi donni tariku"
  },
  "Identité visuelle": {
    "en": "Visual identity",
    "bm": "Baarada ja"
  },
  "Logo": {
    "en": "Logo",
    "bm": "Taamasiyɛn"
  },
  "Bannière": {
    "en": "Banner",
    "bm": "Ja belebele"
  },
  "Choisir un logo": {
    "en": "Choose a logo",
    "bm": "Taamasiyɛn sugandi"
  },
  "Choisir une bannière": {
    "en": "Choose a banner",
    "bm": "Ja belebele sugandi"
  },
  "Retirer": {
    "en": "Remove",
    "bm": "A bɔ"
  },
  "Compagnie validée": {
    "en": "Verified company",
    "bm": "Baarada sɛmɛntiyalen"
  },
  "Compagnie vérifiée": {
    "en": "Verified company",
    "bm": "Baarada sɛmɛntiyalen"
  },
  "Actif": {
    "en": "Active",
    "bm": "Baara la"
  },
  "Inactif": {
    "en": "Inactive",
    "bm": "Baara tɛ"
  },
  "Publiés": {
    "en": "Published",
    "bm": "Bɔlenw"
  },
  "Disponibles": {
    "en": "Available",
    "bm": "Bɛ sɔrɔ"
  },
  "Brouillons": {
    "en": "Drafts",
    "bm": "Sɛbɛn fɔlɔw"
  },
  "Suspendus": {
    "en": "Suspended",
    "bm": "Dabilalenw"
  },
  "Annulés": {
    "en": "Cancelled",
    "bm": "Dabilalenw"
  },
  "Standard": {
    "en": "Standard",
    "bm": "Standard"
  },
  "Premium": {
    "en": "Premium",
    "bm": "Premium"
  },
  "Chargement…": {
    "en": "Loading…",
    "bm": "A bɛ na…"
  },
  "Aucune réservation trouvée.": {
    "en": "No bookings found.",
    "bm": "Biyɛti taɲinini ma sɔrɔ."
  },
  "Toutes les réservations": {
    "en": "All bookings",
    "bm": "Biyɛti taɲininiw bɛɛ"
  },
  "En attente de paiement": {
    "en": "Awaiting payment",
    "bm": "Wari sara makɔnɔ"
  },
  "Paiement simulé": {
    "en": "Simulated payment",
    "bm": "Wari sara kɔrɔbɔ"
  },
  "Expirée": {
    "en": "Expired",
    "bm": "Waati banna"
  },
  "Annulée": {
    "en": "Cancelled",
    "bm": "Dabilalen"
  },
  "Reportée": {
    "en": "Rescheduled",
    "bm": "Don yɛlɛmana"
  },
  "Bienvenue": {
    "en": "Welcome",
    "bm": "I ni ce"
  },
  "Pause": {
    "en": "Pause",
    "bm": "Jɔ"
  },
  "Reprendre": {
    "en": "Resume",
    "bm": "A daminɛ kokura"
  },
  "Simulation": {
    "en": "Simulation",
    "bm": "Kɔrɔbɔ"
  },
  "QR individuel ou collectif": {
    "en": "Individual or group QR",
    "bm": "QR kelen walima jamana"
  },
  "Selon les conditions": {
    "en": "Subject to conditions",
    "bm": "Sariya la"
  },
  "Centre d’aide": {
    "en": "Help center",
    "bm": "Dɛmɛ yɔrɔ"
  },
  "Votre billet dans votre téléphone.": {
    "en": "Your ticket on your phone.",
    "bm": "I ka biyɛtini bɛ i ka telefɔni kɔnɔ."
  },
  "Vos billets à portée de main.": {
    "en": "Keep your tickets at hand.",
    "bm": "I ka biyɛtininw bɛ i bolo."
  },
  "Réservez votre billet sans vous déplacer.": {
    "en": "Book your ticket without traveling to the station.",
    "bm": "I ka biyɛtini ta, i kana taga gare la."
  },
  "Voyagez en toute simplicité.": {
    "en": "Travel with ease.",
    "bm": "Taama ka nɔgɔn."
  },
  "Comparez les offres.": {
    "en": "Compare options.",
    "bm": "Suguyaw lajɛ."
  },
  "Vos projets changent ?": {
    "en": "Plans changed?",
    "bm": "I ka taama yɛlɛmana wa?"
  },
  "Report selon les conditions de la compagnie.": {
    "en": "Reschedule under the company’s conditions.",
    "bm": "Taama don yɛlɛma ni baarada sariya ye."
  }
};
const listeners=new Set<()=>void>();
function initial():Language{try{const saved=localStorage.getItem('sirago-language');return saved==='en'||saved==='bm'?saved:'fr'}catch{return 'fr'}}
let language:Language=initial();
export function translateText(text:string,lang:Language):string{return lang==='fr'?text:words[text]?.[lang]??text}
export function t(text:string){return translateText(text,language)}
function subscribe(fn:()=>void){listeners.add(fn);return()=>{listeners.delete(fn)}}
export function useLanguage(){return useSyncExternalStore(subscribe,()=>language,()=>'fr' as Language)}
export function setLanguage(lang:Language){language=lang;try{localStorage.setItem('sirago-language',lang)}catch{};if(typeof document!=='undefined')document.documentElement.lang=lang;listeners.forEach(fn=>fn())}
export function LanguageSelect(){const lang=useLanguage();useEffect(()=>{document.documentElement.lang=lang},[lang]);return <select className="sirago-language" aria-label="Langue / Language / Kan" value={lang} onChange={e=>setLanguage(e.target.value as Language)}><option value="fr">FR · Français</option><option value="en">EN · English</option><option value="bm">BM · Bamanankan</option></select>}

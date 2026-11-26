import {useEffect,useSyncExternalStore} from 'react';
import {ChevronDown} from 'lucide-react';
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
  },
  "Langue": {
    "en": "Language",
    "bm": "Kan"
  },
  "Cars": {
    "en": "Coaches",
    "bm": "Bisiw"
  },
  "Départs": {
    "en": "Departures",
    "bm": "Boliw"
  },
  "Scanner": {
    "en": "Scanner",
    "bm": "QR lajɛlan"
  },
  "Paiement SasPay": {
    "en": "SasPay payment",
    "bm": "SasPay wari sara"
  },
  "Billet numérique": {
    "en": "Digital ticket",
    "bm": "Telefɔni biyɛtini"
  },
  "Report de voyage": {
    "en": "Reschedule trip",
    "bm": "Taama don yɛlɛma"
  },
  "BILLET": {
    "en": "TICKET",
    "bm": "BIYƐTINI"
  },
  "Simulation — Non valable pour voyager": {
    "en": "Simulation — Not valid for travel",
    "bm": "Kɔrɔbɔ — A tɛ se ka taama ni a ye."
  },
  "Paiement SasPay confirmé (simulation)": {
    "en": "SasPay payment confirmed (simulation)",
    "bm": "SasPay wari sara sɛmɛntiyalen (kɔrɔbɔ)"
  },
  "Paiement SasPay à examiner (simulation)": {
    "en": "SasPay payment to review (simulation)",
    "bm": "SasPay wari sara lajɛli (kɔrɔbɔ)"
  },
  "Paiement SasPay à vérifier": {
    "en": "Verify SasPay payment",
    "bm": "SasPay wari sara lajɛ"
  },
  "Paiement tardif (simulation)": {
    "en": "Late payment (simulation)",
    "bm": "Wari sara kɔfɛ (kɔrɔbɔ)"
  },
  "Paramètres": {
    "en": "Settings",
    "bm": "Labɛnni"
  },
  "Mes réservations": {
    "en": "My bookings",
    "bm": "N ka biyɛti taɲininiw"
  },
  "Modifier mon profil": {
    "en": "Edit my profile",
    "bm": "N kunnafoni yɛlɛma"
  },
  "Aide & support": {
    "en": "Help & support",
    "bm": "Dɛmɛ"
  },
  "Informations légales": {
    "en": "Legal information",
    "bm": "Sariya kunnafoni"
  },
  "Changer le mot de passe": {
    "en": "Change password",
    "bm": "Gundo daɲɛ yɛlɛma"
  },
  "Transactions": {
    "en": "Transactions",
    "bm": "Wari ko"
  },
  "À propos": {
    "en": "About",
    "bm": "Kunnafoni"
  },
  "Toutes": {
    "en": "All",
    "bm": "Bɛɛ"
  },
  "Non lues": {
    "en": "Unread",
    "bm": "Kalanbaliw"
  },
  "Tout marquer comme lu": {
    "en": "Mark all as read",
    "bm": "Bɛɛ taamasiyɛn ko a kalanna"
  },
  "Marquer comme lu": {
    "en": "Mark as read",
    "bm": "A taamasiyɛn ko a kalanna"
  },
  "Actualiser les notifications": {
    "en": "Refresh notifications",
    "bm": "Kibaruya kura"
  },
  "Notifications sur cet appareil": {
    "en": "Notifications on this device",
    "bm": "Kibaruya nin telefɔni in kan"
  },
  "Activer": {
    "en": "Enable",
    "bm": "A daminɛ"
  },
  "Désactiver": {
    "en": "Disable",
    "bm": "A dabila"
  },
  "Bienvenue sur SiraGo": {
    "en": "Welcome to SiraGo",
    "bm": "I ni ce SiraGo la"
  },
  "Téléphone, email ou identifiant admin": {
    "en": "Phone, email or admin username",
    "bm": "Telefɔni, imɛli walima ɲɛmɔgɔ tɔgɔ"
  },
  "Compte voyageur": {
    "en": "Traveler account",
    "bm": "Taga baga jate"
  },
  "Connexion pour réserver": {
    "en": "Sign in to book",
    "bm": "Don ka biyɛti ta"
  },
  "Connectez-vous pour réserver.": {
    "en": "Sign in to book your trip.",
    "bm": "Don ka i ka biyɛti ta."
  },
  "Créer mon compte": {
    "en": "Create my account",
    "bm": "N ka jate da"
  },
  "Pas encore de compte ?": {
    "en": "New here?",
    "bm": "I ka jate tɛ wa?"
  },
  "Vous avez déjà un compte ?": {
    "en": "Already have an account?",
    "bm": "I ka jate bɛ wa?"
  },
  "Retour à l’accueil": {
    "en": "Back to home",
    "bm": "Segi so"
  },
  "Afficher le mot de passe": {
    "en": "Show password",
    "bm": "Gundo daɲɛ jira"
  },
  "Masquer le mot de passe": {
    "en": "Hide password",
    "bm": "Gundo daɲɛ dogo"
  },
  "Veuillez patienter…": {
    "en": "Please wait…",
    "bm": "Makɔnɔ dɔɔnin…"
  },
  "Continuer": {
    "en": "Continue",
    "bm": "A ka tɛmɛ"
  },
  "Retour aux réservations": {
    "en": "Back to bookings",
    "bm": "Segi biyɛti taɲininiw la"
  },
  "Liste des passagers": {
    "en": "Passenger list",
    "bm": "Taga bagaw tɔgɔw"
  },
  "Informations du trajet": {
    "en": "Trip information",
    "bm": "Taama kunnafoni"
  },
  "Référence": {
    "en": "Reference",
    "bm": "Taamasiyɛn"
  },
  "Embarqué (simulation)": {
    "en": "Boarded (simulation)",
    "bm": "Bisi donnen (kɔrɔbɔ)"
  },
  "Embarqués (simulation)": {
    "en": "Boarded (simulation)",
    "bm": "Bisi donnenw (kɔrɔbɔ)"
  },
  "Non embarqué": {
    "en": "Not boarded",
    "bm": "A ma don bisi la"
  },
  "Absent (simulation)": {
    "en": "Absent (simulation)",
    "bm": "A tɛ yan (kɔrɔbɔ)"
  },
  "Billet indisponible": {
    "en": "Ticket unavailable",
    "bm": "Biyɛtini tɛ sɔrɔ"
  },
  "Montant du trajet": {
    "en": "Trip amount",
    "bm": "Taama wari hakɛ"
  },
  "Montant simulé": {
    "en": "Simulated amount",
    "bm": "Wari hakɛ kɔrɔbɔ"
  },
  "Montant encaissé (réel)": {
    "en": "Actual collected amount",
    "bm": "Wari donnen tiɲɛ"
  },
  "Aucun encaissement ni embarquement réel.": {
    "en": "No actual payment or boarding.",
    "bm": "Wari sara ni bisi donni tiɲɛ tɛ."
  },
  "Billets collectifs": {
    "en": "Group tickets",
    "bm": "Biyɛti jamakulu"
  },
  "Billets individuels": {
    "en": "Individual tickets",
    "bm": "Kelen kelen biyɛtininw"
  },
  "Réservation créée le": {
    "en": "Booking created on",
    "bm": "Biyɛti taɲinini don"
  },
  "Voir plus": {
    "en": "See more",
    "bm": "Dɔwɛrɛw lajɛ"
  },
  "Voir moins": {
    "en": "See less",
    "bm": "Dɔɔnin lajɛ"
  },
  "Réserver maintenant": {
    "en": "Book now",
    "bm": "Biyɛti ta sisan"
  },
  "places disponibles": {
    "en": "seats available",
    "bm": "Sigiyɔrɔw bɛ yen"
  },
  "Places insuffisantes": {
    "en": "Not enough seats",
    "bm": "Sigiyɔrɔw man ca"
  },
  "passager": {
    "en": "passenger",
    "bm": "Taga baga"
  },
  "passagers": {
    "en": "passengers",
    "bm": "Taga bagaw"
  },
  "Total minimum": {
    "en": "Minimum total",
    "bm": "Wari hakɛ dɔgɔman"
  },
  "Aucun trajet publié.": {
    "en": "No published trips.",
    "bm": "Taama fɔlen tɛ yen."
  },
  "Chargement des trajets…": {
    "en": "Loading trips…",
    "bm": "Taamaw bɛ don…"
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
export function LanguageFlag({lang}:{lang:Language}){
 const bands=lang==='fr'?['#244aa5','#fff','#ed2939']:['#14a653','#f7cf35','#e33d42'];
 return <svg className="language-flag" viewBox="0 0 24 18" aria-hidden="true" focusable="false">{lang==='en'?<><rect width="24" height="18" fill="#17376b"/><path d="M0 0L24 18M24 0L0 18" stroke="#fff" strokeWidth="4"/><path d="M0 0L24 18M24 0L0 18" stroke="#ce2639" strokeWidth="1.5"/><path d="M12 0V18M0 9H24" stroke="#fff" strokeWidth="6"/><path d="M12 0V18M0 9H24" stroke="#ce2639" strokeWidth="3.5"/></>:bands.map((color,i)=><rect key={i} x={i*8} width="8" height="18" fill={color}/>)}</svg>
}
export function LanguageSelect(){
 const lang=useLanguage();
 useEffect(()=>{document.documentElement.lang=lang},[lang]);
 return <span className="language-pill"><span className="language-pill-face" aria-hidden="true"><LanguageFlag lang={lang}/><strong>{lang.toUpperCase()}</strong><ChevronDown size={13}/></span><select className="sirago-language" aria-label="Langue / Language / Kan" value={lang} onChange={e=>setLanguage(e.target.value as Language)}><option value="fr">🇫🇷 Français</option><option value="en">🇬🇧 English</option><option value="bm">🇲🇱 Bamanankan</option></select></span>
}

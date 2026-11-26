# Partenaires publics
1. Créer/valider la compagnie dans Django Admin, puis publier ses départs.
2. Dans VS Code, ouvrir frontend/src/partners.ts. Renseigner companyId (identifiant réel, recommandé), name, city, logo, cover, address, phones et location (latitude/longitude vérifiées). Les champs de présentation peuvent rester vides. Les photos vont dans frontend/public/images/partners/.
3. Les cartes de l'accueil correspondent aux compagnies ayant des départs futurs disponibles (catalogue existant). Le fichier ne peut pas créer une compagnie ni inventer des départs.
4. Le profil public charge les horaires de PostgreSQL par date, compagnie et nombre de passagers. Les départs non publiés, passés, inactifs, complets ou d'une compagnie non validée sont exclus. 20 départs par page, regroupés par trajet sur la page. Le prochain jour disponible est proposé si aucun départ ne correspond.
5. Le bouton localisation ouvre Google Maps sur les coordonnées vérifiées ou l'adresse renseignée. Sans ces données, aucun lien approximatif n'est affiché. Les numéros sont ceux autorisés pour publication, jamais les téléphones privés des comptes. Aucun avis ni note fictive.
6. Réserver utilise le flux existant (aller simple, sélection des passagers, devis serveur et paiement TEST). Les règles financières ne changent pas.

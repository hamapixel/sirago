# Phase 06 — Paiement et billets

## Étape 1 — Interface de paiement (sans débit)
Résumé calculé à partir de la réservation serveur : noms, catégories, tarifs par trajet, total, référence et expiration. Accès depuis confirmation et détail. Orange Money et Moov Money sont des choix indicatifs, aucun prestataire n'est connecté. Le bouton de paiement reste désactivé et aucune donnée de paiement sensible n'est collectée. Aucun changement backend ou migration.

## Étapes suivantes
Choisir le prestataire et vérifier les moyens réellement disponibles, créer les tentatives de paiement côté serveur, sécuriser la confirmation et le rapprochement des transactions (y compris paiement tardif et expiration), émettre les billets après confirmation, puis historique et tests. Aucun portefeuille, parrainage ni code promotionnel.

## Étape 2a — Diagnostic SasPay (Sandbox, lecture seule)
Prestataire retenu : SasPay. Réseaux cibles orange_ml et moov_ml, XOF, Mali. Voir https://docs.saspay.me/api-reference/reference/networks et https://docs.saspay.me/account-setup. Créer un marchand SiraGo et une clé SANDBOX de scope PAYIN, puis renseigner SASPAY_API_KEY dans le .env local ignoré par Git. Recréer uniquement le conteneur backend (`docker compose up -d --force-recreate backend`) pour injecter la variable. Exécuter `docker compose exec backend python manage.py check_saspay`. Cette commande consulte uniquement le catalogue paginé, sans afficher la clé ni déclencher de paiement. Le catalogue ne garantit pas l'éligibilité de chaque route pour le marchand. Aucun endpoint de paiement ou webhook exposé à ce stade.

La prochaine étape doit persister une tentative idempotente avant tout appel softpay, vérifier les tarifs et frais, gérer la redirection éventuelle et confirmer la transaction côté serveur. Les paiements tardifs doivent être rapprochés sans survente. Vérifier avec SasPay l'autorisation d'encaisser et de reverser aux compagnies, avant le passage en production. Référence : https://docs.saspay.me/api-reference/payments/softpay et https://docs.saspay.me/api-reference/webhooks.

## Étape 2b — Simulation locale
Activer uniquement dans la base locale de développement: DJANGO_DEBUG=1 et SIRAGO_ENABLE_SIMULATED_PAYMENTS=1 dans .env, puis recréer backend. Le POST de simulation est protégé par session, CSRF et propriété de réservation, et retourne 404 quand désactivé ou DEBUG=false. Montant issu du serveur, transaction atomique, un enregistrement de simulation par réservation, statut TEST_PAID distinct et places conservées après expiration. Aucun appel SasPay, aucune recette réelle, aucun billet émis. Ne jamais transférer les données locales de simulation vers la base de production. Les billets de test et la gestion des paiements réels seront des jalons séparés.

## Étape 3 — Billets numériques de test
Un billet par passager et trajet pour toute réservation TEST_PAID avec enregistrement de simulation. Références déterministes SRG-TEST, QR contenant uniquement cette référence, PDF et partage natif si disponible (sinon téléchargement). Endpoints privés, no-store, désactivés hors DEBUG et opt-in. Pas de migration ni d'émission réelle. Rebuild backend nécessaire (qrcode et reportlab). Les billets réels persistés et le contrôle compagnie seront des étapes distinctes.

## Étape 4 — Choix collectif / individuel
Nouvelles réservations : group par défaut, individual au choix avant confirmation. Un groupe par catégorie et par trajet ; une seule personne garde le billet individuel. Le format est enregistré et lié à l'idempotence. Les anciennes réservations restent individuelles (migration 0006). Capacité 1 à 100 selon disponibilités réelles, sans répartir une réservation sur plusieurs cars. Les PDF collectifs incluent les noms en annexe. Le scanner et la validation individuelle à l'embarquement restent à développer ; les références TEST ne sont pas des titres de transport. Avant production, renforcer les protections anti-blocage abusif de grandes réservations.

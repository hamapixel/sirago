# Diagnostic Checkout SasPay

Documentation : https://docs.saspay.me/sandbox et https://docs.saspay.me/api-reference/payments/checkout-create

La clé sk_test_ seule ne garantit pas le mode test. L'API est fixée à https://sandbox-api.saspay.me/api/v1 ; les redirections HTTP sont refusées et le domaine du checkout doit être exactement sandbox-checkout.saspay.me.

Après succès de check_saspay, exécuter une seule fois en développement :
`docker compose exec backend python manage.py check_saspay_checkout --create`

Cela crée une session de 1000 XOF au Mali avec une identité fictive, sans paiement, téléphone, réservation ni billet. Le résultat ne révèle ni clé ni URL de paiement. Rechercher la session dans le tableau de bord Sandbox. Ne pas payer cette session. Vérifier son statut avec `--session UUID`. En cas de timeout ou d'erreur, vérifier le tableau de bord avant toute nouvelle création (SasPay ne garantit pas l'idempotence de la création Checkout).

Les tests automatisés utilisent des réponses simulées. Aucun appel réel n'est exécuté dans les tests. Pas de changement de schéma ni de frontend. La gestion des sessions rattachées aux réservations, l'expiration des places, les webhooks, la vérification des montants et l'émission des billets restent à implémenter. Ne pas activer LIVE.

## Réservations — première intégration
Activer explicitement SIRAGO_ENABLE_SASPAY_SANDBOX=1 en local. Une tentative durable par réservation, montant calculé par Django, référence dans metadata et expiration au plus tard à la fin du blocage. En cas de réponse incertaine, aucun retry automatique. Vérification manuelle par API détail + statut, sans webhook ni conversion en billet ou recette. Les places restent bloquées uniquement jusqu’à l’expiration initiale ; un paiement tardif n’émet aucun billet. La simulation locale ne peut plus être utilisée sur une réservation associée à un Checkout. Une demande incertaine nécessite une revue manuelle dans SasPay. Identité fictive envoyée au fournisseur. Les options proposées par le checkout sont celles de SasPay, non limitées aux trois réseaux mobiles. Cette étape ne doit pas être utilisée en production.

## Historique voyageur
Pagination serveur de 10 par défaut, recherche multi-mots sur les réservations du compte, filtres de statut incluant SasPay. Les confirmations restent exclusivement côté serveur : bouton de vérification depuis la liste et les détails, sans nouvelle session ni billet. Un paiement Sandbox confirmé n'est pas une recette réelle. Aucun webhook ni changement de disponibilité à cette étape.


## Émission Sandbox et webhooks
Activation locale explicite : SIRAGO_ENABLE_SASPAY_TICKETS=1, avec DEBUG=1, simulation activée et clé de test. SIRAGO_SASPAY_LOCAL_RETURN=1 ajoute le retour vers http://localhost:8030/app/?view=tickets&booking=... pour les nouvelles sessions (test sur le même PC; acceptation de localhost par SasPay à vérifier).
Après les migrations, démarrer le worker avec docker compose --profile saspay up -d --build saspay-worker. Il consulte les sessions dues toutes les 5 secondes, sans nouvelle création ni débit. Les webhooks authentifiés enregistrent seulement l'identifiant de transaction, rapproché par le worker après lecture de l'API, sans stocker le numéro de téléphone ou le corps brut. Le worker vérifie également les sessions en l'absence de webhook. Un secret distinct SASPAY_SANDBOX_WEBHOOK_SECRET (16 caractères minimum) active l'endpoint POST /api/v1/travel/webhooks/saspay/sandbox/. Configurer dans le tableau de bord Sandbox une URL HTTPS publique dédiée, événement transaction.success, test webhook.test. Localhost n'est pas joignable par SasPay. Ne pas exposer le serveur Django de développement sur Internet. HMAC SHA-256 du timestamp + point + corps brut, tolérance 300 secondes. Documentation : https://docs.saspay.me/api-reference/webhooks.
Les billets émis restent TEST, non valables pour voyager, et utilisent les QR/PDF existants. La transaction distante est unique, l'émission et les notifications sont atomiques. Les montants SasPay sont séparés des simulations locales et des recettes réelles. Le report des billets SasPay est désactivé (pas de simulation de remboursement).
Une confirmation après libération des places devient REVIEW_PAID même si le paiement distant a eu lieu à temps; LATE_PAID si payé après expiration. Ne jamais créer de nouveau paiement pour ces dossiers. Revue manuelle nécessaire. Les anciennes sessions déjà PAID sont revérifiées par le worker, sans récupération automatique de places libérées. Le LIVE reste interdit. Les tests unitaires ne remplacent pas un vrai test de livraison du webhook sur un environnement HTTPS de recette.

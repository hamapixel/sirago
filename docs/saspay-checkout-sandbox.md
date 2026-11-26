# Diagnostic Checkout SasPay

Documentation : https://docs.saspay.me/sandbox et https://docs.saspay.me/api-reference/payments/checkout-create

La clé sk_test_ seule ne garantit pas le mode test. L'API est fixée à https://sandbox-api.saspay.me/api/v1 ; les redirections HTTP sont refusées et le domaine du checkout doit être exactement sandbox-checkout.saspay.me.

Après succès de check_saspay, exécuter une seule fois en développement :
`docker compose exec backend python manage.py check_saspay_checkout --create`

Cela crée une session de 1000 XOF au Mali avec une identité fictive, sans paiement, téléphone, réservation ni billet. Le résultat ne révèle ni clé ni URL de paiement. Rechercher la session dans le tableau de bord Sandbox. Ne pas payer cette session. Vérifier son statut avec `--session UUID`. En cas de timeout ou d'erreur, vérifier le tableau de bord avant toute nouvelle création (SasPay ne garantit pas l'idempotence de la création Checkout).

Les tests automatisés utilisent des réponses simulées. Aucun appel réel n'est exécuté dans les tests. Pas de changement de schéma ni de frontend. La gestion des sessions rattachées aux réservations, l'expiration des places, les webhooks, la vérification des montants et l'émission des billets restent à implémenter. Ne pas activer LIVE.

## Réservations — première intégration
Activer explicitement SIRAGO_ENABLE_SASPAY_SANDBOX=1 en local. Une tentative durable par réservation, montant calculé par Django, référence dans metadata et expiration au plus tard à la fin du blocage. En cas de réponse incertaine, aucun retry automatique. Vérification manuelle par API détail + statut, sans webhook ni conversion en billet ou recette. Les places restent bloquées uniquement jusqu’à l’expiration initiale ; un paiement tardif n’émet aucun billet. La simulation locale ne peut plus être utilisée sur une réservation associée à un Checkout. Une demande incertaine nécessite une revue manuelle dans SasPay. Identité fictive envoyée au fournisseur. Les options proposées par le checkout sont celles de SasPay, non limitées aux trois réseaux mobiles. Cette étape ne doit pas être utilisée en production.

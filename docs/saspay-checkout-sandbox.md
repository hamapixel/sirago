# Diagnostic Checkout SasPay

Documentation : https://docs.saspay.me/sandbox et https://docs.saspay.me/api-reference/payments/checkout-create

La clé sk_test_ seule ne garantit pas le mode test. L'API est fixée à https://sandbox-api.saspay.me/api/v1 ; les redirections HTTP sont refusées et le domaine du checkout doit être exactement sandbox-checkout.saspay.me.

Après succès de check_saspay, exécuter une seule fois en développement :
`docker compose exec backend python manage.py check_saspay_checkout --create`

Cela crée une session de 1000 XOF au Mali avec une identité fictive, sans paiement, téléphone, réservation ni billet. Le résultat ne révèle ni clé ni URL de paiement. Rechercher la session dans le tableau de bord Sandbox. Ne pas payer cette session. Vérifier son statut avec `--session UUID`. En cas de timeout ou d'erreur, vérifier le tableau de bord avant toute nouvelle création (SasPay ne garantit pas l'idempotence de la création Checkout).

Les tests automatisés utilisent des réponses simulées. Aucun appel réel n'est exécuté dans les tests. Pas de changement de schéma ni de frontend. La gestion des sessions rattachées aux réservations, l'expiration des places, les webhooks, la vérification des montants et l'émission des billets restent à implémenter. Ne pas activer LIVE.

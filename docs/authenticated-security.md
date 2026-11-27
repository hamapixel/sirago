# Recette de sécurité authentifiée — phase 08

Scénarios exclusivement locaux, comptes et données fictifs. Ne jamais diriger ces essais vers un fournisseur de paiement ni un site tiers. La suite Django crée une base PostgreSQL de test jetable ; la 2FA est activée par override_settings dans les tests. Pour les utilisateurs compagnie/voyageur, connexion via les vraies API avec CSRF ; tests Superadmin via enrôlement TOTP. Aucun accès à la base de développement pour les essais négatifs.

## Commandes
- docker compose exec backend python manage.py test fleet.test_authenticated_security accounts.test_mfa
- docker compose exec backend python manage.py test
- docker compose exec frontend npm test
- docker compose exec frontend npm run build
- docker compose exec backend python manage.py makemigrations --check --dry-run

## Couverture et limites
Recherches contenant des syntaxes SQL sans élargissement du résultat, permissions par rôle, accès horizontal via IDs, données financières des agents, sessions révoquées, CSRF absent et origine étrangère, tentative d'attribution de privilèges, données HTML stockées et échappement des composants React. Les tests 2FA existants couvrent enrôlement, rejeu, récupération, limitation et révocation. Tests React par rendu statique : pas un test navigateur ou une preuve exhaustive de l'absence de XSS. Aucun scanner actif exécuté par ce commit. Les résultats des tests et de l'audit de l'image de production actualisée doivent être consignés avant déploiement.

## Recette navigateur isolée (reste à réaliser)
Sur une instance locale de recette avec HTTPS de confiance, comptes fictifs A/B voyageur, propriétaire A/B, agents et superadmin MFA. Vérifier via le navigateur que les requêtes authentifiées et les QR TOTP fonctionnent sous la CSP, que les champs de texte contenant des marqueurs HTML restent du texte sans déclencher d'exécution, et qu'une session déconnectée ne recharge pas de données privées depuis un cache. Tester aussi une compagnie suspendue et un agent désactivé. N'exporter aucun cookie, mot de passe, clé MFA ou code de secours dans les rapports. Ne pas désactiver la 2FA pour un scanner.

## Blocage opérationnel à traiter séparément
La route Django Admin native est bloquée en production et en mode MFA. Le SPA affiche encore des liens vers ce back-office et plusieurs modifications (validation de compagnie, assistance) dépendent de Django Admin. Prévoir une voie administrative sécurisée avec MFA, permissions et journalisation avant l'ouverture publique, sans réactiver le formulaire de connexion Django à mot de passe seul.

## Suite
Après les tests authentifiés, test de charge progressif sur une recette séparée, avec trafic de recherche puis parcours authentifiés, limites de concurrence et seuils p95/erreurs. Ne pas tester les paiements réels. Aucun résultat de capacité serveur ne peut être déduit de tests locaux au repos.

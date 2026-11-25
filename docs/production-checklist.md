# SiraGo — contrôles avant production

Le fichier compose.yaml actuel est **réservé au développement** : runserver, Vite, volumes de code. Ne pas le déployer tel quel.

## Configuration Django préparée

Le profil SIRAGO_ENV=production valide les variables avant démarrage. Il refuse DEBUG et la simulation, une clé faible ou de développement, un mot de passe PostgreSQL faible, un hôte wildcard ou une origine CSRF non HTTPS. Exemple de configuration (valeurs fictives, ne jamais copier les secrets du développement) :

- SIRAGO_ENV=production
- DJANGO_DEBUG=0
- SIRAGO_ENABLE_SIMULATED_PAYMENTS=0
- DJANGO_SECRET_KEY : clé aléatoire unique de 50 caractères ou plus
- POSTGRES_PASSWORD : secret aléatoire indépendant
- DJANGO_ALLOWED_HOSTS : domaine(s) public(s) exact(s), séparés par virgule
- DJANGO_CSRF_TRUSTED_ORIGINS : origines HTTPS exactes, séparées par virgule
- DJANGO_TRUST_HTTPS_PROXY=1 uniquement si le proxy de confiance supprime les en-têtes transmis par le client, impose sa propre valeur et si Django est inaccessible directement.

Le profil active cookies Secure, redirection HTTPS, HSTS initial 3600 secondes (sans preload ni sous-domaines), nosniff, politique de référent same-origin et DENY pour les frames. Ne pas activer ce profil sur le compose de développement : la vérification de santé HTTP actuelle doit aussi être adaptée.

## Vérifications restantes, bloquantes avant mise en ligne

1. Construire une image de production WSGI/ASGI, servir le build statique Vite et les fichiers collectstatic; pas de runserver, ni de serveur Vite de développement.
2. Configurer HTTPS et les en-têtes proxy, tester les redirections, les cookies, la vérification de santé et les hôtes rejetés.
3. Configurer un cache partagé pour la limitation de connexion et une protection contre les requêtes abusives au proxy. La limitation actuelle est locale au processus et ne protège pas toutes les routes Django Admin.
4. Sauvegarder puis tester une restauration PostgreSQL. Séparer physiquement les bases et secrets TEST/production. Les réservations TEST historiques ne doivent jamais migrer vers la production.
5. Configurer une surveillance des erreurs et des sauvegardes, revue des accès et MFA administrateur, rotation des secrets.
6. Auditer les dépendances Python et npm, puis exécuter des tests de concurrence et d'isolation intercompagnies. Ce document n'est pas un audit de pénétration.
7. Obtenir la validation SasPay, tester le vrai flux en sandbox (signature webhook, montant, devise, référence, idempotence, expiration et rapprochement), définir commissions et reversements. Aucun paiement réel n'est encore disponible.
8. Exécuter python manage.py check --deploy avec les véritables paramètres de production. Les avertissements HSTS sous-domaines/preload nécessitent une décision explicite selon les domaines, pas une suppression automatique.

Référence : https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

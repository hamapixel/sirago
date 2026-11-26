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
- SIRAGO_REDIS_URL : URL Redis privée dédiée à la production (redis:// ou rediss://), avec authentification si nécessaire. Aucun repli sur un cache local.
- DJANGO_TRUST_HTTPS_PROXY=1 uniquement si le proxy de confiance supprime les en-têtes transmis par le client, impose sa propre valeur et si Django est inaccessible directement.

Le profil active cookies Secure, redirection HTTPS, HSTS initial 3600 secondes (sans preload ni sous-domaines), nosniff, politique de référent same-origin et DENY pour les frames. Ne pas activer ce profil sur le compose de développement : la vérification de santé HTTP actuelle doit aussi être adaptée.

## Vérifications restantes, bloquantes avant mise en ligne

1. Construire une image de production WSGI/ASGI, servir le build statique Vite et les fichiers collectstatic; pas de runserver, ni de serveur Vite de développement.
2. Configurer HTTPS et les en-têtes proxy, tester les redirections, les cookies, la vérification de santé et les hôtes rejetés.
3. Le profil production exige désormais Redis pour partager les compteurs entre processus. Provisionner Redis sur un réseau privé, vérifier la connectivité et les compteurs entre deux workers, surveiller les indisponibilités et protéger les routes au proxy. La limitation applicative utilise REMOTE_ADDR sans faire confiance aux en-têtes clients : derrière Traefik, valider une stratégie de limitation par IP fiable au proxy pour éviter un quota partagé par tous les voyageurs. Django Admin nécessite encore une protection dédiée et MFA.
4. Sauvegarder puis tester une restauration PostgreSQL. Séparer physiquement les bases et secrets TEST/production. Les réservations TEST historiques ne doivent jamais migrer vers la production.
5. Configurer une surveillance des erreurs et des sauvegardes, revue des accès et MFA administrateur, rotation des secrets.
6. Auditer les dépendances Python et npm, puis exécuter des tests de concurrence et d'isolation intercompagnies. Ce document n'est pas un audit de pénétration.
7. Obtenir la validation SasPay, tester le vrai flux en sandbox (signature webhook, montant, devise, référence, idempotence, expiration et rapprochement), définir commissions et reversements. Aucun paiement réel n'est encore disponible.
8. Exécuter python manage.py check --deploy avec les véritables paramètres de production. Les avertissements HSTS sous-domaines/preload nécessitent une décision explicite selon les domaines, pas une suppression automatique.

Référence : https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

Les options SasPay Sandbox, émission TEST et retour local sont refusées au démarrage du profil production lorsqu'elles sont activées. Les tests de configuration ne prouvent pas la disponibilité de Redis ni le comportement multi-processus ; ces vérifications sont requises en préproduction.

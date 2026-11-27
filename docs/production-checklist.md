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

Les paramètres numériques des chemins API (identifiants et indices de billets) sont limités à 19 chiffres et à la plage positive ou nulle du bigint signé. Les valeurs hors plage sont rejetées avant dispatch par une 404. Cela ne remplace ni les vérifications de propriété, ni la validation des corps JSON et paramètres de requête. Les indices de billet commençant à zéro restent valides.

Django Admin utilise un site et un formulaire de connexion dédiés : seuls les superutilisateurs actifs et staff peuvent accéder aux modèles administratifs. Les soumissions de connexion traitées par le formulaire sont limitées à 10 par IP sur 10 minutes, dans un compteur séparé du login SiraGo. Le cache partagé Redis est requis en production ; la protection au proxy et MFA restent nécessaires. Ne pas exposer l'administration sans ces contrôles complémentaires.

## Lot infrastructure 08B
Le fichier compose.production.yaml est désormais disponible. Suivre docs/phase-08b.md ; aucun déploiement effectif ni validation Docker/TLS n'est encore attesté. Le gateway bloque Django Admin par défaut. Les dépendances supplémentaires doivent être auditées après construction.

## Audit des dépendances — 26 novembre 2026
Les résultats locaux transmis indiquent 90 tests ciblés réussis et zéro vulnérabilité npm pour les dépendances de production. pip-audit a signalé 12 entrées (6 identifiants distincts) pour pip 25.0.1. Les deux Dockerfiles backend fixent désormais pip à 26.3, version indiquée disponible dans le rapport. Reconstruire les images et relancer l'audit avant validation; aucun résultat de nouvel audit n'est encore attesté.
Pour auditer uniquement les paquets de l'image sans mélanger ceux du scanner : `docker compose run --rm --no-deps backend sh -c "python -m venv /tmp/security-audit && /tmp/security-audit/bin/pip install --upgrade pip pip-audit && /tmp/security-audit/bin/pip-audit --path /usr/local/lib/python3.12/site-packages"`. Auditer également l'image de production après construction, ainsi que l'ensemble des dépendances npm (y compris le build).

### Revue Bandit, Semgrep et Gitleaks
Rapports locaux du 26/11/2026 : Bandit 39 alertes faibles (36 identifiants de test, 1 valeur explicitement interdite en production, 2 imports d'échappement XML sans parsing), aucune moyenne/haute ; Gitleaks aucune fuite sur 95 commits ; Semgrep trois alertes. Remédiations : html.escape(quote=False) dans les PDF, action checkout fixée au SHA du tag v4, jeton CI en lecture sans persistance, frontend dev non-root et npm ci, allowlist des hôtes côté gateway. Les identifiants fictifs des tests et la comparaison de rejet en production restent visibles aux scanners, sans suppression globale. Reconstruire les images, relancer les scans et vérifier les réponses HTTP. Un nouveau scan et un test de préproduction restent requis.
Pour un volume node_modules de développement existant appartenant à root, après reconstruction de l'image frontend : `docker compose run --rm --no-deps --user root frontend chown -R node:node /app/node_modules`, puis `docker compose up -d frontend`. Cette opération ne touche pas PostgreSQL. Sur Linux, le dossier frontend monté doit également être accessible en écriture à UID 1000 pour le build.

Re-test du 27/11/2026 : 221 tests Django, 156 tests frontend, compilation PWA non-root et audit npm sans alerte. Semgrep : une alerte restante sur `map $host` malgré la liste d'autorisation. Remplacement par des virtual hosts exacts générés au démarrage, serveur par défaut HTTP 400 et Host transmis via le nom de serveur configuré. Nouveau scan et validation Nginx réelle requis.

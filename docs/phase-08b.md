# Phase 08B — Préproduction isolée

## Prérequis bloquants

- Le fichier frontend/package-lock.json est versionné. Les images frontend utilisent npm ci ; conserver le lockfile validé.
- Ne jamais réutiliser les secrets, le volume PostgreSQL ou les données de développement. Aucune donnée TEST ne doit être importée dans une future production.
- Générer trois secrets indépendants : Django (au moins 50 caractères), PostgreSQL et Redis. Utiliser des chaînes hexadécimales aléatoires pour éviter les caractères spéciaux d'URL Redis. Ne jamais committer le fichier de secrets.
- Le profil production désactive les paiements simulés et les options SasPay TEST. Aucun service de paiement live n'est configuré.
- Le backend est sur deux réseaux privés sans accès Internet par défaut. Les futurs appels de paiement nécessiteront une sortie réseau dédiée et contrôlée en 08C.
- Les limites de connexion existantes utilisent REMOTE_ADDR ; tous les appels publics auront potentiellement la même IP de proxy. Protection par IP au niveau Traefik et revue de cette stratégie obligatoires avant exposition. MFA reste à faire.

## Préproduction locale (PowerShell)

Copier .env.production.example vers .env.preproduction, renseigner trois secrets distincts. Exemple de génération : `docker compose exec backend python -c "import secrets; print(secrets.token_hex(32))"` (trois fois). Ne partager aucun résultat.

```powershell
docker compose --env-file .env.preproduction -p sirago-preprod -f compose.production.yaml -f compose.preproduction.local.yaml config --quiet
docker compose --env-file .env.preproduction -p sirago-preprod -f compose.production.yaml -f compose.preproduction.local.yaml up -d --build --wait
docker compose --env-file .env.preproduction -p sirago-preprod -f compose.production.yaml -f compose.preproduction.local.yaml ps -a
curl.exe -i -H "Host: preprod.example.com" -H "X-Forwarded-Proto: https" http://127.0.0.1:8036/api/v1/health/
curl.exe -i -H "Host: preprod.example.com" -H "X-Forwarded-Proto: https" http://127.0.0.1:8036/admin/
docker compose --env-file .env.preproduction -p sirago-preprod -f compose.production.yaml exec backend python manage.py check --deploy
```

Attendus : santé HTTP 200, admin HTTP 404, services db/redis/backend/gateway healthy, migrate terminé avec code 0. Vérifier aussi le HTML de /app/ et /superadmin/, et la redirection Django sans en-tête HTTPS. Le port 8036 est uniquement une sonde locale HTTP : les cookies Secure nécessitent un vrai HTTPS pour la recette de connexion. Ne pas désactiver ces cookies. Ne pas exécuter down -v.

## Coolify / Traefik

1. Créer une application Docker Compose depuis Git, branche feature/phase-08-production-readiness pour la préproduction, chemin /compose.production.yaml. Aucun override local. Ne pas utiliser le compose de développement.
2. Saisir les variables dans Coolify comme secrets d'exécution. Créer un sous-domaine de préproduction choisi par le propriétaire (DNS vers VPS).
3. Associer uniquement gateway au domaine HTTPS sur port 8080 dans Coolify. Aucun port hôte pour db, redis, backend ni gateway. Vérifier les réseaux effectifs après adaptation du compose par Coolify ; seul gateway doit être accessible au proxy. Ne pas connecter les services privés au réseau partagé.
4. Vérifier que Traefik redirige HTTP vers HTTPS, émet un certificat valable et impose X-Forwarded-Proto=https sans faire confiance à des en-têtes externes. Nginx ne fait confiance qu'à cette frontière réseau ; ne jamais publier directement son port sur le VPS.
5. Django Admin est bloqué sur le gateway, y compris les liens de l'interface qui y pointent. Le superadmin SiraGo reste accessible. Préparer un accès privé VPN ou tunnel avec MFA avant d'autoriser Django Admin, sans publier son port.
6. Valider les tests, les cookies HTTPS, PWA, la limitation des requêtes et l'isolation des compagnies. Les avertissements HSTS de check --deploy doivent être examinés sans les masquer. Les valeurs initiales de deux workers / deux threads sont un point de départ, pas un test de charge.

Docs officielles : https://coolify.io/docs/applications/builds/docker-compose ; https://coolify.io/docs/core/networking/domains ; https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

## Sauvegardes / surveillance

Le service backup (image dédiée sans montage du code source) réalise un pg_dump personnalisé après les migrations et le démarrage sain de Django, puis toutes les 24 h, vérifie le catalogue pg_restore et conserve environ 14 jours dans un volume dédié. Une vérification de catalogue ne prouve pas une restauration complète. Contrôler les logs et copier les sauvegardes chiffrées hors VPS sur un stockage indépendant. Le volume local seul ne protège pas d'une panne VPS. Tester une restauration dans une base jetable séparée (jamais dans la base active), vérifier les lignes et l'accès à l'application. Configurer alertes d'échec et d'âge du dernier dump avant lancement.

Uptime Kuma : moniteur HTTP(s) sur https://<domaine-preprod>/api/v1/health/ (200 attendu, contrôle PostgreSQL + Redis), intervalle 60 s, 2 échecs avant alerte. Ajouter un moniteur HTTPS sur la page d'accueil et vérifier l'expiration TLS. Ne pas exposer les bases pour les surveiller. Les alertes et le monitor ne sont pas encore créés sur le VPS.

## Critères d'acceptation

Build reproductible, conteneurs sains, redémarrage sans perte de données, restauration testée, TLS et proxy contrôlés, audit des nouvelles dépendances, aucune exposition DB/Redis, paiements réels inactifs. Ce lot ne vaut ni déploiement effectif ni autorisation de mise en service.

## Web Push (optionnel)
Activer seulement après recette HTTPS. Générer les clés une seule fois avec `python manage.py generate_vapid`, conserver la clé privée uniquement dans les secrets du worker, renseigner SIRAGO_PUSH_ENABLED=1, SIRAGO_VAPID_PUBLIC_KEY et SIRAGO_VAPID_SUBJECT=mailto:adresse-technique. Ajouter compose.push.yaml au compose production (Coolify : vérifier la prise en charge de plusieurs fichiers avant activation). Le worker seul a un réseau de sortie dédié ; limiter en complément les sorties HTTPS aux fournisseurs autorisés. Pas de port publié. Abonnement volontaire lié à la session, au maximum cinq appareils, supprimé à la déconnexion. Alertes génériques, sans données personnelles, expiration du travail après une heure, TTL 5 minutes. Livraison non garantie (réseau, autorisation, système). Tester Android et iPhone installé sur écran d’accueil, avec appareil verrouillé, refus puis désactivation, changement de compte, erreurs fournisseur et redémarrage du worker. Aucun paiement réel activé.

Les notifications push utilisent des messages fixes selon le type (réservation, billet, embarquement, départ, assistance), avec le logo SiraGo et un pictogramme dans le titre. Le rendu final des icônes dépend du système. Aucun détail privé n'est transmis ; les simulations restent signalées. Un scan seul ne notifie pas : seule la validation d'un nouveau passager crée l'événement, pour le compte ayant réservé et le responsable de compagnie. Le contrôle réel reste à intégrer avec les paiements réels.

### Contrôle des hôtes Nginx
Le gateway génère une liste exacte à partir de DJANGO_ALLOWED_HOSTS au démarrage. Un hôte absent ou non autorisé doit donner HTTP 400, y compris sur les pages statiques. Sa sonde interne utilise le premier domaine configuré. Vérifier avec `curl.exe -i -H "Host: invalid.example.net" http://127.0.0.1:8036/` et les deux sondes autorisées ci-dessus. Ne pas publier directement le gateway sur le VPS.

Chaque domaine public validé dispose désormais d'un bloc server distinct, sans wildcard. Le backend reçoit `$server_name` (nom littéral configuré dans ce bloc) et non l'en-tête Host brut. Le serveur par défaut refuse les hôtes inconnus. Tester chaque domaine autorisé et les hôtes inconnus ; le résultat du scan ne remplace pas ces tests HTTP.

### Windows / scripts Linux
Les scripts shell sont forcés en LF par .gitattributes. Les Dockerfiles gateway et backup normalisent également les CRLF résiduels et vérifient la syntaxe avec sh -n au build. Premier démarrage local : backend, migrations, Redis et PostgreSQL OK ; gateway code 127 et backup code 2. La cause CRLF est une hypothèse à confirmer par les logs. Reconstruire uniquement ces deux images et vérifier leur démarrage, sans supprimer les volumes.

### Durcissement après ZAP baseline
Le gateway définit CSP (scripts et connexions same-origin, pas d'unsafe-eval ni de JS inline ; CSS inline maintenu pour splash/Swiper/React), Permissions-Policy (caméra same-origin conservée), COOP/CORP same-origin et COEP require-corp. Les intégrations externes incorporées devront être revues avant activation ; les liens externes de paiement restent des navigations de premier niveau. HSTS initial 3600 secondes uniquement via proxy HTTPS de confiance ; les en-têtes Django redondants sont retirés à la frontière Nginx. HTML shell no-store, service worker et manifeste à revalider, ressources fingerprintées publiques conservées en cache. Les politiques de cache de l'API restent celles de Django. Robots/sitemap absents retournent 404. La recette navigateur HTTPS est obligatoire : carrousel, authentification, QR caméra/import, téléchargements PDF, paiement TEST, installation, push et hors ligne. Le scan HTTP passif ne suffit pas pour valider les fonctionnalités ni l'isolation cross-origin en navigateur.

### Deuxième remédiation Trivy — images candidates
Gateway : paquet signé Alpine 3.23 nginx >=1.28.3-r8, configuration principale explicite, génération des virtual hosts inchangée et nginx -t au build puis au démarrage. Backup : gosu inutilisé retiré (entrypoint propre). DB : même image officielle PostgreSQL 17 et mises à jour apk, remplacement du binaire gosu par su-exec pour la baisse de privilèges de l'entrypoint officiel, vérification du contrat et de l'UID au build. Redis : même version 7.4 et Alpine 3.22 avec apk upgrade. Les images db et redis sont désormais construites par Compose, non tirées directement. Avant de remplacer les conteneurs existants : scanner les images candidates et tester une initialisation PostgreSQL neuve, la restauration et le fonctionnement sur un projet Compose distinct. Ne pas réutiliser les volumes de la préproduction actuelle pour cette recette. Aucun changement du backend Python dans ce lot ; vérifier la provenance du signalement setuptools 70.3.0 et les CVE Debian sans correctif. Ne pas masquer les alertes.

### Activation Superadmin 2FA
Production : obligatoire et non désactivable par variable d'environnement. Après migration 0009, créer un superuser si nécessaire puis lancer dans un terminal privé : python manage.py admin_mfa_activation IDENTIFIANT. Se connecter avec le mot de passe, saisir le code privé fourni, scanner le QR dans une application TOTP, confirmer avec un code valide, garder les huit codes de secours hors ligne. Ne jamais partager le code opérateur, le QR, la clé ou les codes de secours. Pour réinitialiser après vérification d'identité par l'opérateur : même commande avec --reset ; toutes les anciennes sessions MFA sont révoquées. En local, ajouter SIRAGO_ADMIN_MFA_REQUIRED=1 à .env (non versionné) et recréer le backend. Tester avec HTTPS réel avant la mise en ligne ; les autres rôles restent inchangés.

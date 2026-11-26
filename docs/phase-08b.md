# Phase 08B — Préproduction isolée

## Prérequis bloquants

- Versionner le frontend/package-lock.json réellement validé après npm install et npm ci. Le Dockerfile production exige ce fichier et refuse de construire sans lui.
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

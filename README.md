# SiraGo
Ka billet ta fô i sigi yorola. — Propulsé par BTDIGIT.

## Phase 01 — socle de développement
Prérequis : Docker Desktop démarré, Docker Compose v2.
```powershell
Copy-Item .env.example .env
docker compose up -d --build
docker compose ps
```
Accueil : http://localhost:8030/ ; santé API : http://localhost:8030/api/v1/health/
Tests : `docker compose exec backend python manage.py test` et `docker compose exec frontend npm test`.
Build : `docker compose exec frontend npm run build`.
Admin local : `docker compose exec backend python manage.py createsuperuser`, puis /admin/.
Les exemples de trajets et compagnies sont fictifs. L'inscription, la réservation et le paiement ne sont pas encore actifs. PWA testable après build avec `npm run preview -- --host 0.0.0.0` (port 8030 configuré).
Ne pas déployer cet environnement de développement en production. Les secrets et paramètres HTTPS devront être configurés séparément.

# Phase 08 — Préparation à la production

Base validée : phase 07, PR #7, commit de fusion 6d07287d942fa5c0aaed7f649a03f7988d34ff3d. Validation locale : 175 tests Django, 131 tests Vitest, aucune migration manquante et build PWA réussi.

Cette phase ne déploie pas encore SiraGo et n'autorise ni encaissement ni reversement LIVE. Conserver le développement local et les tests Sandbox isolés. Ne jamais transférer les réservations TEST vers une base de production.

## 08A — Audit et durcissement (premier lot)
- [ ] Inventorier les endpoints publics, authentifiés, agents, compagnies et superadmin ; vérifier permissions, CSRF, isolation intercompagnies, IDOR, validation des entrées et limites de pagination.
- [ ] Tester concurrence des réservations, expiration des blocages, émission et embarquement idempotents, et séparation TEST/LIVE.
- [ ] Vérifier le profil config/production.py ; cache partagé et limitation des abus, journalisation sans secrets, protection Django Admin, revue des accès et MFA.
  - Premier lot : profil production exigeant Redis, validation de l'URL sans divulgation de secrets, refus explicite des options SasPay TEST ; tests unitaires ajoutés. Le compose local reste inchangé. Validation locale : 179 tests Django, 131 Vitest, build et migrations OK ; CI verte sur bc48d61. Provisionnement Redis, test multi-worker, limitation au proxy et MFA restent ouverts.
  - Deuxième lot : bornage des paramètres numériques des routes API avant dispatch, tests de routage et HTTP, tests PostgreSQL de concurrence (rejeu simultané et dernière place Premium). L'audit des champs JSON, permissions et entrées hors URL continue ; la CI de ce lot doit être validée.
- [ ] Auditer dépendances Python et npm, documenter les correctifs et exécuter la suite de tests.
- [ ] Vérifier la CI ; ne pas considérer les tests seuls comme un audit de pénétration.

## 08B — Infrastructure de préproduction
- [ ] Compose dédié à la production : serveur WSGI/ASGI, frontend Vite compilé, collectstatic, santé des services, volumes persistants et réseau privé PostgreSQL.
- [ ] HTTPS via Coolify/Traefik, proxy de confiance, cookies, en-têtes et domaines explicites ; aucun serveur de développement exposé.
- [ ] Environnement de préproduction distinct, secrets injectés côté serveur. Aucun secret dans Git, le frontend ou les logs.
- [ ] Vérifier manage.py check --deploy, démarrage, arrêt, migrations et retour arrière.

## 08C — SasPay et finances
- [ ] Confirmer auprès de SasPay l'éligibilité LIVE, les moyens de paiement, frais, remboursements, litiges et modalités de collecte/reversement pour les compagnies.
- [ ] Vérifier signatures et rejeu des webhooks, rapprochement API indépendant, montant/devise/référence et états en attente/expirés/confirmés ; aucun billet sur simple redirection navigateur.
- [ ] Séparer clés, URL, données et indicateurs TEST/LIVE ; prévoir idempotence, journal financier, traitement des paiements tardifs et remboursements.
- [ ] Définir par écrit qui supporte les frais et comment commissions et reversements sont calculés ; aucun transfert automatique par défaut.
- [ ] Tester l'ensemble en Sandbox puis obtenir validation explicite avant toute activation LIVE.

## 08D — Données et exploitation
- [ ] Sauvegarde PostgreSQL automatisée et chiffrée hors VPS, rétention définie, restauration sur base isolée et vérification des données restaurées.
- [ ] Mesurer temps de réponse, requêtes SQL, charge concurrente et démarrage PWA sur réseau mobile ; optimiser selon mesures, pas uniquement taille du bundle.
- [ ] Mettre en place suivi disponibilité (Uptime Kuma ou équivalent), alertes erreurs, sauvegardes et worker, rotation des logs et procédures d'incident.

## 08E — Recette et lancement
- [ ] Recette mobile 320–430 px, tablette, PC ; installation PWA Android/iPhone/PC, scanner caméra HTTPS, PDF et navigation tactile.
- [ ] Valider avec une compagnie pilote : tarifs, réservations, embarquement, manifeste, assistance, annulations et rapport financier.
- [ ] Vérifier conditions d'utilisation, confidentialité, obligations applicables et accords partenaires avant lancement.
- [ ] Autorisation explicite du propriétaire avant domaine public, paiements réels ou reversements réels.

## Critères de sortie
CI et tests locaux verts, aucune migration manquante, build réussi, risques critiques corrigés, sauvegarde restaurée, recette préproduction validée, modalités financières confirmées et activation LIVE autorisée séparément.

Voir aussi [production-checklist.md](production-checklist.md). Le compose.yaml existant reste un compose de développement ; ne pas le déployer tel quel. Ce document est un plan de travail, pas une attestation de sécurité ou de conformité.

### Correctifs de recette 08A
- Connexion directe des superutilisateurs par nom d'utilisateur Django si aucun téléphone/email ne correspond ; les comptes ordinaires gardent leurs identifiants habituels. Vérification du mot de passe, CSRF et limitation inchangées. En cas de collision, téléphone/email prioritaire ; utiliser un nom d'utilisateur administratif distinct.
- Tests de concurrence : recréer Bamako et Sikasso dans le fixture après flush PostgreSQL ; vérifier HTTP 200 avant lecture du total. Aucune assertion de capacité supprimée.
- Quatre tests d'authentification supplémentaires. Validation locale et CI à confirmer.

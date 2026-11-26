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
- Recette UI Superadmin : sidebar bureau rétractable, tiroir mobile modal accessible, tableau de bord compact et profil personnel. Les identifiants et droits restent en lecture seule ; changement de mot de passe avec vérification du mot de passe actuel, CSRF, limitation et isolation du compte. Les espaces voyageur/compagnie restent inchangés. Tests locaux précédents : 190 Django et 131 Vitest réussis ; nouveaux tests et recette visuelle mobile à valider.
- Validation frontend du correctif db87799 : 134 tests réussis, build TypeScript/Vite et PWA OK ; CI push et pull_request réussies. La recette visuelle reste distincte des tests automatisés.
- Durcissement Django Admin : accès réservé aux comptes superutilisateurs actifs et staff, y compris pour les sessions existantes ; limitation de 10 soumissions de connexion valides par IP sur 10 minutes via le cache Django, sans confiance dans X-Forwarded-For. Protection CSRF conservée. MFA et limitation au proxy restent à configurer ; nouveaux tests à valider.

### Audit des dépendances — 26 novembre 2026
- Base locale validée : 199 tests Django, 134 Vitest, aucune migration manquante ; CI d9a953c réussie.
- npm audit local : 8 vulnérabilités (5 modérées, 3 critiques), concernant Swiper, Vitest/mocker, Tinypool, glob et minimatch. pip check sans conflit ; pip-audit : 5 vulnérabilités DRF 3.16.1.
- Remédiation ciblée : Swiper >=12.1.2 dans la série 12 (GHSA-hmx5-qpq5-p643), Vitest >=5.1.2 dans la série 5 et Vite >=6.4.6 dans la série 6, DRF >=3.18.2 dans la série 3.18. Vitest 5 exige Node >=22.12 et Vite >=6.4 ; vérifier les versions effectives et la compatibilité des tests. Ne pas utiliser npm audit fix --force.
- Le lockfile frontend est actuellement non suivi sur le poste local. Régénérer avec npm install, puis traiter glob/minimatch via npm audit fix --package-lock-only (sans --force), npm ci, npm audit et npm audit --omit=dev. Vérifier les changements du manifeste et du lockfile, tester l'ensemble et les carrousels sur mobile avant de versionner le lockfile puis utiliser npm ci dans Docker/CI. Ne pas écraser le fichier local existant depuis GitHub.
- Refaire pip check et pip-audit sur les versions réellement installées après reconstruction. Aucun audit propre ni compatibilité des nouvelles versions n'est attesté par ce commit seul. Production bloquée tant que les vulnérabilités critiques ne sont pas corrigées et les contrôles restants ne sont pas validés.

### Recette avant 08B
- Audit local après 5262ce3 : zéro vulnérabilité critique npm, zéro vulnérabilité npm hors dev et zéro vulnérabilité Python connue ; 4 alertes modérées de construction PWA restent ouvertes. 199 Django, 134 Vitest, build PWA et migrations OK.
- Styles de trajet chargés au démarrage, historique et détails de réservation harmonisés, billet écran compact (340 px) et PDF A6 (105 × 148 mm), nom de compagnie, ville du siège et car issus des données existantes. Pas de coordonnées privées ni de faux logos. QR et règles TEST inchangés ; annexe collective paginée conservée. Recette visuelle et scan du PDF à confirmer.

- Finitions UI : cartes compactes, graphiques dynamiques basés sur les agrégats de la compagnie, PDF collectif sur une page pour deux noms courts, identité visuelle logo/bannière téléversable (normalisation raster côté serveur, droits propriétaire, migration 0007). Sélecteur FR/EN/BM avec préférence locale et dictionnaire initial des navigations et libellés principaux ; traduction exhaustive des erreurs serveur, PDF, messages et formulaires secondaires encore à compléter, bambara à relire avec des locuteurs. Les avertissements de simulation restent explicites. Recette visuelle et CI à confirmer.

- Recette locale d9b2d33 : 203 Django, 138 Vitest, compilation et PWA réussies. Finition ciblée : départs en grille compacte, disponibilité visible pour les départs publiés à venir, capacités du car protégées côté serveur et signalées dans le formulaire, modification du chauffeur conservée. Nouveau test de non-régression du verrou. Aucun changement de schéma.

- Validation bf08877 : 204 tests Django, 138 Vitest, build et migrations OK. Manifeste premium (écran et PDF A4) ajouté, permissions et avertissements de simulation conservés.
- 08B : compose de préproduction dédié, images Gunicorn/Nginx, migrations séparées, Redis/PostgreSQL sur réseau interne, santé DB/cache et sauvegarde quotidienne. Lockfile validé à versionner avant build ; TLS, restauration, MFA, protection proxy et Uptime Kuma restent à vérifier/configurer. Voir docs/phase-08b.md.

- Notifications : centre partagé pour les trois rôles, badge et rafraîchissement sur retour au premier plan, événements Superadmin (inscription compagnie, assistance), Web Push opt-in par session avec file persistante et worker isolé. Migration 0008. VAPID, HTTPS et recette appareils réels indispensables ; push désactivé par défaut. Aucun SMS.

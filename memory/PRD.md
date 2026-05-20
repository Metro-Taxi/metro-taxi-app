# Métro-Taxi - Product Requirements Document

## Original Problem Statement
Plateforme web + mobile "Métro-Taxi" pour mettre en relation des usagers abonnés et des chauffeurs VTC. Application full-stack avec inscriptions, abonnements, PWA installable, internationalisation (16 langues), interface d'administration avec traçabilité usagers, paiements sécurisés.

## User Personas
1. **Usagers** : Personnes souhaitant des trajets illimités via abonnement
2. **Chauffeurs VTC** : Conducteurs professionnels recevant des courses et des virements
3. **Administrateur** : Gestion des utilisateurs, chauffeurs, régions, revenus, conformité RGPD

## Core Requirements
- Inscriptions usagers/chauffeurs avec validation
- Système d'abonnements (24h, 1 semaine, 1 mois) par région
- Paiements Stripe (en transition vers Crédit Agricole)
- Tableau de bord temps réel avec géolocalisation (Leaflet/OpenStreetMap)
- PWA installable avec service worker
- Internationalisation complète (16 langues)
- Système d'e-mails transactionnels (Resend)
- Export PDF des données admin
- Conformité RGPD

---

## What's Been Implemented

### Session 2026-05-20 (P0 Sécurité admin zombie + Refonte plan hebdomadaire 19,99€)
- [x] **🔴 P0 — Suppression compte admin zombie (faille critique)**
  - Diagnostic : 2 admins en DB prod, seul `contact@metro-taxi.com` synchronisé par le seed `.env`, l'autre `admin-mt@metro-taxi.com` (créé le 03/05/2026) gardait un vieux hash bcrypt jamais sync → backdoor potentielle
  - Action prod : `db.admins.delete_many({'email': {'$ne': 'contact@metro-taxi.com'}})` + `db.admin_otps.delete_many({})`
  - `backend/server.py` `create_default_admin` : auto-purge au startup de TOUT compte admin (collections `admins` ET `users`) dont l'email ≠ `ADMIN_EMAIL` du `.env`. Invalidation auto des OTPs en cours à chaque restart.
  - `backend/server.py` `_initiate_admin_otp` : throttle 3 emails OTP max par IP / 15 min via `_otp_email_throttle` (anti email-bombing) → 429 sinon
  - `memory/deploy/nginx-security-patch-2026-05-20-v3.conf` : rate-limit Nginx 5 logins/15min + 10 verify-otp/5min (sans blacklist IP, IP 37.67.127.14 identifiée comme fausse alerte — IP perso fondateur)

- [x] **🟠 P1 — Refonte plan hebdomadaire à 19,99€ (60% du Navigo Semaine 32,40€)**
  - **Limites :** 15 trajets / 7 jours + max 3 trajets / 24h glissant (anti-abus, push vers le mois illimité)
  - Backend : `SUBSCRIPTION_PLANS["1week"]` = {price 19.99, max_rides_per_period 15, max_rides_per_day 3} dans `server.py` + `config.py` + `utils/helpers.py`. `REGIONAL_PRICING` aligné pour 8 régions (paris/lyon 19,99€ ; london £34.99-£69.99 ; madrid 14,99€-20,99€).
  - `backend/routes/admin.py` (POST `/api/admin/ride-requests`) : ajout d'une seconde branche de plafond pour `1week` : compteur hebdomadaire + compteur 24h glissant → 429 si dépassement
  - Frontend : Subscription.js, SalesTerms.jsx (CGV), Landing.js (3 cartes France + 3 zones Madrid + 3 zones London), Profile.js, AdminDashboard.js (dropdown gift) — restauration de la 3ème carte hebdo
  - i18n : 8 fichiers (`fr/en/en-GB/es/de/it/nl/pt.json`) — ajout de `pricing.limits.{day,week,month}` pour afficher les limites correctement par plan (24h → "5 trajets max", semaine → "15 trajets sur 7j (3/jour)", mois → "Trajets illimités") **protection juridique anti-DGCCRF**

- [x] **🟢 P2 — Page `/subscription` enrichie**
  - Badge "Subscribed" du UserDashboard rendu cliquable → navigation directe vers `/subscription`
  - Carte "Mon abonnement actuel" sur `/subscription` avec compteur jours/heures restants + bouton renouvellement conditionnel (≤ 48h avant expiration)
  - Système 48h/24h/jour-J déjà en place (`check_and_notify_expiring_subscriptions` cron + emails Resend) — pas de modif requise


### Session 2026-05-15 (P0 Rentabilité algo + P1 Patron VTC + P1 Email perso admin)
- [x] **🔴 P0 — Seuil de rentabilité par type de véhicule**
  - `backend/utils/algorithm_config.py` : `DEFAULT_VEHICLE_FILL_THRESHOLDS` (berline 3/4/4, monospace 4/5/5, van 5/7/7), `DEFAULT_QUEUE_TIMEOUT_MINUTES=12`, `normalize_vehicle_type()`, `assess_dispatch_profitability()`, cache `get_vehicle_thresholds()` Mongo
  - `backend/routes/admin.py` : GET/PUT `/api/admin/algorithm-config` étendus avec `vehicle_thresholds` + `queue_timeout_minutes`. Validation stricte typo véhicule → 400. Reset purge aussi le cache véhicules.
  - Nouveau endpoint `GET /api/admin/algorithm/avg-fill?days=7` : remplissage moyen / chauffeur, fleet_summary, classement santé (excellent/ok/below_threshold/no_data)
  - Nouveau endpoint `POST /api/admin/algorithm/check-profitability` : simulation pour debug admin
  - Frontend `AlgorithmConfigTab.js` : section "Seuils de rentabilité" éditable (berline/monospace/van + queue_timeout), section "Performance flotte" (composant `FleetFillPanel.js`)
  - Tests Pytest : `tests/test_profitability_thresholds.py` (24 tests) + `tests/test_iteration14_admin_apis.py` (24 tests d'intégration via le testing agent) → **48/48 ✅**

- [x] **🟠 P1 — Page Patron VTC (B2B partenariats flotte)**
  - Nouveau router `backend/routes/fleet_partnerships.py` : POST `/api/fleet-partnerships/apply` (public, anti-doublon 409), GET `/api/admin/fleet-partnerships`, POST `/api/admin/fleet-partnerships/{id}/status`
  - Emails `services/emails.py` : `send_fleet_partnership_alert` (vers fondateur), `send_fleet_partnership_confirmation` (vers patron VTC)
  - Frontend `pages/PatronVTC.js` : page hero + bénéfices + formulaire (nom, société, email, tél, taille flotte, ville, message)
  - Routes `/patron-vtc`, `/patron`, `/b2b` enregistrées dans App.js

- [x] **🟠 P1 — Bouton "Envoyer email perso" dans la fiche chauffeur admin**
  - Email service `send_admin_personal_email()` (texte libre vers chauffeur via Resend)
  - Endpoint `POST /api/admin/drivers/{id}/send-email` (auth admin, validation subject 2-200 / body 5-10000, audit dans `admin_email_logs`)
  - Endpoint `GET /api/admin/email-logs?limit=50` (lecture audit)
  - Frontend `DriverCardDialog.js` : bouton "Envoyer email perso" + sous-Dialog avec sujet/signature/corps + envoi async


### Session 2026-05-12 (Algorithme transbordement adaptatif + Plafond 24h)
- [x] **🧠 Algorithme transbordement adaptatif par zone** (segments dynamiques)
  - Module `backend/utils/zone_detector.py` : détection hybride code postal + GPS fallback (paris_intra / banlieue / grande_couronne / hors_zone)
  - Module `backend/utils/algorithm_config.py` : config par zone (Paris 3-4km / Banlieue 5-7km / GC 8-12km / Nuit 10-15km)
  - `calculate_multi_transfer_route()` dans `server.py` mis à jour — utilise désormais la config adaptive selon la zone du point de départ + l'heure (jour/nuit Europe/Paris avec DST)
- [x] **🖥️ API panneau admin algorithme** (`/api/admin/algorithm-config`)
  - `GET` — récupère defaults + overrides + effective config
  - `PUT` — override per-zone + per-key avec validation stricte des clés
  - `POST /reset` — réinitialise aux valeurs par défaut
  - Cache mémoire 30s pour éviter de spammer MongoDB
- [x] **🚦 Plafond abonnement 24h = 5 trajets max** (`/api/rides/request`)
  - Retourne 429 quand le plafond est atteint
  - Compte les trajets sur la période courante de l'abonnement (rejected/cancelled exclus)
  - Champ `max_rides_per_period` ajouté à `SUBSCRIPTION_PLANS["24h"]`
- [x] **🧪 Tests pytest 27/27 PASSED**
  - `tests/test_adaptive_algorithm.py` — 23 tests (CP, GPS, hybride, nuit DST, config)
  - `tests/test_subscription_24h_cap.py` — 4 tests d'intégration (blocage, allow, rejected non-comptés, 1month no-cap)
  - `tests/conftest.py` + `pytest.ini` — fix event loop pour Motor/async
- [x] **🐛 Bug pré-existant fixé** : `create_ride_request` retournait `_id` ObjectId non-sérialisable
- [x] **⚖️ Short list avocats** consolidée dans ROADMAP.md (Parallel Avocats, INFLUXIO, Mochon, Goldwin, Hashtag, Swim Legal)


### Session 2026-05-07 jour 3 (Validation marché chauffeurs + Premier engagement organique massif)
- [x] **🔥 13 chauffeurs VTC pros répondent** à une question soft sur la Page Métro-Taxi (265 vues / 80 commentaires)
  - Médiane confirmée : 220 km/jour pour vivre du métier
  - Stéphane Pes : "1€/km minimum = seuil de survie" → Métro-Taxi à 1,50€/km = +50% au-dessus du marché
  - 13 réponses personnalisées préparées (Stéphane, Rodrigue, Flow, PassionateDragon, Mustapha, etc.) pour conversion en MP
- [x] **🖨️ 100 flyers A6 imprimés** (Copy Top Opéra, papier satiné 170g, 81,70€) — prêts pour distribution CDG vendredi 8 mai
- [x] **📨 Mail relance Agnès** envoyé avec proposition code parrainage (3 amis = 1 mois offert)
- [x] **🛠️ Endpoint `/api/marketing/download/`** créé pour bypasser PWA scope sur fichiers vidéos/flyers
- [x] **🔗 Routes courtes `/chauffeur` et `/usager`** créées dans App.js pour campagnes marketing
- [x] **🎨 Bouton "Devenir chauffeur"** retravaillé en blanc plein contrasté (vs bordure transparente)
- [x] **📊 Apprentissage clé** : les chauffeurs VTC pros NE convertissent PAS via TikTok/Insta. Recrutement = TERRAIN (CDG, gares) + DM directs

### Session 2026-05-05 (LANCEMENT MARKETING — 1ère inscription LIVE 🏆)
- [x] **🎬 3 vidéos campagne chauffeurs produites avec Sora 2 + voix off TTS française**
  - Coupe Sora à 7s pour éliminer le faux logo halluciné
  - Outro fond noir + logo officiel Métro-Taxi + URL metro-taxi.com
  - Voix masculine grave (onyx HD) — script sans concurrence citée
  - Fichiers : `/app/marketing_assets/final/video_1_chiffre_qui_fait_mal_FINAL.mp4` (et videos 2, 3)
  - Durée 13-16s, format vertical 9:16, prêt TikTok/Insta/Facebook
- [x] **📤 Campagne lancée sur 4 plateformes** (TikTok, Instagram, Facebook personnel, 3 Groupes Facebook VTC)
- [x] **🏆 1ère inscription réelle confirmée** : AGNÈS MAYILI (mayiliagnes@yahoo.fr) — usager via TikTok
- [x] **📊 1 311 personnes touchées en 1 journée** (vs 30 vues/jour précédent)
- [x] **📋 Stratégie hashtags 2026 validée** : 5 hashtags max — `#chauffeurvtc #vtcparis #pourtoi #iledefrance #fyp`
- [x] **🛠️ Scripts marketing dans `/app/scripts/`** :
  - `generate_marketing_assets.py` (TTS voix off)
  - `generate_sora_video1.py` / `generate_sora_videos_2_3.py` (génération Sora)
  - `montage_final_v2.py` (fusion ffmpeg : Sora cut 7s + outro logo + voix off)

### Session 2026-02-04 (Déploiement sécurité 2FA admin sur VPS — SUCCÈS LIVE)
- [x] **🔒 Faille critique sécurité corrigée** : suppression des identifiants admin hardcodés dans `Login.js`
- [x] **🔐 Système 2FA OTP par email implémenté** (`server.py` + `services/emails.py`)
  - Endpoint `POST /api/auth/login` retourne `{otp_required: true}` pour les admins
  - Endpoint `POST /api/auth/admin/verify-otp` valide le code 6 chiffres (TTL 5 min, max 5 tentatives)
  - Collection MongoDB `admin_otps` (auto-créée)
- [x] **📧 Migration email admin** : `admin-mt@metro-taxi.com` → `contact@metro-taxi.com` (ancien email banni par Resend suppression list)
- [x] **🚀 DÉPLOIEMENT VPS RÉUSSI** : `git pull` + `sed -i .env` + `pm2 restart all --update-env` sur VPS Hostinger
- [x] **✅ Test live validé** : API répond `{"otp_required":true}`, OTP envoyé par mail, admin peut se connecter
- [x] **📈 Premiers utilisateurs réels inscrits** suite au partage WhatsApp — confirmations visibles dans le panneau admin
- [x] **🛡️ Manifest PWA** : ajout `id` stable pour éviter alertes Google Play Protect
- [x] **📄 Documents INPI générés** : `INPI_FORBIDDEN_TERMS.pdf`, `SECURITY_BRAND_GUIDELINES.pdf`, `INPI_ALGORITHME_TRANSBORDEMENT.pdf`

### Session 2026-02 (urgence sécurité brevet + bug voix multilingue)
- [x] **🔴 BUG CRITIQUE (1000+ vues impactées) corrigé : voix Landing Page bloquée en anglais**
  - Cause : `Landing.js` chargeait des fichiers MP3 statiques `/audio/voiceover/voiceover_*.mp3` depuis `frontend/build/` mais ces fichiers ne sont pas garantis présents après `yarn build` sur le VPS (le backend les écrit dans `frontend/public/` après le build)
  - Fix : `playVoiceover()` appelle maintenant directement `POST /api/tts/voiceover` avec le langCode → backend retourne MP3 en streaming (cache backend ou regénération à la volée)
  - Service Worker bumpé à v15 (audio-cache v7) pour invalider les anciens MP3 cachés
  - Validation : test 3 langues (FR/ES/DE) → 200 OK audio/mpeg ✅
- [x] **Reformulation TOTALE des 16 scripts vocaux TTS** (`/app/backend/routes/tts.py`)
  - Phrase technique "changez de véhicule en route" remplacée par **"Voyagez librement à travers toute la ville, sans contrainte, sans limite, jusqu'où vous voulez"** (Option 4) dans les 16 langues
  - 3 voix critiques (fr, en, es) régénérées et validées (HTTP 200)
- [x] **🚨 FUITE CRITIQUE corrigée dans le chatbot IA** (`/app/backend/routes/support_chat.py`)
  - System prompt réécrit + directive d'interdiction multilingue ajoutée
  - Test live validé : le chatbot répond "réseau intelligent qui vous emmène partout" sans révéler le mécanisme
- [x] **Nettoyage chirurgical des 16 fichiers i18n locales JSON**
  - 13 chemins UI ciblés (common.transfers, dashboard.user.transferSuggestions, drivers.app.transfersDesc, cgu.service5, subscription.plans.{day,week,month}.feature3, etc.)
  - **182 valeurs remplacées** par termes neutres ("itinéraires", "routes", "rutas", "Strecken"…)
  - Stripe payouts (driverEarnings.transferred / payoutDate) intentionnellement intacts (virements bancaires légitimes)
  - 16 JSON validés (parsing OK), screenshot Landing OK
- [x] **Création du fichier `/app/SECURITY_BRAND_GUIDELINES.md`** — référentiel complet anti-fuite IP
  - 40+ termes interdits dans 16 langues
  - Distinction texte public (à nettoyer) vs code interne (OK)
  - Script Python de scan automatique pré-déploiement
  - Statut nettoyage global + checklist

### Session 2025-04-20
- [x] **Chatbot IA Support** : page /support avec assistant GPT-4.1-mini
  - Répond en 16 langues automatiquement
  - Connaît tous les tarifs, zones, fonctionnement de Métro-Taxi
  - Questions fréquentes en raccourcis
  - Escalade vers email contact@metro-taxi.com si nécessaire
  - Bouton AIDE redirige vers /support

### Session 2025-04-12 (Refactoring Phase 1)
- [x] **Extraction emails → `services/emails.py`** : 4 fonctions email (vérification, confirmation abo, notification paiement, rappel expiration, cadeau) extraites de `server.py` (~514 lignes supprimées, 5940 → 5426)

### Session 2025-04-12
- [x] **Correction bug internationalisation anglais (US + GB)** :
  - Refonte complète de la configuration i18n (`/app/frontend/src/i18n/index.js`)
  - Suppression du plugin `LanguageDetector` (causait des résolutions de langue incorrectes)
  - Remplacement par une détection explicite : stored → querystring → navigator → 'fr'
  - Ajout de `supportedLngs`, `load: 'currentOnly'`, événement `languageChanged` pour sync localStorage
  - Correction structure `auth.login` dans `fr.json` (string → object)
  - Correction `Subscription.js` : `t('auth.login')` → `t('auth.login.submit')`
  - Bump service worker v11 pour invalidation cache
  - 9/9 tests de langues passés (Testing Agent)

### Session 2025-04-10
- [x] **Correctif anti-double-clic** sur page d'abonnement (`Subscription.js`)
- [x] **Pare-feu & Sécurité** implémenté (slowapi, secure, admin dashboard)
- [x] **Cadeau d'abonnement** (admin peut offrir un abo + email auto)
- [x] **Resend SDK v2** (`resend.Emails.send`)
- [x] **Tarification multi-zones** (France, Londres x3, Madrid x3)
- [x] **Landing page dynamique** (revenus chauffeurs par région, prix zones)
- [x] **Traductions massives** (16 langues, placeholders, noms de zones)

### Sessions précédentes
- [x] Vidéos promotionnelles (Sora 2 + TTS)
- [x] Nouveaux champs d'inscription (adresse + date de naissance)
- [x] Stripe Live key
- [x] Auto-centrage carte géolocalisation
- [x] Admin : colonne "Identité", modale RGPD, historique trajets
- [x] Export PDF (jsPDF pur)
- [x] PWA installable
- [x] Internationalisation 16 langues
- [x] Système de notation chauffeurs
- [x] Historique des trajets
- [x] Page CGU / CGV

---

## Prioritized Backlog

### P0 - Critique (Bloqué)
- [ ] **Migration Stripe → Crédit Agricole** : En attente des identifiants bancaires du client (Site ID, Clés HMAC, ICS)

### P1 - Haute priorité
- [x] Refactoring `server.py` complet : 5940 → 2778 lignes (-53%, 8 modules extraits)
- [ ] Validation complète des fonctionnalités (Notifications Push, Historique, Notation)
- [ ] Mettre en place VAPID keys de production

### P2 - Moyenne priorité
- [ ] Sauvegardes automatiques MongoDB sur VPS
- [ ] Espaces publicitaires pour annonceurs (repoussé par le client)

### P3 - Basse priorité
- [ ] Chat en temps réel usager/chauffeur
- [ ] Amélioration mode hors ligne PWA

---

## Technical Stack
- **Frontend**: React, Tailwind, Shadcn/UI, jsPDF, i18next, Leaflet.js
- **Backend**: FastAPI, Motor (async MongoDB)
- **Database**: MongoDB
- **Payments**: Stripe (transition vers Crédit Agricole)
- **Emails**: Resend (SDK v2)
- **AI**: OpenAI Sora 2, OpenAI TTS (via Emergent LLM Key)
- **Infrastructure**: VPS Hostinger, PM2

## Deployment Notes
Le client héberge sur son propre VPS. Les changements doivent être :
1. Sauvegardés sur GitHub via "Save to GitHub"
2. Déployés manuellement : `cd /var/www/metro-taxi-app && git pull && cd frontend && yarn build && pm2 restart all`
3. Cache PWA vidé côté utilisateurs (service worker versionné pour auto-invalidation)

## Key Config
- i18n: 16 langues, détection explicite (localStorage > querystring > navigator > 'fr'), fallback: 'en'
- Service Worker: v11, network-first pour pages, cache-first pour audio
- IMPORTANT: Ne pas toucher à l'implémentation Resend (`resend.Emails.send`)

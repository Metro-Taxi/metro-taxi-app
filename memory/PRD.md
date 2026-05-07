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

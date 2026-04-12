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
- [ ] Refactoring `server.py` (~5900 lignes) → diviser en modules
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

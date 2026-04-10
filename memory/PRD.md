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

### Session 2025-04-10
- [x] **Correctif anti-double-clic** sur page d'abonnement (`Subscription.js`)
  - État `isRedirecting` bloquant
  - Boutons désactivés pendant transaction
  - Toast d'avertissement si re-clic
  - Écran de chargement plein page

### Sessions précédentes
- [x] Vidéos promotionnelles (Sora 2 + TTS)
- [x] Nouveaux champs d'inscription (adresse complète + date de naissance)
- [x] Mise à jour clé API Stripe Live
- [x] Auto-centrage carte sur géolocalisation usager
- [x] Admin Dashboard : colonne "Identité", modale RGPD, historique trajets
- [x] Export PDF fonctionnel (jsPDF pur)
- [x] PWA installable
- [x] Internationalisation 16 langues
- [x] Système de notation chauffeurs (code prêt, non testé)
- [x] Historique des trajets (code prêt, non testé)
- [x] Page CGU

---

## Prioritized Backlog

### P0 - Critique (Bloqué)
- [ ] **Migration Stripe → Crédit Agricole** : En attente des identifiants bancaires du client (Site ID, Clés HMAC, ICS)

### P1 - Haute priorité
- [ ] Validation complète des fonctionnalités (Notifications Push, Historique, Notation)
- [ ] Mettre en place les VAPID keys de production pour notifications push

### P2 - Moyenne priorité
- [ ] Refactoring `server.py` (>5400 lignes) → diviser en modules
- [ ] Sauvegardes automatiques MongoDB sur VPS
- [ ] Espaces publicitaires pour annonceurs (demande client)

### P3 - Basse priorité
- [ ] Chat en temps réel usager/chauffeur
- [ ] Amélioration mode hors ligne PWA

---

## Technical Stack
- **Frontend**: React, Tailwind, Shadcn/UI, jsPDF, i18next, Leaflet.js
- **Backend**: FastAPI, Motor (async MongoDB)
- **Database**: MongoDB
- **Payments**: Stripe (transition vers Crédit Agricole)
- **Emails**: Resend
- **AI**: OpenAI Sora 2, OpenAI TTS (via Emergent LLM Key)
- **Infrastructure**: VPS Hostinger, PM2

## Deployment Notes
Le client héberge sur son propre VPS. Les changements doivent être :
1. Sauvegardés sur GitHub via "Save to GitHub"
2. Déployés manuellement : `cd /var/www/metro-taxi-app && git pull && cd frontend && yarn build && pm2 restart all`
3. Cache PWA vidé côté utilisateurs

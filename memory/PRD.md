# Métro-Taxi - Product Requirements Document

## 📋 Problème Original
Créer une plateforme web Métro-Taxi de mise en relation entre usagers abonnés et chauffeurs VTC. Les trajets sont gratuits car couverts par abonnement. Design moderne style Uber avec couleurs noir/jaune/blanc.

## 🏗️ Architecture
- **Frontend**: React 19, TailwindCSS, Leaflet/OpenStreetMap, Framer Motion, i18next
- **Backend**: FastAPI (Python), MongoDB, JWT Auth
- **Paiement**: Stripe (emergentintegrations library) + Stripe Connect (SDK natif)
- **TTS**: OpenAI Text-to-Speech (emergentintegrations library)
- **Email**: Resend (vérification email)
- **Temps réel**: WebSocket

## 👥 User Personas
1. **Usager**: Cherche mobilité urbaine abordable via abonnement
2. **Chauffeur VTC**: Souhaite optimiser ses trajets avec passagers
3. **Admin**: Gère la plateforme, valide/désactive les chauffeurs

## ✅ Fonctionnalités Implémentées

### Section 1 - Inscription ✅
- [x] Inscription usager + chauffeur avec IBAN/BIC
- [x] Activation automatique des chauffeurs
- [x] Page inscription chauffeur traduite en 16 langues

### Section 2 - Abonnements ✅
- [x] 3 forfaits: 24h (7€), 1 semaine (17€), 1 mois (54€)
- [x] Paiement Stripe + prix en devises locales

### Section 3-5 - Trajets & Matching ✅
- [x] Carte géolocalisée usagers/chauffeurs
- [x] Algorithme de matching intelligent
- [x] Calcul des kilomètres par trajet (pickup + ride)

### Section 6 - Backend Admin ✅
- [x] Dashboard statistiques
- [x] Gestion chauffeurs + revenus
- [x] Traitement des virements

### Section 7 - Landing Page ✅
- [x] Hero multilingue + vidéo promo TTS

### Section 8 - Internationalisation ✅
- [x] 16 langues triées alphabétiquement (sélecteur scrollable)

### Section 9 - Système de Revenus Chauffeurs ✅ (NOUVEAU)
- [x] **Tarif : 1,50€ par kilomètre**
- [x] **Kilomètres : trajets avec passagers + déplacement vers pickup**
- [x] **Virement automatique le 10 du mois**
- [x] **APIs implémentées** :
  - GET /api/drivers/earnings (revenus chauffeur)
  - GET /api/drivers/stripe-connect/status (statut compte Stripe)
  - POST /api/drivers/stripe-connect/create-account (créer compte)
  - GET /api/admin/driver-earnings (admin: tous les revenus)
  - POST /api/admin/stripe-connect/process-payout/{driver_id} (virement individuel)
  - POST /api/admin/stripe-connect/process-all-payouts (tous les virements)
  - GET /api/stripe-connect/config (configuration Stripe)

### Section 10 - Stripe Connect ✅ (NOUVEAU - 15/03/2026)
- [x] **Création de comptes Stripe Connect Custom** pour les chauffeurs
- [x] **Ajout automatique du compte bancaire SEPA** (IBAN/BIC)
- [x] **Virements via Stripe Transfer API**
- [x] **Tâche planifiée automatique** le 10 du mois
- [x] **Documentation claire** des étapes d'activation

## ⚠️ Configuration Requise pour Virements Réels

**Stripe Connect nécessite une vraie clé API Stripe** (pas `sk_test_emergent`):

1. Créer un compte Stripe sur https://dashboard.stripe.com
2. Activer Stripe Connect dans les paramètres
3. Obtenir une clé API (sk_live_xxx ou sk_test_xxx)
4. Configurer dans `/app/backend/.env` : `STRIPE_API_KEY=sk_xxx`

**Route de vérification**: GET /api/stripe-connect/config

## 📊 Statut Tests
- Backend: 100% ✅
- Frontend: 100% ✅

## 🔄 Backlog

### P1 - Important  
- [ ] Obtenir et configurer une vraie clé Stripe Connect
- [ ] Vérifier domaine metro-taxi.com sur Resend

### P2 - Améliorations
- [ ] Interface chauffeur pour voir les revenus détaillés
- [ ] Notifications push
- [ ] Historique trajets complet
- [ ] Système de notation

## 🔑 Credentials Test
- Admin: admin@metrotaxi.fr / admin123
- Driver test: jean.dupont.test@example.com / test123456

## 📁 Fichiers Clés
- `/app/backend/server.py` - API avec Stripe Connect (lignes 1768-2000)
- `/app/frontend/src/pages/RegisterDriver.js` - Formulaire internationalisé
- `/app/frontend/src/i18n/` - 16 langues

## 🔧 Dernières Modifications (15/03/2026)
1. **Stripe Connect intégré** : Création comptes, virements SEPA
2. **Tâche automatique améliorée** : Utilise Stripe Transfer API
3. **Route de configuration** : /api/stripe-connect/config
4. **Documentation claire** : Instructions pour activer les virements réels

## 🌐 3rd Party Integrations
- **Stripe Checkout** — via emergentintegrations (clé test)
- **Stripe Connect** — via SDK natif stripe (requiert vraie clé)
- **OpenAI Sora 2 / TTS** — Emergent LLM Key
- **Resend** — en attente vérification domaine

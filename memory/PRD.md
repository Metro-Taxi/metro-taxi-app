# Métro-Taxi - Product Requirements Document

## 📋 Problème Original
Créer une plateforme web Métro-Taxi de mise en relation entre usagers abonnés et chauffeurs VTC. Les trajets sont gratuits car couverts par abonnement. Design moderne style Uber avec couleurs noir/jaune/blanc.

## 🏗️ Architecture
- **Frontend**: React 19, TailwindCSS, Leaflet/OpenStreetMap, Framer Motion, i18next
- **Backend**: FastAPI (Python), MongoDB, JWT Auth
- **Paiement**: Stripe (emergentintegrations library)
- **TTS**: OpenAI Text-to-Speech (emergentintegrations library)
- **Email**: Resend (vérification email)
- **Temps réel**: WebSocket

## 👥 User Personas
1. **Usager**: Cherche mobilité urbaine abordable via abonnement
2. **Chauffeur VTC**: Souhaite optimiser ses trajets avec passagers
3. **Admin**: Gère la plateforme, valide/désactive les chauffeurs

## ✅ Fonctionnalités Implémentées

### Section 1 - Inscription ✅
- [x] Inscription usager (nom, prénom, email, téléphone, mot de passe)
- [x] Inscription chauffeur (+ plaque, type véhicule, places, licence VTC)
- [x] **Champ compte bancaire (IBAN + BIC/SWIFT)** pour les chauffeurs (NOUVEAU - 14/03/2026)
- [x] **Activation automatique des chauffeurs** à l'inscription (NOUVEAU - 14/03/2026)
- [x] Désactivation manuelle par admin toujours disponible
- [x] Vérification email via Resend (emails multilingues)

### Section 2 - Abonnements ✅
- [x] 3 forfaits: 24h (7€), 1 semaine (17€), 1 mois (54€)
- [x] Prix en devises locales selon la langue
- [x] Paiement Stripe (Visa, MasterCard, American Express)
- [x] Activation automatique après paiement
- [x] Désactivation automatique des abonnements expirés

### Section 3 - Écran Usager ✅
- [x] Carte géolocalisée avec véhicules disponibles
- [x] Demande de trajet en un clic
- [x] Progression du trajet avec timeline visuelle

### Section 4 - Écran Chauffeur ✅
- [x] Carte avec usagers demandeurs
- [x] Accepter/Refuser demandes
- [x] Bouton connexion/déconnexion en ligne
- [x] **Gestion des informations bancaires** (NOUVEAU - 14/03/2026)

### Section 5 - Algorithme Central ✅
- [x] Algorithme intelligent de matching
- [x] Calcul de route optimale avec segments (1.5-3 km)
- [x] Maximum 2 transbordements

### Section 6 - Backend Admin ✅
- [x] Dashboard avec statistiques
- [x] Gestion chauffeurs (activer/désactiver)
- [x] Onglet Abonnements avec badges traduits (ACTIFS, BIENTÔT, EXPIRÉS)
- [x] Cartes virtuelles avec détails

### Section 7 - Landing Page ✅
- [x] Hero section multilingue
- [x] Vidéo promotionnelle avec voix off TTS
- [x] Section forfaits avec prix locaux

### Section 8 - Internationalisation (i18n) ✅ (Mis à jour - 14/03/2026)
- [x] **16 langues supportées** :
  - 🇫🇷 Français (défaut)
  - 🇺🇸 English (US)
  - 🇬🇧 English (UK)
  - 🇩🇪 Deutsch
  - 🇳🇱 Nederlands
  - 🇪🇸 Español
  - 🇵🇹 Português
  - 🇮🇹 **Italiano** (NOUVEAU)
  - 🇳🇴 Norsk
  - 🇸🇪 Svenska
  - 🇩🇰 Dansk
  - 🇨🇳 中文
  - 🇮🇳 हिन्दी
  - 🇵🇰 ਪੰਜਾਬੀ
  - 🇸🇦 **العربية** (NOUVEAU)
  - 🇷🇺 **Русский** (NOUVEAU)
- [x] Badges admin traduits (ACTIFS, BIENTÔT, EXPIRÉS)
- [x] Voix off TTS pour toutes les langues

## 📊 Statut Tests
- Backend: 100% ✅ (iteration_5.json)
- Frontend: 100% ✅

## 🔄 Backlog

### P0 - Prioritaire
- [ ] **Système de virement automatique des salaires** (Stripe Connect Payouts)
- [ ] Connecter domaine `metro-taxi.com`

### P1 - Important  
- [ ] Vérifier domaine metro-taxi.com sur Resend

### P2 - Améliorations
- [ ] Notifications push mobiles
- [ ] Historique complet des trajets
- [ ] Système de notation chauffeur

## 🔑 Credentials Test
- Admin: admin@metrotaxi.fr / admin123
- User test: marie.test@example.com / test123

## 📁 Fichiers Clés
- `/app/backend/server.py` - API FastAPI avec routes bank-info
- `/app/frontend/src/pages/RegisterDriver.js` - Formulaire avec IBAN/BIC
- `/app/frontend/src/i18n/locales/` - 16 fichiers de traduction

## 🔧 Dernières Modifications (14/03/2026)
1. **Ajout champ compte bancaire** : IBAN + BIC/SWIFT dans l'inscription chauffeur
2. **Activation automatique** : `is_validated=True` par défaut
3. **API bancaire** : PUT/GET /api/drivers/bank-info
4. **Nouvelles langues** : Italien, Arabe, Russe (total 16 langues)
5. **Badges traduits** : ACTIFS, BIENTÔT, EXPIRÉS dans admin dashboard

## 🌐 3rd Party Integrations
- **Stripe** — clé test disponible
- **OpenAI Sora 2** — Emergent LLM Key
- **OpenAI TTS** — Emergent LLM Key
- **Resend** — en attente vérification domaine

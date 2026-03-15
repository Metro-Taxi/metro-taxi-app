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
- [x] Champ compte bancaire (IBAN + BIC/SWIFT) pour les chauffeurs
- [x] Activation automatique des chauffeurs à l'inscription
- [x] Désactivation manuelle par admin toujours disponible
- [x] Vérification email via Resend (emails multilingues)
- [x] **Page inscription chauffeur traduite en 16 langues** (NOUVEAU - 15/03/2026)

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
- [x] Gestion des informations bancaires
- [x] **Visualisation des revenus** (NOUVEAU - 15/03/2026)

### Section 5 - Algorithme Central ✅
- [x] Algorithme intelligent de matching
- [x] Calcul de route optimale avec segments (1.5-3 km)
- [x] Maximum 2 transbordements
- [x] **Calcul des kilomètres par trajet** (pickup + ride) (NOUVEAU - 15/03/2026)

### Section 6 - Backend Admin ✅
- [x] Dashboard avec statistiques
- [x] Gestion chauffeurs (activer/désactiver)
- [x] Onglet Abonnements avec badges traduits (ACTIFS, BIENTÔT, EXPIRÉS)
- [x] Cartes virtuelles avec détails
- [x] **Gestion des revenus chauffeurs** (NOUVEAU - 15/03/2026)
- [x] **Traitement des virements** (NOUVEAU - 15/03/2026)

### Section 7 - Landing Page ✅
- [x] Hero section multilingue
- [x] Vidéo promotionnelle avec voix off TTS
- [x] Section forfaits avec prix locaux

### Section 8 - Internationalisation (i18n) ✅
- [x] **16 langues supportées** triées alphabétiquement :
  - 🇸🇦 العربية (Arabe)
  - 🇩🇰 Dansk
  - 🇩🇪 Deutsch
  - 🇺🇸 English (US)
  - 🇬🇧 English (UK)
  - 🇪🇸 Español
  - 🇫🇷 Français
  - 🇮🇳 हिन्दी
  - 🇮🇹 Italiano
  - 🇳🇱 Nederlands
  - 🇳🇴 Norsk
  - 🇵🇰 ਪੰਜਾਬੀ
  - 🇵🇹 Português
  - 🇷🇺 Русский
  - 🇸🇪 Svenska
  - 🇨🇳 中文
- [x] **Sélecteur de langues scrollable** (max-h-80, overflow-y-auto) (NOUVEAU - 15/03/2026)
- [x] Badges admin traduits
- [x] Voix off TTS pour toutes les langues

### Section 9 - Système de Revenus Chauffeurs ✅ (NOUVEAU - 15/03/2026)
- [x] **Tarif : 1,50€ par kilomètre**
- [x] **Kilomètres comptés : trajets avec passagers + déplacement vers point de prise en charge**
- [x] **Virement automatique le 10 du mois suivant**
- [x] Collection `driver_earnings` pour le suivi mensuel
- [x] Collection `driver_payouts` pour l'historique des paiements
- [x] API GET /api/drivers/earnings (chauffeur)
- [x] API GET /api/admin/driver-earnings (admin)
- [x] API POST /api/admin/process-payouts (admin)
- [x] Tâche planifiée automatique (process_automatic_payouts)
- [x] **Note: Virements bancaires MOCKÉS** - les paiements sont enregistrés mais non exécutés réellement

## 📊 Statut Tests
- Backend: 100% ✅ (iteration_6.json)
- Frontend: 100% ✅

## 🔄 Backlog

### P1 - Important  
- [ ] Vérifier domaine metro-taxi.com sur Resend
- [ ] Connecter domaine personnalisé

### P2 - Améliorations
- [ ] Intégration Stripe Connect réelle pour virements bancaires automatiques
- [ ] Notifications push mobiles
- [ ] Historique complet des trajets
- [ ] Système de notation chauffeur

## 🔑 Credentials Test
- Admin: admin@metrotaxi.fr / admin123
- User test: marie.test@example.com / test123
- Driver test: jean.dupont.test@example.com / test123456

## 📁 Fichiers Clés
- `/app/backend/server.py` - API FastAPI avec système de revenus
- `/app/frontend/src/pages/RegisterDriver.js` - Formulaire internationalisé
- `/app/frontend/src/i18n/index.js` - 16 langues triées alphabétiquement
- `/app/frontend/src/i18n/locales/` - Fichiers de traduction avec clés `driverRegister`

## 🔧 Dernières Modifications (15/03/2026)
1. **Sélecteur de langues amélioré** : Scrollable (max-h-80), trié alphabétiquement
2. **Inscription chauffeur traduite** : 16 langues avec clés `driverRegister.*`
3. **Système de revenus chauffeurs** : 
   - DRIVER_RATE_PER_KM = 1.50€
   - PAYOUT_DAY = 10 (du mois)
   - Calcul: pickup_km + ride_km
   - Collections: driver_earnings, driver_payouts

## 🌐 3rd Party Integrations
- **Stripe** — clé test disponible
- **OpenAI Sora 2** — Emergent LLM Key
- **OpenAI TTS** — Emergent LLM Key
- **Resend** — en attente vérification domaine

## ⚠️ APIs Mockées
- **Virements bancaires** : Les payouts sont enregistrés dans la base de données avec statut "processed" mais aucun virement SEPA n'est réellement exécuté. Pour une mise en production, il faudra intégrer Stripe Connect ou une API bancaire.

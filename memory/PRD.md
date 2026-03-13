# Métro-Taxi - Product Requirements Document

## 📋 Problème Original
Créer une plateforme web Métro-Taxi de mise en relation entre usagers abonnés et chauffeurs VTC. Les trajets sont gratuits car couverts par abonnement. Design moderne style Uber avec couleurs noir/jaune/blanc.

## 🏗️ Architecture
- **Frontend**: React 19, TailwindCSS, Leaflet/OpenStreetMap, Framer Motion
- **Backend**: FastAPI (Python), MongoDB, JWT Auth
- **Paiement**: Stripe (emergentintegrations library)
- **Temps réel**: WebSocket

## 👥 User Personas
1. **Usager**: Cherche mobilité urbaine abordable via abonnement
2. **Chauffeur VTC**: Souhaite optimiser ses trajets avec passagers
3. **Admin**: Gère la plateforme, valide les chauffeurs

## ✅ Fonctionnalités Implémentées (13/03/2026)

### Section 1 - Inscription ✅
- [x] Inscription usager (nom, prénom, email, téléphone, mot de passe)
- [x] Inscription chauffeur (+ plaque, type véhicule, places, licence VTC)
- [x] Validation chauffeur par admin
- [x] **Vérification email** avec token sécurisé

### Section 2 - Abonnements ✅
- [x] 3 forfaits: 24h (6,99€), 1 semaine (16,99€), 1 mois (53,99€)
- [x] Paiement Stripe (Visa, MasterCard, American Express)
- [x] Activation automatique après paiement

### Section 3 - Écran Usager ✅
- [x] Carte géolocalisée avec véhicules disponibles
- [x] Affichage places libres et direction
- [x] Demande de trajet en un clic
- [x] **Suggestions de transbordement** (changement véhicule)
- [x] **Progression du trajet** avec timeline visuelle
- [x] **Sélection destination sur carte**

### Section 4 - Écran Chauffeur ✅
- [x] Carte avec usagers demandeurs
- [x] Accepter/Refuser demandes
- [x] Bouton connexion/déconnexion en ligne
- [x] Indicateur places restantes
- [x] **Mise à jour progression trajet**

### Section 5 - Algorithme Central ✅ (NOUVEAU - 13/03/2026)
- [x] **Algorithme intelligent de matching** basé sur:
  - Distance usager-chauffeur (score pondéré)
  - Direction du trajet (cosine similarity)
  - Nombre de places libres
  - ETA (temps estimé d'arrivée)
- [x] **Calcul de route optimale** avec segments
  - Segments optimisés entre 1.5km et 3km
  - Suggestion transbordement automatique
  - Maximum 2 transbordements
- [x] **APIs de matching**:
  - `/api/matching/optimal-route` - Route optimale avec segments
  - `/api/matching/network-status` - Statut réseau temps réel
  - `/api/matching/transfers` - Suggestions transbordement
  - `/api/matching/find-drivers` - Chauffeurs compatibles
  - `/api/matching/driver-passengers/{id}` - Passagers compatibles
- [x] **Panneau itinéraire optimal** avec:
  - Distance totale
  - Nombre de transbordements
  - Temps estimé
  - Efficacité du trajet
  - Détail des segments

### Section 6 - Backend Admin ✅
- [x] Dashboard avec statistiques (usagers, chauffeurs, abonnements, trajets)
- [x] Liste chauffeurs avec actions Activer/Désactiver
- [x] Liste usagers
- [x] **Cartes virtuelles** visibles avec détails

### Section 7 - Carte Virtuelle ✅
- [x] Carte nominative avec identifiant unique (MT-XXXXXXXX)
- [x] Affichage abonnement actif
- [x] Visible dans profil usager
- [x] **Visible dans l'admin** avec historique trajets

### Section 8 - Landing Page ✅
- [x] Hero section avec CTA
- [x] Section vidéo présentation
- [x] Section forfaits
- [x] Section "Comment ça marche"
- [x] **Section "Devenir Chauffeur VTC"** avec revenus et avantages

### Section 9 - Sécurité ✅
- [x] **Vérification email** à l'inscription (MOCK - pas d'envoi réel)
- [x] Authentification JWT sécurisée
- [x] Validation chauffeur par admin
- [x] Protection des routes

## 📊 Statut Tests
- Backend: 100% ✅ (18/18 tests)
- Frontend: 100% ✅

## 🔄 Backlog

### P0 - Prioritaire
- [ ] Connecter domaine `metro-taxi.com`
- [ ] Créer email professionnel `judeesouleymane@metro-taxi.com`

### P1 - Important
- [ ] Implémenter vérification email réelle (SendGrid/Resend)
- [ ] Vidéo promotionnelle AI (Sora 2) - bloqué par balance

### P2 - Améliorations
- [ ] Notifications push mobiles
- [ ] Historique complet des trajets usager
- [ ] Système de notation chauffeur

### P3 - Futur
- [ ] Version mobile native

## 🔑 Credentials Test
- Admin: admin@metrotaxi.fr / admin123
- User test: marie.test@example.com / test123
- Stripe: sk_test_emergent (env)

## 📁 Fichiers Clés
- `/app/backend/server.py` - API FastAPI avec algorithme central
- `/app/frontend/src/pages/UserDashboard.js` - Dashboard usager avec carte
- `/app/frontend/src/pages/Landing.js` - Page d'accueil avec section chauffeurs
- `/app/frontend/src/contexts/AuthContext.js` - Gestion auth
- `/app/scripts/video_script_v2.md` - Script vidéo pour future génération

## 🧮 Algorithme Central - Détails Techniques

### Constantes
```python
SEGMENT_MIN_KM = 1.5  # Distance minimum par segment
SEGMENT_MAX_KM = 3.0  # Distance maximum (suggère transbordement)
MAX_PICKUP_DISTANCE_KM = 2.0  # Distance max de prise en charge
MAX_TRANSFERS = 2  # Nombre max de transbordements
DIRECTION_THRESHOLD = 60  # Score direction minimum (0-100)
```

### Calcul du Score de Matching
- Distance (40 points max): `40 - (distance * 20)`
- Direction (40 points max): `cosine_similarity * 0.4`
- Places (20 points max): `min(20, seats * 5)`

### Fonctions Clés
- `calculate_distance()` - Haversine formula
- `calculate_direction_score()` - Cosine similarity
- `calculate_eta_minutes()` - ETA basé sur vitesse moyenne
- `find_optimal_transfer_point()` - Point de transbordement optimal
- `calculate_multi_transfer_route()` - Route complète avec segments

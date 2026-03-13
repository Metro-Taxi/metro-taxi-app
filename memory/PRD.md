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

### Section 4 - Écran Chauffeur ✅
- [x] Carte avec usagers demandeurs
- [x] Accepter/Refuser demandes
- [x] Bouton connexion/déconnexion en ligne
- [x] Indicateur places restantes
- [x] **Mise à jour progression trajet**

### Section 5 - Algorithme Matching ✅
- [x] **Algorithme intelligent** basé sur:
  - Distance usager-chauffeur
  - Direction du trajet (cosine similarity)
  - Nombre de places libres
- [x] Score de matching calculé
- [x] **Optimisation des correspondances** (transbordements)

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
- [x] CTA Devenir chauffeur

### Section 9 - Sécurité ✅
- [x] **Vérification email** à l'inscription
- [x] Authentification JWT sécurisée
- [x] Validation chauffeur par admin
- [x] Protection des routes

## 📊 Statut Tests
- Backend: 94.4% ✅
- Frontend: 90% ✅

## 🔄 Backlog (P2/P3)
- [ ] P2: Notifications push mobiles
- [ ] P2: Historique complet des trajets usager
- [ ] P2: Système de notation chauffeur
- [ ] P3: Version mobile native
- [ ] P3: Envoi réel email (intégration SendGrid/Resend)

## 🔑 Credentials Test
- Admin: admin@metrotaxi.fr / admin123
- Stripe: sk_test_emergent (env)

## 📁 Fichiers Clés
- `/app/backend/server.py` - API FastAPI complète
- `/app/frontend/src/pages/` - Toutes les pages React
- `/app/frontend/src/contexts/AuthContext.js` - Gestion auth
- `/app/frontend/src/pages/VerifyEmail.js` - Page vérification email

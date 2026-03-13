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

### Section 1 - Inscription
- [x] Inscription usager (nom, prénom, email, téléphone, mot de passe)
- [x] Inscription chauffeur (+ plaque, type véhicule, places, licence VTC)
- [x] Validation chauffeur par admin

### Section 2 - Abonnements
- [x] 3 forfaits: 24h (6,99€), 1 semaine (16,99€), 1 mois (50,99€)
- [x] Paiement Stripe (Visa, MasterCard, American Express)
- [x] Activation automatique après paiement

### Section 3 - Écran Usager
- [x] Carte géolocalisée avec véhicules disponibles
- [x] Affichage places libres et direction
- [x] Demande de trajet en un clic
- [x] Suivi du statut de la demande

### Section 4 - Écran Chauffeur
- [x] Carte avec usagers demandeurs
- [x] Accepter/Refuser demandes
- [x] Bouton connexion/déconnexion en ligne
- [x] Indicateur places restantes

### Section 5 - Algorithme Matching
- [x] Affichage véhicules proches
- [x] Système de demandes directes

### Section 6 - Backend Admin
- [x] Dashboard avec statistiques (usagers, chauffeurs, abonnements, trajets)
- [x] Liste chauffeurs avec actions Activer/Désactiver
- [x] Liste usagers

### Section 7 - Carte Virtuelle
- [x] Carte nominative avec identifiant
- [x] Affichage abonnement actif
- [x] Visible dans profil usager

### Section 8 - Landing Page
- [x] Hero section avec CTA
- [x] Section vidéo présentation
- [x] Section forfaits
- [x] Section "Comment ça marche"
- [x] CTA Devenir chauffeur

### Section 9 - Sécurité
- [x] Authentification JWT
- [x] Validation chauffeur par admin
- [x] Protection des routes

## 📊 Statut Tests
- Backend: 100% ✅
- Frontend: 90% ✅

## 🔄 Backlog (P1/P2)
- [ ] P1: Email de vérification
- [ ] P1: Algorithme transbordement (changement de véhicule)
- [ ] P2: Historique des trajets
- [ ] P2: Système de notation
- [ ] P2: Notifications push mobiles
- [ ] P2: Version mobile native

## 🔑 Credentials Test
- Admin: admin@metrotaxi.fr / admin123
- Stripe: sk_test_emergent (env)

## 📁 Fichiers Clés
- `/app/backend/server.py` - API FastAPI complète
- `/app/frontend/src/pages/` - Toutes les pages React
- `/app/frontend/src/contexts/AuthContext.js` - Gestion auth

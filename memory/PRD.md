# Métro-Taxi - Product Requirements Document

## 📋 Résumé
Plateforme de mise en relation usagers/chauffeurs VTC avec abonnements. Trajets gratuits couverts par l'abonnement.

## 🏗️ Stack Technique
- **Frontend**: React 19, TailwindCSS, Leaflet, i18next (16 langues)
- **Backend**: FastAPI, MongoDB, JWT Auth
- **Paiements**: Stripe Checkout + Stripe Connect Express
- **Emails**: Resend (domaine metro-taxi.com vérifié)
- **TTS**: OpenAI (Emergent LLM Key)
- **PWA**: Service Worker, Manifest, Cache hors ligne

## ✅ Fonctionnalités Complètes

### 📜 Conditions Générales de Vente (CGV) ✅ (24/03/2026)
- Page `/cgv` avec tous les détails tarifaires et conditions
- Modèle par abonnement (aucun paiement par trajet)
- **Tarifs** : 24h - 6,99€ | 1 semaine - 16,99€ | 1 mois - 53,99€
- **Conditions** : Abonnement actif requis, non remboursable, renouvellement utilisateur
- **Suspension** : Accès désactivé si abonnement expiré
- Bouton "J'accepte les CGV" avec checkbox
- Lien CGV ajouté au pied de page
- Traductions complètes (français, anglais)

### 📄 Conditions Générales d'Utilisation (CGU) ✅
- Page `/cgu` et `/terms` avec règles d'utilisation
- Traductions multilingues

### 🔔 Notifications Push ✅ (19/03/2026)
- Endpoint `/api/notifications/subscribe` pour enregistrer les tokens
- Endpoint `/api/notifications` pour récupérer les notifications
- Composant `NotificationCenter` avec icône cloche et compteur non-lus
- Polling toutes les 30 secondes pour nouvelles notifications

### 📜 Historique des trajets ✅ (19/03/2026)
- Endpoint `/api/rides/history` avec pagination et filtres
- Endpoint `/api/rides/{ride_id}` pour détails
- Composant `RideHistory` avec modal complet
- Filtres par statut (Tous, Terminé, Annulé, En cours)
- Affichage trajets avec adresses, chauffeur, notes

### ⭐ Système de notation ✅ (19/03/2026)
- Endpoint `/api/ratings` pour créer une note (1-5 étoiles)
- Endpoint `/api/ratings/pending` pour trajets non notés
- Endpoint `/api/ratings/driver/{id}` pour notes d'un chauffeur
- Composant `RatingModal` avec étoiles interactives
- Composant `PendingRatings` pour rappeler de noter
- Mise à jour automatique moyenne chauffeur

### 🚀 Guide de déploiement ✅ (19/03/2026)
- `/app/DEPLOYMENT_GUIDE.md` - Guide complet étape par étape
- Configuration Docker Compose
- Configuration Nginx avec SSL
- Variables d'environnement production

### Progressive Web App (PWA) ✅
- Manifest.json, Service Worker, icônes
- Bannière d'installation (mobile uniquement)

### Système d'Emails Resend ✅
- Domaine metro-taxi.com vérifié
- Notifications de virement aux chauffeurs

### Internationalisation (i18n) ✅
- 16 langues avec devises locales
- Voix off TTS dans chaque langue

### Système de Revenus Chauffeurs ✅
- 1,50€/km avec passagers à bord
- Virements Stripe Connect automatiques

## 🔑 Credentials Test
- Admin: admin@metrotaxi.fr / admin123
- User: testfeatures@test.com / Test1234!

## 📊 Collections MongoDB
- `users` - Utilisateurs
- `drivers` - Chauffeurs  
- `rides` - Trajets
- `ratings` - Notes
- `notifications` - Notifications
- `push_subscriptions` - Abonnements push
- `driver_earnings` - Revenus chauffeurs
- `payout_history` - Historique virements

## 📅 Dernière Mise à Jour
**24/03/2026**
- ✅ Page CGV créée avec tarifs, conditions et bouton d'acceptation
- ✅ Lien CGV ajouté au pied de page
- ✅ Traductions français/anglais ajoutées

## 🔄 Prochaines Étapes
- [ ] Tester les fonctionnalités complètes (notifications, historique, notation)
- [ ] Résoudre l'incohérence de la base de données de test
- [ ] Déploiement en production sur metro-taxi.com
- [ ] Configuration clé Stripe LIVE

## 📦 Backlog Futur
- Notifications push réelles avec VAPID keys
- Système de chat usager/chauffeur
- Mode hors ligne avancé pour PWA

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

### 📢 Pop-up d'Information Important ✅ (24/03/2026)
- **Affichage** : À l'ouverture de l'application et quand l'abonnement expire bientôt
- **Message** :
  - "Votre abonnement doit être actif pour utiliser Métro-Taxi."
  - "Vous recevrez des notifications de rappel avant expiration."
  - "Nous vous recommandons de renouveler votre abonnement dès réception de ces alertes afin d'éviter toute interruption du service pendant vos déplacements."
- **Alerte d'expiration** : Affiche les heures restantes si expiration proche (<48h)
- **Bouton "J'ai compris"** : Ferme la pop-up et sauvegarde l'état
- Ne réapparaît pas avant 24h (sauf si abonnement expire bientôt)

### 🚫 Contrôle d'Accès - Abonnement Expiré ✅ (24/03/2026)
- **Overlay de blocage** : Si abonnement expiré, affiche un écran de blocage
- **Message** : "Votre abonnement a expiré. Veuillez le renouveler pour continuer à utiliser Métro-Taxi."
- **Fonctionnalités bloquées** :
  - ❌ Réservation de trajets
  - ❌ Connexion aux véhicules
  - ❌ Visualisation des chauffeurs
- **Bouton "Renouveler mon abonnement"** : Redirige vers `/subscription`
- **Option "Se déconnecter"** : Pour quitter l'application
- Icône d'avertissement rouge et fond flou

### 🔔 Notifications Automatiques d'Expiration d'Abonnement ✅ (24/03/2026)
- **Tâche de fond** : Vérifie toutes les heures les abonnements expirants
- **Notifications envoyées** :
  - 48 heures avant expiration
  - 24 heures avant expiration
  - Le jour de l'expiration
- **Message** : "Votre abonnement Métro-Taxi expire bientôt. Renouvelez-le dès maintenant pour continuer à utiliser le service sans interruption."
- **Bouton "Renouveler maintenant"** : Redirige vers `/subscription`
- **Endpoint `/api/subscription/status`** : Statut de l'abonnement avec heures restantes
- **Endpoint `/api/notifications/test-expiry`** : Pour tests
- Icône ⚠️ et bordure orange pour distinguer les alertes d'expiration

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
**28/03/2026**
- ✅ **Traductions Dashboard Admin vérifiées** : Toutes les langues (EN, ES, etc.) correctement traduites
  - "Drivers" → "Conductores" (ES) - Corrigé
  - Section `driverEarnings` complètement traduite en espagnol
- ✅ **Stripe en mode LIVE** : Paiements réels activés (clé `sk_live_...`)
- ✅ **Sélecteur de langue Admin** : Composant `LanguageSelector.jsx` fonctionnel avec data-testid
- ✅ **Document confidentiel PI** : `/app/CONFIDENTIEL_ALGORITHME_METROTAXI.md` créé

**26/03/2026**
- ✅ **Correction lien de vérification email** : URL complète générée via variable FRONTEND_URL
- ✅ **Clés VAPID générées** : Notifications push réelles configurées avec pywebpush
- ✅ **Emails de rappel d'expiration** : Envoi automatique à 48h, 24h et le jour de l'expiration
- ✅ **Chat en temps réel** : WebSocket usager/chauffeur pendant un trajet
- ✅ **Mode hors ligne PWA amélioré** : Page offline personnalisée + cache API
- ✅ **Structure refactoring préparée** : Dossiers `routes/`, `models/`, `services/`, `utils/` créés

## 🔧 Configuration Production
Variables d'environnement à configurer sur Emergent pour la production :
```
FRONTEND_URL=https://metro-taxi-demo.emergent.host
VAPID_PUBLIC_KEY=BB87ARCh1dnirM0zNPAaYoDXAv9AMErgqZ210CX7mWr1e2DMBJ5aShocfx2wZpvXaBT8Y5FpDmn7V87yfscujEs
VAPID_PRIVATE_KEY=eoxM6m3lnv0X0h1n2cR8dYK9mu9zLiDUbnrZieGoHxg
VAPID_CONTACT=mailto:contact@metro-taxi.com
SENDER_EMAIL=contact@metro-taxi.com
STRIPE_API_KEY=sk_live_... (déjà configuré)
```

## ⚠️ Note Importante sur les Traductions
Les noms propres stockés dans la base de données (ex: "Test Driver", "Boniface Tegang") ne changent **PAS** quand on change la langue de l'interface. Ce sont des **données** entrées par les utilisateurs, pas des clés de traduction. L'internationalisation (i18n) ne traduit que les labels et menus de l'interface.

## 🔄 Prochaines Étapes
- [ ] Refactoring de `server.py` (4400+ lignes → modules séparés)
- [ ] Déploiement en production sur metro-taxi.com
- [ ] Test des notifications push en production avec vraies VAPID keys
- [ ] Découpage de `UserDashboard.js` (1000+ lignes)

## 📦 Backlog Futur
- Amélioration mode hors ligne avancé pour PWA
- Tests automatisés (pytest backend, Jest frontend)

# Métro-Taxi - Product Requirements Document

## 📋 Résumé
Plateforme de mise en relation usagers/chauffeurs VTC avec abonnements multi-régions. Trajets gratuits couverts par l'abonnement.

## 🏗️ Stack Technique
- **Frontend**: React 19, TailwindCSS, Leaflet, i18next (16 langues)
- **Backend**: FastAPI, MongoDB, JWT Auth
- **Paiements**: Stripe Checkout + Stripe Connect Express (LIVE)
- **Emails**: Resend (domaine metro-taxi.com vérifié)
- **TTS**: OpenAI (Emergent LLM Key)
- **PWA**: Service Worker, Manifest, Cache hors ligne
- **Notifications Push**: WebPush (VAPID)

## 🌍 Système Multi-Régions ✅ (28/03/2026)

### Architecture
- **Un chauffeur = Une région** (obligatoire à l'inscription)
- **Abonnements par région** (un utilisateur peut avoir Paris + Lyon actifs simultanément)
- **Prix identiques partout** (même tarification EUR)
- **Base de données centralisée** (collection `regions`)

### Régions configurées
| ID | Nom | Pays | Devise | Statut |
|----|-----|------|--------|--------|
| `paris` | Île-de-France | FR | EUR | ✅ Actif |
| `lyon` | Rhône-Alpes | FR | EUR | ⏳ Inactif |
| `london` | Greater London | GB | GBP | ⏳ Inactif |

### Endpoints API
- `GET /api/regions` - Toutes les régions
- `GET /api/regions/active` - Régions actives uniquement
- `GET /api/regions/detect?lat=...&lng=...` - Détection auto par géolocalisation
- `GET /api/regions/{id}` - Détails d'une région
- `POST /api/admin/regions` - Créer une région (admin)
- `POST /api/admin/regions/{id}/activate` - Activer une région
- `POST /api/payments/checkout/region` - Paiement pour une région spécifique
- `GET /api/subscription/regions` - Abonnements actifs par région
- `GET /api/subscription/region/{id}` - Statut abonnement pour une région

### Composants Frontend ✅ Intégrés
- `RegionSelector.jsx` - Sélecteur de région (dropdown ou cartes)
- `RegionContext.jsx` - Contexte React pour la région courante
- **Page d'inscription chauffeur** - Sélection obligatoire de la région
- **Page d'abonnement** - Sélection de la région avant paiement, affichage des abonnements actifs par région

### Configuration DNS (Hostinger)
Pour activer les sous-domaines :
```
paris.metro-taxi.com  → CNAME → votre-app.emergent.host
lyon.metro-taxi.com   → CNAME → votre-app.emergent.host
london.metro-taxi.com → CNAME → votre-app.emergent.host
```

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
**01/04/2026 - Session Charly (Suite)**
- ✅ **Nouveau panneau de destination** : Après sélection de destination, affiche:
  - Bouton "Rechercher les véhicules" toujours visible
  - Résumé du trajet (km, transferts, temps estimé)
  - Liste des véhicules disponibles avec score de matching
  - Message si aucun véhicule disponible
- ✅ **Traductions ajoutées** : `destinationSelected`, `searchingVehicles`, `findVehicles`, `noVehiclesFound`, etc.
- ✅ **Tests passés** : 100% (13/13) sur le flux de destination

**01/04/2026 - Session Charly**
- ✅ **Bug bouton audio mobile corrigé** : Suppression variables non définies (`audioReady`, `audioProgress`)
- ✅ **Tests de régression complets** : 100% réussis (Backend 11/11, Frontend tous passés)
- ✅ **Vérification cohérence MongoDB** : API et scripts utilisent la même base de données
- ✅ **Début refactoring server.py** : Création `/app/backend/routes/auth.py` (non intégré, préparation)

**30/03/2026 - Session 3**
- ✅ **Champ Tax ID pour chauffeurs** : Numéro d'identification fiscale adapté par pays
  - France : Numéro SIRET (14 chiffres)
  - Espagne/Portugal : NIF
  - Allemagne : Steuernummer
  - Italie : Partita IVA
  - UK : VAT Number / UTR
  - Et tous les autres pays avec labels en langues locales
- ✅ **Enchaînement des abonnements** : Si un utilisateur renouvelle avant expiration, la nouvelle période commence à la fin de l'ancienne (pas immédiatement)
- ✅ **Bug page blanche Stripe corrigé** : Amélioration de la redirection et gestion du cache PWA

**30/03/2026 - Session 2**
- ✅ **Date de virement automatique changée** : 10 → **15** du mois
- ✅ **Onglet Virements Admin** avec bouton manuel
- ✅ **Région affichée dans profil** utilisateur et chauffeur
- ✅ **Champ recherche d'adresse** avec autocomplétion
- ✅ **Protection contre double paiement** (vérification API + messages + email)

**30/03/2026 - Session 1**
- ✅ **Bug d'arrondi Stripe corrigé** : Le montant 16,99€ s'affichait 16,98€ sur Stripe
- ✅ **Migration SDK Stripe** : emergentintegrations → SDK Python `stripe` natif
- ✅ **Refactoring modulaire Phase 1** : Routes `/regions/*` migrées vers `routes/regions.py`

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

### Refactoring server.py - Phase 1 COMPLÈTE ✅
Modules créés et prêts à intégrer :
| Module | Lignes | Routes couvertes |
|--------|--------|------------------|
| `routes/auth.py` | 295 | `/auth/*` (register, login, verify) |
| `routes/drivers.py` | 229 | `/drivers/*` (location, earnings, bank) |
| `routes/matching.py` | 309 | `/matching/*` (algorithme, réseau) |
| `routes/notifications.py` | 242 | `/notifications/*` (push, status) |
| `routes/regions.py` | 228 | `/regions/*` (déjà intégré) |

**Prochaine étape** : Intégrer les routers dans server.py et supprimer le code dupliqué.

### Autres tâches
- [ ] **Migration routes auth** vers `routes/auth.py` ✅ (30/03/2026)
- [ ] **Migration routes paiements** vers `routes/payments.py`
- [ ] **Migration routes chauffeurs** vers `routes/drivers.py`
- [ ] **Migration routes admin** vers `routes/admin.py`
- [ ] Déploiement en production sur metro-taxi.com
- [ ] Test des notifications push en production avec vraies VAPID keys
- [ ] Découpage de `UserDashboard.js` (1000+ lignes)

## 📦 Backlog Futur
- Amélioration mode hors ligne avancé pour PWA
- Tests automatisés (pytest backend, Jest frontend)
- Chat en temps réel usager/chauffeur pendant trajet

## 📝 Changelog

### 01/04/2026 - Correction Bug Bouton Audio Mobile (Session 2)
- **Corrigé** : Bouton audio "Écouter" bloqué/figé sur mobile
  - Suppression des variables non définies (`audioReady`, `audioProgress`) qui causaient une erreur JavaScript
  - Simplification du JSX du bouton pour n'utiliser que `audioPlaying` et `audioLoading`
  - États du bouton :
    - Initial : fond vert (`bg-green-600`), texte "Écouter"
    - Chargement : fond gris (`bg-zinc-700`), icône spinner
    - Lecture : fond jaune (`bg-[#FFD60A]`), texte "Stop"
- **Testé** : 100% des tests passés (13/13) - Desktop et Mobile
  - Bouton visible et cliquable
  - Transitions d'état correctes
  - Changement de langue fonctionnel (FR: "Écouter", EN: "Listen")
  - Endpoints audio HTTP 200

### 01/04/2026 - Audio Landing Page & Notification Mise à Jour PWA
- **Corrigé** : Problème de lenteur de chargement audio (headers Cache-Control)
  - Service Worker v7 avec stratégie **cache-first** pour les fichiers audio
  - Les 16 fichiers MP3 sont pré-chargés dans le cache `metro-taxi-audio-v3`
  - Après premier chargement, audio instantané depuis le cache
- **Corrigé** : Écran noir sur desktop au clic sur le bouton audio
  - Ajout de `safePlayAudio()` pour gérer les erreurs de lecture (politique Autoplay)
  - Les erreurs de play() sont maintenant silencieusement gérées sans crasher
- **Ajouté** : Endpoint backend `/api/audio/voiceover/{filename}` (fallback si local indisponible)
- **Amélioré** : Logique de préchargement audio avec priorité : Local SW cache > Backend API > TTS API
- **Ajouté** : Traductions du bouton "Écouter" / "Stop" dans les 16 langues
- **Ajouté** : Composant `UpdateNotification.jsx` - Notification élégante quand une nouvelle version est disponible
  - Design moderne avec gradient et animation
  - Traduit dans les 16 langues
  - Boutons "Mettre à jour" et "Plus tard"
  - Responsive (desktop et mobile)
- **Ajouté** : Centre d'aide complet (`HelpCenter.jsx`)
  - FAQ organisées par catégories (Usagers: Abonnements, Trajets, Compte / Chauffeurs: Inscription, Revenus, Application)
  - Chatbot IA GPT-4o-mini multilingue (répond dans la langue de l'utilisateur)
  - Endpoint backend `/api/help/chat` avec stockage des conversations
  - Bouton AIDE visible sur: page d'accueil (nav + flottant mobile), dashboard usager, dashboard chauffeur


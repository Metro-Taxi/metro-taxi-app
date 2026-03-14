# Métro-Taxi - Product Requirements Document

## 📋 Problème Original
Créer une plateforme web Métro-Taxi de mise en relation entre usagers abonnés et chauffeurs VTC. Les trajets sont gratuits car couverts par abonnement. Design moderne style Uber avec couleurs noir/jaune/blanc.

## 🏗️ Architecture
- **Frontend**: React 19, TailwindCSS, Leaflet/OpenStreetMap, Framer Motion, i18next
- **Backend**: FastAPI (Python), MongoDB, JWT Auth
- **Paiement**: Stripe (emergentintegrations library)
- **TTS**: OpenAI Text-to-Speech (emergentintegrations library)
- **Temps réel**: WebSocket

## 👥 User Personas
1. **Usager**: Cherche mobilité urbaine abordable via abonnement
2. **Chauffeur VTC**: Souhaite optimiser ses trajets avec passagers
3. **Admin**: Gère la plateforme, valide les chauffeurs

## ✅ Fonctionnalités Implémentées

### Section 1 - Inscription ✅
- [x] Inscription usager (nom, prénom, email, téléphone, mot de passe)
- [x] Inscription chauffeur (+ plaque, type véhicule, places, licence VTC)
- [x] Validation chauffeur par admin
- [x] Vérification email avec token sécurisé (MOCK)

### Section 2 - Abonnements ✅
- [x] 3 forfaits: 24h (7€), 1 semaine (17€), 1 mois (54€) - Prix arrondis
- [x] **Prix en devises locales** selon la langue (EUR, NOK, SEK, DKK, CNY, PKR)
- [x] Paiement Stripe (Visa, MasterCard, American Express)
- [x] Activation automatique après paiement
- [x] **Désactivation automatique des abonnements expirés** (toutes les 5 min)
- [x] **Dashboard admin des abonnements** avec stats et nettoyage manuel

### Section 3 - Écran Usager ✅
- [x] Carte géolocalisée avec véhicules disponibles
- [x] Affichage places libres et direction
- [x] Demande de trajet en un clic
- [x] Suggestions de transbordement
- [x] Progression du trajet avec timeline visuelle
- [x] Sélection destination sur carte

### Section 4 - Écran Chauffeur ✅
- [x] Carte avec usagers demandeurs
- [x] Accepter/Refuser demandes
- [x] Bouton connexion/déconnexion en ligne
- [x] Indicateur places restantes
- [x] Mise à jour progression trajet

### Section 5 - Algorithme Central ✅
- [x] Algorithme intelligent de matching (distance, direction, places, ETA)
- [x] Calcul de route optimale avec segments (1.5-3 km)
- [x] Maximum 2 transbordements
- [x] APIs: optimal-route, network-status, transfers, find-drivers

### Section 6 - Backend Admin ✅
- [x] Dashboard avec statistiques
- [x] Gestion chauffeurs (activer/désactiver/valider)
- [x] **Onglet Abonnements** avec actifs, expirés, expirant bientôt
- [x] Cartes virtuelles avec détails

### Section 7 - Landing Page ✅
- [x] Hero section avec CTA
- [x] **Slogan écologique**: "Système de déplacement intelligent par covoiturage"
- [x] **Message environnemental**: "Réduisez votre empreinte carbone"
- [x] Section vidéo avec voix off TTS dynamique
- [x] Section forfaits avec prix locaux arrondis
- [x] Section "Comment ça marche"
- [x] Section "Devenir Chauffeur VTC" avec revenus et avantages

### Section 8 - Internationalisation (i18n) ✅ (Mis à jour - 14/03/2026)
- [x] **Sélecteur de langue** sur la page d'accueil (9 langues)
- [x] **Détection automatique** de la langue du navigateur
- [x] **Langues supportées**:
  - 🇫🇷 Français (défaut)
  - 🇬🇧 English
  - 🇪🇸 Español
  - 🇵🇹 Português
  - 🇳🇴 Norsk (NOK)
  - 🇸🇪 Svenska (SEK)
  - 🇩🇰 Dansk (DKK)
  - 🇨🇳 中文 (CNY)
  - 🇵🇰 اردو (PKR)
- [x] **Traduction complète** de TOUTES les pages:
  - Landing page (héro, forfaits, fonctionnement, section chauffeurs)
  - Page de connexion
  - Page d'inscription usager
  - Page d'inscription chauffeur
- [x] **Voix off TTS** pour la vidéo dans chaque langue
- [x] **API TTS**: `/api/tts/voiceover` et `/api/tts/languages`
- [x] **Scripts TTS traduits** avec slogan écologique dans toutes les langues

## 📊 Statut Tests
- Backend: 100% ✅
- Frontend: 100% ✅

## 🔄 Backlog

### P0 - Prioritaire
- [ ] **Traduire les dashboards** (Admin, Usager, Chauffeur) - Partiellement traduit
- [ ] Connecter domaine `metro-taxi.com`

### P1 - Important
- [ ] Créer email professionnel `judeesouleymane@metro-taxi.com`
- [ ] Implémenter vérification email réelle (SendGrid/Resend)
- [ ] Vidéo promotionnelle AI (Sora 2) - script prêt

### P2 - Améliorations
- [ ] Notifications push mobiles
- [ ] Historique complet des trajets usager
- [ ] Système de notation chauffeur

## 🔑 Credentials Test
- Admin: admin@metrotaxi.fr / admin123
- User test: marie.test@example.com / test123

## 📁 Fichiers Clés
- `/app/backend/server.py` - API FastAPI avec algorithme central + TTS
- `/app/frontend/src/pages/Landing.js` - Page d'accueil multilingue
- `/app/frontend/src/i18n/` - Configuration i18n et traductions
- `/app/frontend/src/i18n/locales/*.json` - Fichiers de traduction
- `/app/scripts/video_script_v2.md` - Script vidéo pour future génération

## 🌍 Configuration i18n
```
/app/frontend/src/i18n/
├── index.js          # Configuration i18next (avec load: 'languageOnly')
└── locales/
    ├── fr.json       # Français
    ├── en.json       # English
    ├── es.json       # Español
    ├── pt.json       # Português
    ├── no.json       # Norsk
    ├── sv.json       # Svenska
    ├── da.json       # Dansk
    ├── zh.json       # 中文
    └── ur.json       # اردو
```

## 🐛 Bugs Corrigés (14/03/2026)
- [x] **Bug TTS**: Les scripts VIDEO_SCRIPTS avaient des entrées dupliquées cassant le dict Python
- [x] **Bug i18n**: Le détecteur de langue retournait "en-US@posix" au lieu de "en", causant un mismatch
- [x] **Fix**: Ajout de `load: 'languageOnly'` dans la config i18next
- [x] **Fix**: Ajout de `getBaseLanguage()` pour extraire le code de langue de base

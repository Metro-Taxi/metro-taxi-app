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
- [x] **Vérification email via Resend** (emails multilingues FR/EN/ES/DE/PT)

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
- [x] **Sélecteur de langue** sur la page d'accueil (13 langues)
- [x] **Détection automatique** de la langue du navigateur
- [x] **Badge POPULAIRE traduisible** (était en CSS, maintenant JSX)
- [x] **Concept PAR ABONNEMENT** mis en évidence dans toutes les langues
- [x] **Langues supportées**:
  - 🇫🇷 Français (défaut) - Prix: 6,99€, 16,99€, 53,99€
  - 🇺🇸 English (US) - Prix: $7.99, $18.99, $59.99
  - 🇬🇧 English (UK) - Prix: £5.99, £14.99, £45.99
  - 🇩🇪 Deutsch - Prix: 6,99€, 16,99€, 53,99€ (identique FR)
  - 🇳🇱 Nederlands - Prix: 6,99€, 16,99€, 53,99€
  - 🇪🇸 Español - Prix: 6,99€, 16,99€, 53,99€ (aligné FR)
  - 🇵🇹 Português - Prix: 6,99€, 16,99€, 53,99€ (aligné FR)
  - 🇳🇴 Norsk (NOK) - Prix: 79,99kr, 189,99kr, 599,99kr
  - 🇸🇪 Svenska (SEK) - Prix: 79,99kr, 189,99kr, 599,99kr
  - 🇩🇰 Dansk (DKK) - Prix: 54,99kr, 129,99kr, 409,99kr
  - 🇨🇳 中文 (CNY) - Prix: ¥54.99, ¥129.99, ¥419.99
  - 🇮🇳 हिन्दी (Hindi) - Prix: ₹629, ₹1,529, ₹4,859 (NOUVEAU)
  - 🇵🇰 ਪੰਜਾਬੀ (Punjabi) - Prix: ₨1,999, ₨4,799, ₨14,999 (remplace Ourdou)
- [x] **Revenus chauffeurs localisés** par devise :
  - EUR: 2 250 € - 3 000 € (max 7 500 €) - FR, DE, NL, ES, PT
  - GBP: £1,999 - £2,599 (max £6,499) - UK
  - NOK/SEK: 25 899 kr - 34 499 kr (max 86 249 kr)
  - DKK: 16 799 kr - 22 399 kr (max 55 999 kr)
  - CNY: ¥17,499 - ¥23,399 (max ¥58,499)
  - INR: ₹1,99,999 - ₹2,69,999 (max ₹6,74,999)
  - PKR: ₨629,999 - ₨839,999 (max ₨2,099,999)
- [x] **Traduction des dashboards** (en cours):
  - UserDashboard: Partiellement traduit
  - DriverDashboard: Partiellement traduit  
  - AdminDashboard: Import ajouté
- [x] **Voix off TTS** pour la vidéo dans chaque langue (13 langues)
- [x] **API TTS**: `/api/tts/voiceover` et `/api/tts/languages`
- [x] **Scripts TTS traduits** avec slogan écologique dans toutes les langues

## 📊 Statut Tests
- Backend: 100% ✅ (11/11 tests - iteration_4.json)
- Frontend: 100% ✅ (i18n complet testé)

## 🔄 Backlog

### P0 - Prioritaire
- [x] **Traduire les dashboards** (Admin, Usager, Chauffeur) ✅
- [ ] Connecter domaine `metro-taxi.com` (DNS chez Hostinger)

### P1 - Important  
- [x] Emails créés: jhs@metro-taxi.com, judeesouleymane@metro-taxi.com ✅
- [x] Implémenter vérification email réelle via **Resend** ✅
- [ ] Vidéo promotionnelle AI (Sora 2) - **Budget Emergent insuffisant** (~$5 requis)
- [ ] Vérifier domaine metro-taxi.com sur Resend pour envoi emails en production

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
- [x] **Bug Hero Subtitle**: Le concept "PAR ABONNEMENT" n'était pas visible dans plusieurs langues (EN, DE, NL, ZH, EN-GB)
  - **Cause**: Le code prenait les 2 derniers mots du sous-titre qui ne correspondaient pas au concept d'abonnement dans toutes les langues
  - **Solution**: Ajout d'une clé de traduction dédiée `hero.subtitleHighlight` dans les 13 fichiers de traduction pour mettre en évidence le concept d'abonnement dans chaque langue
- [x] **Bug i18n en-GB**: La configuration `load: 'languageOnly'` empêchait le chargement du fichier en-GB.json
  - **Cause**: i18next réduisait `en-GB` à `en`, utilisant le fichier américain
  - **Solution**: Changement de `load: 'all'` et ajout de `nonExplicitSupportedLngs: true`
- [x] **Alignement prix ES/PT**: Les prix espagnols et portugais n'étaient pas alignés sur la France
  - **Solution**: Mise à jour des fichiers es.json et pt.json avec les mêmes prix que fr.json (6,99€, 16,99€, 53,99€)
  - **Revenus chauffeurs**: 2 250€ - 3 000€ (max 7 500€)
- [x] **Badge POPULAIRE non traduit**: Le badge utilisait un pseudo-élément CSS `::before` non traduisible
  - **Solution**: Remplacement par un élément JSX `<span className="popular-badge">` avec clé de traduction `pricing.popularBadge`
- [x] **Traduction dashboards**: Ajout des traductions dans les 3 dashboards (User, Driver, Admin)
  - **Solution**: Remplacement du texte en dur par des clés de traduction `t('common.xxx')` et `t('dashboard.admin.xxx')`

## 📺 Génération Vidéo Sora 2
- **Statut**: Tentative échouée (budget Emergent LLM dépassé)
- **Vidéo existante**: `/app/frontend/public/videos/metro-taxi-promo.mp4` (4.9 MB)
- **Script prêt**: `/app/scripts/video_script_v2.md`
- **Pour générer**: Ajouter du budget sur Emergent (Profile → Universal Key → Add Balance)

## 🌐 Domaine Personnalisé
- **Domaine**: metro-taxi.com (chez Hostinger)
- **Emails créés**: jhs@metro-taxi.com, judeesouleymane@metro-taxi.com
- **À créer**: contact@metro-taxi.com
- **Configuration DNS**: En attente (voir instructions deployment_agent)

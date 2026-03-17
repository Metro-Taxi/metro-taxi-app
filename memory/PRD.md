# Métro-Taxi - Product Requirements Document

## 📋 Résumé
Plateforme de mise en relation usagers/chauffeurs VTC avec abonnements. Trajets gratuits couverts par l'abonnement.

## 🏗️ Stack Technique
- **Frontend**: React 19, TailwindCSS, Leaflet, i18next (16 langues)
- **Backend**: FastAPI, MongoDB, JWT Auth
- **Paiements**: Stripe Checkout + Stripe Connect Express
- **Emails**: Resend (vérification + notifications paiement) ✅ Domaine vérifié
- **TTS**: OpenAI (Emergent LLM Key)
- **PWA**: Service Worker, Manifest, Cache hors ligne ✅ NOUVEAU

## ✅ Fonctionnalités Complètes

### Progressive Web App (PWA) ✅ (17/03/2026)
- **Manifest.json** : Configuration complète avec nom, icônes, thème
- **Service Worker** : Cache offline, network-first strategy
- **Icônes** : 8 tailles (72x72 → 512x512) + apple-touch-icon + favicon
- **Bannière d'installation** : Détecte mobile, affiche après 5s, traduit FR/EN
- **Meta tags** : Open Graph, Apple Web App, Microsoft tiles

### Système d'Emails Resend ✅ (17/03/2026)
- **Domaine vérifié** : metro-taxi.com
- **Expéditeur** : noreply@metro-taxi.com
- **DNS configurés** : SPF, DKIM, MX (eu-west-1)
- **Fonctionnel** : Emails de test envoyés avec succès

### Internationalisation (i18n) ✅
- **16 langues** : FR, EN, EN-GB, ES, PT, DE, NL, SV, NO, DA, ZH, HI, PA, AR, RU, IT
- **Devises locales** : € (Europe), ¥ (Chine), ₹ (Inde), £ (UK), etc.
- **Voix off TTS** : Vidéo promotionnelle dans la langue sélectionnée

### Système de Revenus Chauffeurs ✅
- **Tarif** : 1,50€/km
- **Règle Métro-Taxi** : SEULS les km avec usagers à bord sont comptés
- **Période** : Du 1er au dernier jour du mois
- **Virement** : Automatique le 10 du mois suivant via Stripe Connect

### Email de Notification Paiement ✅
- Email automatique envoyé au chauffeur lors du virement
- Templates FR/EN avec design Métro-Taxi

### Interface Chauffeur "Mes Revenus" ✅
- Onglet Revenus : Mois en cours, km, trajets, tarif, cumul total
- Onglet Stripe Account : Statut compte, vérification, infos bancaires
- Onglet Historique : Virements effectués

## ⚙️ Configuration

**Stripe** : ✅ `sk_test_51TAPT2BJV...`
**Resend** : ✅ Domaine metro-taxi.com vérifié

## 🔑 Credentials
- Admin: admin@metrotaxi.fr / admin123
- Driver: jean.dupont.test@example.com / test123456

## 📊 Tests
- Backend: 100% ✅
- Frontend: 100% ✅
- PWA: 100% ✅

## 🔄 Prochaines Étapes

### P0 - Immédiat
- [x] ~~Vérifier domaine Resend~~ ✅ FAIT
- [x] ~~Installer PWA~~ ✅ FAIT

### P1 - Important
- [ ] Chauffeur complète vérification Stripe
- [ ] Connecter domaine metro-taxi.com en production

### P2 - Améliorations
- [ ] Notifications push (base service worker en place)
- [ ] Historique trajets détaillé
- [ ] Système de notation

## 📅 Dernière Mise à Jour
**17/03/2026**
- ✅ Domaine Resend vérifié (metro-taxi.com)
- ✅ PWA installé : manifest.json, sw.js, icônes, bannière d'installation
- ✅ Vérification visuelle des traductions dans 16 langues confirmée

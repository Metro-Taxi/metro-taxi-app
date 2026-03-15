# Métro-Taxi - Product Requirements Document

## 📋 Résumé
Plateforme de mise en relation usagers/chauffeurs VTC avec abonnements. Trajets gratuits couverts par l'abonnement.

## 🏗️ Stack Technique
- **Frontend**: React 19, TailwindCSS, Leaflet, i18next (16 langues)
- **Backend**: FastAPI, MongoDB, JWT Auth
- **Paiements**: Stripe Checkout + Stripe Connect Express
- **TTS**: OpenAI (Emergent LLM Key)
- **Email**: Resend

## ✅ Fonctionnalités Complètes

### Système de Revenus Chauffeurs ✅
- **Tarif** : 1,50€/km
- **Calcul** : Total km du 1er au dernier jour du mois (tous usagers confondus)
- **Virement** : Automatique le 10 du mois suivant

### Interface Chauffeur "Mes Revenus" ✅ (NOUVEAU)
- **Onglet Revenus** : Mois en cours, km, trajets, tarif, cumul total
- **Onglet Stripe Account** : Statut compte, vérification, infos bancaires
- **Onglet Historique** : Virements effectués

### APIs Stripe Connect ✅
| Route | Description |
|-------|-------------|
| GET /api/stripe-connect/config | Configuration Stripe |
| POST /api/drivers/stripe-connect/create-account | Créer compte Express |
| GET /api/drivers/stripe-connect/status | Statut du compte |
| GET /api/drivers/earnings | Revenus du chauffeur |
| GET /api/drivers/payouts | Historique des virements |

### Internationalisation ✅
- 16 langues triées alphabétiquement
- Inscription chauffeur traduite
- Interface revenus traduite

## ⚙️ Configuration Stripe

**Clé configurée** : ✅ `sk_test_51TAPT2BJV...`
**Compte test créé** : `acct_1TBJzhB1CsXOKYfE` (en attente de vérification)

## 🔑 Credentials
- Admin: admin@metrotaxi.fr / admin123
- Driver: jean.dupont.test@example.com / test123456

## 📊 Tests
- Backend: 100% ✅
- Frontend: 100% ✅

## 🔄 Prochaines Étapes

### P0 - Immédiat
- [ ] Chauffeur complète vérification Stripe (lien onboarding)

### P1 - Important
- [ ] Vérifier domaine metro-taxi.com sur Resend
- [ ] Connecter domaine personnalisé

### P2 - Améliorations
- [ ] Notifications push
- [ ] Historique trajets détaillé
- [ ] Système de notation

## 📅 Dernière Mise à Jour
**15/03/2026** - Interface revenus chauffeur complète avec 3 onglets

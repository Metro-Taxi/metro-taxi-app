# Métro-Taxi - Product Requirements Document

## 📋 Problème Original
Plateforme web Métro-Taxi de mise en relation usagers/chauffeurs VTC. Trajets gratuits couverts par abonnement.

## 🏗️ Architecture
- **Frontend**: React 19, TailwindCSS, Leaflet, i18next (16 langues)
- **Backend**: FastAPI, MongoDB, JWT Auth
- **Paiements**: Stripe Checkout + **Stripe Connect Express**
- **TTS**: OpenAI (Emergent LLM Key)
- **Email**: Resend

## ✅ Fonctionnalités Implémentées

### Système de Revenus Chauffeurs ✅
- **Tarif** : 1,50€/km (trajets + déplacement vers pickup)
- **Virement automatique** : le 10 de chaque mois
- **Stripe Connect Express** : Comptes chauffeurs + virements SEPA

### APIs Stripe Connect ✅
| Route | Description |
|-------|-------------|
| GET /api/stripe-connect/config | Configuration Stripe |
| POST /api/drivers/stripe-connect/create-account | Créer compte chauffeur |
| GET /api/drivers/stripe-connect/status | Statut du compte |
| POST /api/admin/stripe-connect/process-payout/{id} | Virement individuel |
| POST /api/admin/stripe-connect/process-all-payouts | Tous les virements |

### Flux de Paiement Chauffeur
1. Chauffeur s'inscrit avec IBAN/BIC
2. Il crée son compte Stripe Connect via l'API
3. Il complète la vérification sur Stripe (identité + coordonnées bancaires)
4. Ses revenus sont calculés automatiquement (km × 1,50€)
5. Le 10 du mois, virements automatiques vers son compte bancaire

## ⚙️ Configuration Stripe Connect

**Clé configurée** : ✅ `sk_test_51TAPT2BJV...` (mode test)

**Compte chauffeur test créé** :
- ID: `acct_1TBJzhB1CsXOKYfE`
- Statut: En attente de vérification
- Lien onboarding: Le chauffeur doit compléter sa vérification

## 🔑 Credentials
- Admin: admin@metrotaxi.fr / admin123
- Driver test: jean.dupont.test@example.com / test123456

## 🔄 Prochaines Étapes

### P0 - Immédiat
- [ ] Chauffeur complète la vérification Stripe (lien onboarding)
- [ ] Tester un virement réel après vérification

### P1 - Important
- [ ] Interface frontend pour les revenus chauffeurs
- [ ] Vérifier domaine Resend

### P2 - Améliorations
- [ ] Notifications push
- [ ] Historique trajets détaillé

## 📅 Dernière Mise à Jour
**15/03/2026** - Stripe Connect Express intégré et fonctionnel

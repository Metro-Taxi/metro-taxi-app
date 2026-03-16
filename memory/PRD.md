# Métro-Taxi - Product Requirements Document

## 📋 Résumé
Plateforme de mise en relation usagers/chauffeurs VTC avec abonnements. Trajets gratuits couverts par l'abonnement.

## 🏗️ Stack Technique
- **Frontend**: React 19, TailwindCSS, Leaflet, i18next (16 langues)
- **Backend**: FastAPI, MongoDB, JWT Auth
- **Paiements**: Stripe Checkout + Stripe Connect Express
- **Emails**: Resend (vérification + notifications paiement)
- **TTS**: OpenAI (Emergent LLM Key)

## ✅ Fonctionnalités Complètes

### Système de Revenus Chauffeurs ✅
- **Tarif** : 1,50€/km
- **Règle Métro-Taxi** : SEULS les km avec usagers à bord sont comptés
  - Compteur démarre quand 1er usager embarque (status = "in_progress")
  - Continue avec plusieurs usagers (trajets partagés)
  - S'arrête quand dernier usager descend (status = "completed")
- **Période** : Du 1er au dernier jour du mois
- **Virement** : Automatique le 10 du mois suivant

### Email de Notification Paiement ✅ (NOUVEAU)
- Email automatique envoyé au chauffeur lors du virement
- Contenu : Montant, km parcourus, nombre de trajets, période, date
- Templates FR/EN avec design Métro-Taxi

### Interface Chauffeur "Mes Revenus" ✅
- **Onglet Revenus** : Mois en cours, km, trajets, tarif, cumul total
- **Onglet Stripe Account** : Statut compte, vérification, infos bancaires
- **Onglet Historique** : Virements effectués

### Tracking Kilométrique ✅
- `km_start_location` : Position quand usager embarque
- `km_with_user` : Km calculés avec usager(s) à bord
- Différenciation claire vs autres plateformes VTC

## ⚙️ Configuration

**Stripe** : ✅ `sk_test_51TAPT2BJV...`
**Compte test** : `acct_1TBJzhB1CsXOKYfE` (en attente vérification)

## 🔑 Credentials
- Admin: admin@metrotaxi.fr / admin123
- Driver: jean.dupont.test@example.com / test123456

## 📊 Tests
- Backend: 100% ✅
- Frontend: 100% ✅

## 🔄 Prochaines Étapes

### P0 - Immédiat
- [ ] Chauffeur complète vérification Stripe

### P1 - Important
- [ ] Vérifier domaine Resend pour emails en production
- [ ] Connecter domaine metro-taxi.com

### P2 - Améliorations
- [ ] Notifications push
- [ ] Historique trajets détaillé
- [ ] Système de notation

## 📅 Dernière Mise à Jour
**16/03/2026**
- Compteur km automatisé : démarre à l'embarquement, s'arrête à la descente
- Emails de notification de paiement ajoutés
- Description tarif mise à jour dans 16 langues

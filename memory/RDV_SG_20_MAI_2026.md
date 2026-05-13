# 🏦 RDV SG — Mercredi 20 mai 2026 (Installation crédentiales e-Transactions)

**Avec** : Conseillère SG + Technicien banque
**Pour** : Judée Mané — Métro-Taxi
**Préparé par** : Charly · 13 mai 2026

---

## 🎯 OBJECTIF DU RDV

Récupérer les **4 informations indispensables** pour migrer Métro-Taxi de Stripe vers le système de paiement direct **Crédit Agricole / Société Générale e-Transactions** (HMAC SHA256).

---

## 📋 LISTE DES 4 CRÉDENTIALES À DEMANDER

### 1️⃣ Identifiant marchand (Merchant ID)
- Aussi appelé : `vads_site_id` ou `PBX_SITE`
- Format : généralement 7-8 chiffres
- C'est ton numéro de compte commerçant sur la plateforme bancaire

### 2️⃣ Clé secrète HMAC SHA256
- Aussi appelée : `vads_secret_key` ou `signature_key`
- C'est une chaîne longue (32-64 caractères)
- ⚠️ **JAMAIS la partager par email — la demander en main propre ou via un canal sécurisé bancaire**
- Sert à signer toutes les requêtes vers la banque

### 3️⃣ URL du serveur de paiement
- Aussi appelée : `gateway_url` ou `payment_endpoint`
- Format : `https://systempay.cyberpluspaiement.com/vads-payment/` (ou équivalent SG)
- C'est l'URL vers laquelle tes utilisateurs seront redirigés pour payer

### 4️⃣ URL et clé de notification (IPN / Webhook)
- Aussi appelée : `notification_url` ou `IPN_endpoint`
- C'est l'URL **chez nous** (Métro-Taxi) que la banque appellera pour nous confirmer un paiement
- Format de notre côté : `https://metro-taxi.com/api/payments/sg-webhook`
- ⚠️ Le technicien doit nous donner la **clé de validation** pour vérifier que la notification vient bien de la banque

---

## 🛠️ INFORMATIONS À DONNER AU TECHNICIEN

Pour qu'il configure correctement de son côté, il a besoin de **TES** URLs (chez Métro-Taxi) :

| Type d'URL | Valeur à fournir |
|-----------|------------------|
| **URL de retour succès** (après paiement OK) | `https://metro-taxi.com/payment/success` |
| **URL de retour échec** (après paiement KO) | `https://metro-taxi.com/payment/cancel` |
| **URL de notification serveur (IPN)** | `https://metro-taxi.com/api/payments/sg-webhook` |
| **Email de contact technique** | `contact@metro-taxi.com` |
| **Nom du commerce** | `Métro-Taxi` |
| **Activité** | `Plateforme de covoiturage par abonnement` |
| **Code MCC** | `4121` (Taxicabs and Limousines) |

---

## ❓ QUESTIONS UTILES À POSER AU TECHNICIEN

1. **Mode test vs production** : peut-on avoir des clés de test (sandbox) AVANT de passer en prod ?
2. **Frais bancaires** : quel est le coût par transaction (% + frais fixes) pour notre activité ?
3. **Délai de versement** : sous combien de jours les paiements arrivent-ils sur notre compte pro ?
4. **3D Secure** : est-il automatique ou à configurer ? (Important en 2026, c'est obligatoire pour B2C)
5. **Remboursements** : peut-on rembourser un abonné directement depuis l'API ou faut-il passer par l'interface web ?
6. **Abonnements récurrents** : la plateforme supporte-t-elle les paiements récurrents mensuels nativement (pour notre plan 1 mois à 53,99€) ou faut-il un système de re-débit programmé ?
7. **Webhook signature** : quel algorithme exactement ? HMAC SHA256 avec quel encodage (hex/base64) ?
8. **Documentation API** : où trouver la doc technique complète (manuel intégrateur) ?

---

## 🚨 IMPORTANT — SÉCURITÉ DES CLÉS

Quand tu auras reçu les clés :

1. ❌ **NE LES TAPE JAMAIS** en clair dans un email, WhatsApp ou SMS
2. ❌ **NE LES STOCKE JAMAIS** dans Google Drive / Dropbox / iCloud
3. ✅ **Stocke-les UNIQUEMENT** dans :
   - Le fichier `/var/www/metro-taxi-app/backend/.env` sur ton VPS (déjà chiffré au repos)
   - Un gestionnaire de mots de passe sérieux (Bitwarden, 1Password, KeePass)
4. ✅ Pour me les transmettre à moi (Charly) : **utilise la fonction ask_human directement dans Emergent** (c'est chiffré et sécurisé)

---

## 📝 APRÈS LE RDV (mercredi 20 mai)

Quand tu auras récupéré les clés :
1. Ouvre Emergent
2. Lance une nouvelle session avec moi (Charly)
3. Dis-moi simplement : *"Charly, j'ai les clés SG, on lance la migration Stripe → e-Transactions"*
4. Je te demanderai les clés via `ask_human` (sécurisé)
5. Je code l'intégration en ~2-3h
6. On teste avec un paiement de 0,01€ en sandbox
7. On passe en prod

---

*Préparé par Charly · 13 mai 2026 · À imprimer ou consulter sur ton portable le jour du RDV*

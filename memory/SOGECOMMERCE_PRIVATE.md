# 🔒 IDENTIFIANTS SOGECOMMERCE — DOCUMENT ULTRA-CONFIDENTIEL

**⚠️ NE JAMAIS PUBLIER, NE JAMAIS COMMIT DANS UN REPO PUBLIC, NE JAMAIS PARTAGER PAR EMAIL**

Reçus le 29/05/2026 par Capitaine Judée Souleymane Nazim après signature contrat Société Générale.

---

## 🏪 Boutique Marchande

| Paramètre | Valeur |
|---|---|
| **Identifiant boutique** | `43696939` |
| **Nom boutique** | METRO-TAXI |
| **Mode actuel** | TEST (passage en PROD = après validation tests CB) |
| **URL Back Office** | https://sogecommerce.societegenerale.eu/vads-merchant/ |
| **URL Documentation** | https://sogecommerce.societegenerale.eu/doc/ |
| **URL Plugins CMS** | https://sogecommerce.societegenerale.eu/doc/fr-FR/plugins/ |
| **URL Support technique** | https://support.sogecommerce.com/hc/fr/requests/new |

## 👤 Compte utilisateur Back Office

| Paramètre | Valeur |
|---|---|
| **ID utilisateur** | `jsouleymanenazim` |
| **Mot de passe TEMPORAIRE** ⚠️ | `O8bl1tJowes0` |
| **Code de sécurité** | À définir par Judée au 1er login |

**ACTION REQUISE** : Changer le mot de passe temporaire OBLIGATOIREMENT au premier login.

## 📜 Contrats actifs

| Contrat | Référence | Statut |
|---|---|---|
| Apple Pay | `sogecommerce-99728222` | À activer (Paramétrage > Société > Contrats) |
| CB principal | À confirmer après login | — |

---

## 🛠️ Étapes techniques pour passage en PRODUCTION

D'après l'email SG :
1. ✅ Boutique créée en mode TEST
2. ⏳ Effectuer des transactions test avec cartes de test (liste dans doc SG)
3. ⏳ Aller dans Paramétrage > Boutiques > [METRO-TAXI] > onglet Clés
4. ⏳ Cliquer "Génération de la clé de production"
5. ⏳ SG analyse les tests → autorise la génération
6. ⏳ Récupérer la clé de PRODUCTION
7. ⏳ Intégrer dans `/app/backend/routes/payments.py` (Emergent backend)

---

## 🔑 Clés à récupérer après 1er login

À aller chercher dans **Paramétrage > Boutiques > METRO-TAXI > onglet Clés** :

- [x] **Identifiant boutique** : `43696939` ✅
- [x] **Clé de TEST API formulaire (V1/V2/SOAP)** : `uqhmpvNV0v45QpNI` ✅ (récupérée le 29/05/2026 ~15h50)
- [ ] **Clé HMAC SHA-256 TEST** : à vérifier dans onglet "Clés d'API REST"
- [ ] **Clé de production** : "À générer" — bouton actuellement DÉSACTIVÉ (4 lignes de tests CB à valider d'abord)
- [ ] **Clé HMAC SHA-256 PROD** : (à générer APRÈS validation tests)

### 🧪 Tests CB requis avant génération clé production

D'après le Back Office, il faut valider **4 transactions test** sur la table suivante :

| # | CB | Mastercard | Maestro | Visa Electron |
|---|---|---|---|---|
| 1 | 4970100000000055 | 5970100300000067 | 5000550000000052 | 4917480000000057 |
| 2 | 4970100000000063 | 5970100300000075 | 5000550000000060 | 4917480000000065 |
| 3 | 4970100000000071 | 5970100300000083 | 5000550000000078 | 4917480000000073 |
| 4 | 4970115000000228 | 5100010000000106 | 5000551000000415 | 4917481000000402 |

Les paiements de test sont purgés au bout de 30 jours. Paramètre `vads_page_action` doit être à `PAYMENT` ou `REGISTER_PAY`.

### ⚠️ Configuration manquante (à faire dans Métro-Taxi avant production)

- **URL de notification IPN** : Statut "Non paramétrée" actuellement
  - À configurer dans Paramétrage > Règles de notifications
  - Devra pointer vers : `https://metro-taxi.com/api/payments/sogecommerce/ipn` (endpoint à créer côté backend Métro-Taxi)


---

## 📋 Intégration Métro-Taxi (à coder dans payments.py)

D'après docs Sogecommerce (vads-merchant) :
- **Méthode privilégiée** : Formulaire de paiement embarqué (REST API)
- **Endpoint test** : `https://sogecommerce.societegenerale.eu/vads-payment/`
- **Endpoint prod** : Même URL, différencié par l'identifiant boutique + clé
- **Signature** : SHA-256 HMAC sur les paramètres triés
- **Retour utilisateur** : URL de redirection à configurer (`vads_url_return`)
- **Notification IPN** : URL serveur-à-serveur pour confirmation paiement (`vads_url_check`)

---

## ⚠️ Sécurité opérationnelle

- ❌ Ne JAMAIS hardcoder ces clés dans le code source
- ✅ TOUJOURS via variables d'environnement (.env)
  - `SOGECOMMERCE_SHOP_ID=43696939`
  - `SOGECOMMERCE_TEST_KEY=...`
  - `SOGECOMMERCE_PROD_KEY=...`
  - `SOGECOMMERCE_HMAC_TEST=...`
  - `SOGECOMMERCE_HMAC_PROD=...`
- ✅ Ajouter les variables au pod environment Emergent (jamais en clair dans le repo Git)

---

## 💰 Économie estimée vs Stripe

D'après les analyses précédentes :
- **Stripe** : 1,4% + 0,25€ par transaction (Europe CB)
- **Sogecommerce** : ~0,5% + frais forfaitaires + 3€/mois abonnement Back Office
- **Volume estimé Métro-Taxi an 1** : ~80 000 transactions à 49€ moy
- **Économie annuelle estimée** : **~11 000 €/an** ✅

---

*Document créé le 29/05/2026 à 15h12 par Charly. Capitaine Judée a reçu les identifiants par email de la banque.*

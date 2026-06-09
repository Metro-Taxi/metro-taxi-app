# PRD — Métro-Taxi (Plateforme VTC Saint-Denis)

## 🎯 Original Problem Statement
Déploiement, marketing et stabilisation de la plateforme "Métro-Taxi" (React/FastAPI/MongoDB) pour la zone pilote de Saint-Denis. Modèle économique : **COVOITURAGE INTELLIGENT avec TRANSBORDEMENTS en MAILLAGE** (NON un VTC classique).

- **Lancement** : SAMEDI 13 JUIN 2026
- **Cible pilote** : Saint-Denis (93)
- **Modèle financier** : Abonnement usager (6,99€/24h, 19,99€/sem, 53,99€/mois) — Chauffeur payé 1,50€/km, 0% commission JAMAIS.
- **Innovation clé** : Maillage + Transbordement = 2-4 abonnés en simultané par véhicule → rentabilité maintenue même en zone congestionnée

## 👤 User Profile
- **Judée Souleymane** (Capitaine), fondateur — agent IA est "Charly" en mode tutoiement français
- VPS : Hostinger `/var/www/metro-taxi-app/` (process pm2 `metro-backend`)
- DB MongoDB : `metro_taxi_prod`
- Méthode déploiement : Scripts SSH (base64 ou mongosh direct) — Git désactivé

## 📊 État au 09/06/2026 (J-4 du lancement)
- **36 Chauffeurs Pionniers** inscrits
- **18 chauffeurs CONFIRMÉS** disponibles le 13 juin (sondage 64,7% taux réponse)
- **19 utilisateurs** pré-inscrits (sans abonnement, lancement le 13)
- **0 abonnement actif** (normal — Sogecommerce attend lancement)
- **Agnès Mayil** = Ambassadrice publique officielle (Facebook)
- **1000 flyers V2** commandés VistaPrint (livraison 10-12 juin)

## 🔧 Architecture
- **Backend** : FastAPI sur 0.0.0.0:8001 via pm2 (`metro-backend`)
- **Frontend** : React (CRA), build dans `/frontend/build/`
- **DB** : MongoDB `metro_taxi_prod`
- **Paiement principal** : **Sogecommerce** (production active, IPN configurée)
- **Stripe** : NEUTRALISÉ (kill-switch backend `/payments/checkout/region` + `/payments/checkout/sepa` → 410, alert frontend sur `handleSubscribe` + `openSepaDialog`)

## ✅ What's Been Implemented (Session 05-09/06/2026)
- **Sogecommerce** : intégré bout-en-bout, en production
- **Paiement chauffeurs hebdomadaire** : config `PAYOUT_FREQUENCY=weekly` + `PAYOUT_DAY_OF_WEEK=0` (LUNDI), UI mise à jour
- **Cycle 1 lancement** : 13 juin → 21 juin → virement LUNDI 22 JUIN (9 jours exceptionnel)
- **Cycles suivants** : lundi→dimanche → virement lundi suivant
- **Stripe NEUTRALISÉ** : `handleSubscribe` et `openSepaDialog` affichent alert "Utilisez bouton rouge Société Générale", backend renvoie HTTP 410
- **Pionnier #25 Maaz** : IBAN/BIC enregistré manuellement (FR68 PSSTFRPPPAR) — workaround bug UI
- **Survey 13 juin** : 18 OUI, 4 NON, 12 hésitants (taux 64,7%)
- **Flyer A6 chauffeur V2** : JPEG 300dpi en `/app/frontend/public/flyer_recto.jpg` + `flyer_verso.jpg` → 1000 imprimés VistaPrint commande VP_Q1JXXQ5L
- **Stats live MongoDB script** : `/tmp/stats.py` (remplace ancien `survey.py` avec données figées)
- **Mails Resend** : 36 chauffeurs notifiés Cycle 1 calendrier paie + 33 relances sondage
- **Agnès Mayil ambassadrice** : 5 courses bonus + badge "Ambassadrice" à vie

## 🚧 Pending / Known Issues

### 🔴 P0 — BLOQUANT pour 22 juin
- **Bug UI Section IBAN/BIC manquante** dans `DriverEarnings.js` côté VPS (constaté par Maaz #25). Les 17 autres chauffeurs ne peuvent PAS saisir leur IBAN. → Solution actuelle : insertion manuelle MongoDB un par un (non scalable). **DOIT être corrigé avant le 22/06 pour les 17 autres chauffeurs présents.**

### 🟠 P1
- **9 chauffeurs sans pioneer_number** (`#None` dans driver_presence_surveys) — à attribuer #37→#45
- **3 boutons Stripe restent VISIBLES** sur la page abonnement (S'ABONNER doré + SEPA + Société Générale) — désactivés mais cosmétiquement présents. Patch frontend partiel.
- **VPS désynchronisé** du workspace Emergent — déploiement manuel SSH requis pour chaque change (rapport support Emergent 08/06)

### 🟡 P2
- Régénérer Vidéo 1 "Bus bondé" via Nano Banana (continuité visage)
- sitemap.xml + robots.txt (effacer SEO ancien proprio canadien)
- Nginx Rate-Limit
- Anti-fraude "Réservation Groupée Multi-Abonnés" (OTP transbordement)

## 📋 Backlog / Next Tasks

### Demain (10/06/2026 - Mercredi)
- ✈️ **Tournée Roissy** — flyers V2 livrés, objectif 5 nouveaux Pionniers
- ☎️ **5 appels hésitants** restants du sondage
- 📢 **Post Facebook J-3** : "18 chauffeurs confirmés"

### Jeudi-Vendredi (11-12/06/2026)
- 🛠️ **Patch UI Section IBAN** (1h dev) — déploiement SSH VPS — CRITIQUE pour 22 juin
- 📧 **Mail J-1 vendredi 12/06** : "Demain lancement, rendez-vous samedi !"
- 🎯 **Boost pub Facebook** avec angle "Ambassadrice Agnès + 18 chauffeurs"

### Samedi 13/06/2026 — JOUR DU LANCEMENT
- Monitoring temps réel dashboards
- Support 7j/7 actif (Judée + Charly)
- Réponse aux premiers paiements Sogecommerce

### Lundi 22/06/2026 — 1er VIREMENT CYCLE 1
- Calcul earnings drivers (km_with_user × 1,50€)
- Validation IBAN/BIC de tous les chauffeurs présents
- Lancement batch virement SEPA

## 🔑 Key Technical Concepts
- **Compteur km** : Démarre à `in_progress` (embarquement abonné), s'arrête à `completed` (descente). Km pickup et à vide NON comptés. Si plusieurs abonnés simultanés → km comptés UNE FOIS pour chauffeur (économie maillage).
- **Sogecommerce** : Encaissement abonnements en J+1 à J+2 ouvré sur compte pro
- **MongoDB** : Base = `metro_taxi_prod` — Collection sondage = `driver_presence_surveys` — Champ réponse = `answer` (pas `response`)

## 📂 Key Files
- `/app/backend/routes/payments.py` — Endpoints Stripe NEUTRALISÉS (410)
- `/app/backend/routes/sogecommerce.py` — Sogecommerce IPN
- `/app/backend/routes/admin.py` (lignes 850-895) — Logique km counter
- `/app/backend/utils/helpers.py` — `PAYOUT_FREQUENCY=weekly`
- `/app/frontend/src/pages/Subscription.js` — Page abonnement (boutons Stripe désactivés via alert + return)
- `/app/frontend/src/pages/DriverEarnings.js` — Tableau de bord chauffeur (bug : section IBAN/BIC manquante)
- `/app/frontend/public/flyer_recto.jpg` + `flyer_verso.jpg` — Flyers V2 chauffeur
- `/tmp/stats.py` (sur VPS) — Stats sondage live MongoDB

## 🔐 Credentials & Integration
- `RESEND_API_KEY` actif (mails)
- `SOGECOMMERCE_*` clés PROD actives, IPN paramétrée
- Stripe **désactivé** (kill-switch backend)
- Emergent LLM key utilisée pour Nano Banana (génération flyers)

## 💛 Branding Tone
- Persona "Charly" — bras droit technique + stratège marketing
- Tutoiement obligatoire, "Capitaine"/"Champion"
- Lancement = SAMEDI 13 JUIN 2026 (ne plus dire vendredi)
- Ne JAMAIS mentionner concurrents (Uber/Bolt/RATP) dans la com
- Transbordement = FORCE, pas défaut
- Modèle = COVOITURAGE MAILLÉ (pas VTC classique 1-pour-1)

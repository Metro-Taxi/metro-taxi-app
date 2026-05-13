# 📋 BRIEF JURIDIQUE — MÉTRO-TAXI

**Pour** : Maître [à compléter] · **Cabinet** : Parallel Avocats — Paris
**De** : Judée Mané (fondateur de Métro-Taxi)
**Date du RDV** : [à compléter]
**Durée du brief** : ~15 min de lecture · 1h de RDV recommandée pour le 1er entretien
**Préparé par** : Charly (CTO/bras droit technique de Métro-Taxi)

---

## 🎯 EN UNE PHRASE

**Métro-Taxi est une plateforme de mise en relation entre usagers abonnés et chauffeurs VTC déjà en activité, basée sur un système de covoiturage à maillage intelligent (transbordements adaptatifs) — modèle économique 0% de commission.**

---

## 1️⃣ POURQUOI VOUS (Parallel Avocats) ?

Notre choix n'est pas fortuit :
- 🏆 Vous avez **défendu et fait valider juridiquement le modèle Citygo contre Heetch** en matière de concurrence déloyale.
- ✅ Le jugement Citygo (covoiturage validé vs travail dissimulé / VTC déguisé) est **directement applicable à notre modèle**.
- 🎯 Nous voulons sécuriser notre dépôt INPI ET notre lancement commercial **avant d'atteindre 150 chauffeurs**.

---

## 2️⃣ MODÈLE ÉCONOMIQUE

### Pour les **usagers (abonnés)** :
- 3 plans d'abonnement par carte bancaire :
  - **24h** : 6,99€ (plafonné à 5 trajets max — anti-abus)
  - **1 semaine** : 16,99€ — trajets illimités
  - **1 mois** : 53,99€ — trajets illimités
- ⚠️ **Tarif Membre Fondateur 53,99€/mois verrouillé à vie** pour les 9 premiers usagers (engagement contractuel public)
- L'abonné NE PAYE PAS le trajet à la course. Il a un "passe".

### Pour les **chauffeurs (VTC professionnels)** :
- **Rémunération : 1,50 €/km parcouru AVEC AU MOINS UN ABONNÉ MÉTRO-TAXI À BORD**
- ❌ **Pas de commission** prélevée par la plateforme
- ❌ **Pas de promesse de revenu mensuel** (uniquement la formule contractuelle ci-dessus)
- 💰 Virement bancaire SEPA mensuel **le 10 du mois suivant**
- 🎁 **Bonus pionnier 1,55€/km TEMPORAIRE** pour les 100 premiers chauffeurs en zone pilote (Paris + 92/93/94) — communiqué comme temporaire

### Notre revenu (Métro-Taxi) :
- 100% des abonnements payés par les usagers
- Nous reversons ensuite 1,50€/km aux chauffeurs sur la base des km mesurés (GPS embarqué dans l'app)
- Le delta entre abonnements et reversements = notre marge brute

### ✅ Argument juridique fort :
**Nous ne sommes PAS Uber.** Nous ne vendons pas de "courses" individuelles. Nous vendons un "passe de mobilité" (abonnement). Les chauffeurs sont **rémunérés selon une formule fixe et publique**, jamais sur la course individuelle. Cela renforce le statut de plateforme de mise en relation pure (comme Citygo), pas d'opérateur de transport.

---

## 3️⃣ MODÈLE TECHNIQUE — ALGORITHME DE TRANSBORDEMENT ADAPTATIF

### 🧠 Le cœur du modèle (innovation à protéger INPI)

Contrairement à Uber/Heetch qui font du **point-à-point** (1 chauffeur prend 1 client de A à B), Métro-Taxi fait du **maillage intelligent** :
- Un abonné monte dans un véhicule allant **dans sa direction**
- Le véhicule peut transporter **jusqu'à 4 abonnés simultanément** (vans = 7 abonnés)
- Si l'itinéraire diverge, l'abonné **change de véhicule à un point de transbordement** (max 2 transbordements par trajet)
- L'algorithme adapte la **longueur des segments** selon la zone :
  - Paris intra-muros : 3-4 km par segment
  - Petite couronne (92/93/94) : 5-7 km
  - Grande couronne (77/78/91/95) : 8-12 km
  - Profil Nuit (22h-05h) : 10-15 km

### 🔥 Pourquoi c'est juridiquement original (et donc protégeable) :
- Ce n'est **PAS du VTC classique** (pas de relation 1-1 chauffeur/passager)
- Ce n'est **PAS du taxi** (pas de tarif compteur, pas de stationnement)
- Ce n'est **PAS exactement du covoiturage BlaBlaCar** (pas de chauffeur particulier — uniquement des VTC pros)
- C'est un **modèle hybride covoiturage VTC à maillage adaptatif** — sans précédent juridique direct en France

---

## 4️⃣ QUESTIONS JURIDIQUES PRIORITAIRES

### 🔴 P0 — Questions à résoudre AVANT le lancement commercial des abonnements

#### Q1. Qualification juridique du chauffeur Métro-Taxi
Le chauffeur est-il :
- Un **travailleur indépendant** (modèle Citygo — notre préférence)
- Un **salarié déguisé** (risque Uber-like)
- Un **transporteur public de personnes** (chauffeur VTC en activité — ce qu'il est déjà)
**→ Quelle qualification est la plus solide en 2026 selon la jurisprudence actuelle ?**

#### Q2. Modèle de rémunération €/km
Le passage de notre rémunération forfaitaire (1,50€/km) à un **système à paliers selon le remplissage** (1,50€ à 1 abonné → 2,10€ à 5+ abonnés) est-il :
- Conforme à la loi Grandguillaume / Code des transports ?
- Compatible avec le statut VTC du chauffeur ?
- Susceptible de requalification en salariat ?
**→ Nous pencher pour le modèle simple (1,50€ uniforme) ou multi-paliers ?**

#### Q3. Le terme "Transbordement"
- Mot évocateur du langage ferroviaire/maritime
- Risque-t-il de heurter la **loi LOTI** ou la réglementation des transports publics ?
- Nous l'utilisons en interne mais en public nous parlons de "covoiturage à maillage intelligent" — est-ce suffisant ?
**→ Quel terme employer en public, dans les CGV, et dans le dépôt INPI ?**

#### Q4. Membre Fondateur — engagement à vie
Nous avons promis aux 9 premiers usagers un **tarif 53,99€/mois "verrouillé à vie"**.
- Est-ce juridiquement opposable ?
- Que se passe-t-il si nous devons augmenter les prix dans 5 ans (inflation, expansion) ?
- Comment formuler cette clause dans les futures CGV pour la rendre :
  - Crédible auprès des fondateurs
  - Sans créer un piège juridique pour Métro-Taxi
**→ Rédiger une clause "Membre Fondateur" sécurisée**

#### Q5. RGPD & données chauffeurs
- Nous collectons : nom, email, téléphone, plaque, licence VTC, IBAN, BIC, géolocalisation temps réel
- Nous envoyons des alertes email automatiques au fondateur à chaque inscription
- Nous trackons la **source d'inscription** (CDG, gare, Facebook, etc.) via URL `?src=`
**→ Notre process RGPD est-il conforme ? Avons-nous besoin d'un DPO externe ?**

---

### 🟠 P1 — À traiter dans les 2-3 mois

#### Q6. Algorithme — Brevet vs Droit d'auteur vs Secret industriel
- En France (art. L611-10 CPI), les **algorithmes purs ne sont PAS brevetables**
- Mais une **innovation technique** (notre algorithme adaptatif par zone + transbordement) l'est-elle ?
- Stratégie recommandée par notre veille : **Brevet (innovation technique) + Droit d'auteur (code) + Marque INPI (nom "Métro-Taxi")**
**→ Quelle stratégie privilégier ? Combien ça coûte (estimation honoraires) ? Quelle est la priorité ?**

#### Q7. Dépôt INPI — Marque "Métro-Taxi"
- Le nom contient "Taxi" — risque-t-il d'être refusé par l'INPI (descriptif/déceptif) ?
- Faut-il ajouter un signe distinctif (logo, slogan associé) au dépôt ?
**→ Conseil INPI : déposer maintenant ou attendre validation du modèle juridique ?**

#### Q8. CGV / CGU / Mentions légales
- Nous n'avons pas encore de CGV professionnelles rédigées par un avocat
- Forfait estimé : ~1500-3000€ ?
**→ Devis pour rédaction complète CGV + CGU + Mentions Légales + Politique de Confidentialité conformes RGPD**

#### Q9. Système "Relais Dormant" (V1.5 — juillet 2026)
- Idée : réveiller des chauffeurs inactifs proches d'un point de transbordement en cas de pénurie
- Implique géolocalisation persistante avec consentement explicite
- Activation par notification push avec son distinctif ("bip Métro-Taxi")
**→ Conformité RGPD + droit du travail des chauffeurs indépendants ?**

---

### 🟡 P2 — Pour mémoire (V2.0 fin 2026 / 2027)

- Partenariats B2B "Patrons VTC" (5+ véhicules sur la plateforme)
- Partenariats boîtes de nuit / bars (commission 0,50€/réservation pour le bar)
- Partenariat RATP/SNCF (service mobilité d'urgence en cas de panne RER/Transilien)
- Expansion Afrique de l'Ouest (Cotonou, Abidjan, Dakar) — adaptation locale du modèle

---

## 5️⃣ NOS PROTECTIONS DÉJÀ EN PLACE (côté technique)

Pour info juridique, voici ce qui est déjà gravé dans notre cahier des charges interne :

| # | Règle d'or | Pourquoi |
|---|------------|----------|
| 1 | Vocabulaire : **"1,50€/km avec au moins un abonné Métro-Taxi à bord"** (jamais "client", jamais "course") | Préserver le statut covoiturage |
| 2 | **Pas de promesse de revenu mensuel** chauffeur | Anti-requalification salariat |
| 3 | **Pas de mode direct V1** — full mutualisation obligatoire | Préserver le modèle covoiturage |
| 4 | **Pas de vente d'abonnements** avant 150 chauffeurs | Éviter de vendre du vent (réputation + protection conso) |
| 5 | **"Transbordement"** = mot interdit en public tant que INPI pas validé | Anti-litige RATP/SNCF |
| 6 | **"Supplément" ≠ "Bonus"** : un supplément est un tarif différent dans un cas spécifique, pas un additif | Cohérence contractuelle |

---

## 6️⃣ ÉTAT D'AVANCEMENT (mai 2026)

- ✅ Plateforme web + PWA en production : https://metro-taxi.com
- ✅ Infrastructure : VPS Hostinger, MongoDB, FastAPI, React
- ✅ 9 chauffeurs VTC pionniers inscrits (Paris + 92/93/94)
- ✅ 9 usagers en liste d'attente (les "Membres Fondateurs" à vie 53,99€/mois)
- 🟠 1000 flyers Vistaprint commandés (campagne CDG/gares Paris)
- 🟠 Inscription en cours au RDV Société Générale (compte pro)
- 🔴 Pas encore d'abonnements vendus (volontaire — attente 150 chauffeurs)

---

## 7️⃣ NOS ATTENTES VIS-À-VIS DE PARALLEL AVOCATS

1. 🎯 **Validation du modèle juridique global** (similaire à Citygo) — go / no go
2. 📝 **Rédaction des CGV, CGU, Mentions Légales, Politique RGPD**
3. 🛡️ **Stratégie de protection PI** (Brevet + Droit d'auteur + Marque INPI)
4. ⚖️ **Recommandation sur le modèle de rémunération chauffeur** (uniforme vs paliers de remplissage)
5. 🤝 **Accompagnement long terme** sur les évolutions du modèle (V1.5, V2.0)
6. 💰 **Devis transparent** pour les 5 points ci-dessus

---

## 8️⃣ DOCUMENTS DÉJÀ DISPONIBLES POUR VOTRE ANALYSE

Sur demande, nous pouvons vous fournir :
- L'architecture technique complète (algorithme adaptatif + modèles de données)
- Notre roadmap stratégique 2026-2027
- Les contrats actuels chauffeurs (à valider/améliorer)
- Les conditions actuelles affichées aux usagers (à transformer en CGV)
- Le code source en lecture seule pour vérifier la conformité technique RGPD

---

## 9️⃣ CONTACT

**Judée Mané** — Fondateur Métro-Taxi
📧 judeemane@hotmail.com
📧 contact@metro-taxi.com
📱 [Numéro pro Bouygues — en attente d'activation]
🌐 https://metro-taxi.com

**Disponibilité** : préférence pour des RDV en soirée (18h-20h) ou en visio.

---

*Préparé par Charly (assistant technique de Judée) le 13 mai 2026. Document strictement confidentiel — réservé au cabinet Parallel Avocats.*

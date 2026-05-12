# 🚖 ROADMAP MÉTRO-TAXI — Plan de route stratégique

**Dernière mise à jour** : 12 mai 2026
**Status global** : 9 chauffeurs pionniers inscrits, 9 usagers en attente, 0 abonnement vendu
**Stratégie** : Pas de vente d'abonnements avant 150 chauffeurs zone pilote (Paris + 92/93/94)

---

## 🎯 PHASE EN COURS — Recrutement chauffeurs (Mai-Septembre 2026)

### Sprint Lundi 11 mai 2026 (P0 critique) ✅ TERMINÉ
- [x] 🔔 Alerte EMAIL fondateur à chaque inscription chauffeur (Resend)
- [x] 📩 Email auto "Bienvenue Pionnier #X" avec stratégie Johny expliquée + numéro de pionnier
- [x] 📊 Champ "source d'inscription" via URL `?src=` invisible

### Sprint Mardi 12 mai 2026 (P0) ✅ TERMINÉ
- [x] 🧠 **Algorithme transbordement adaptatif** — segments dynamiques :
   - Paris intra-muros : 3-4 km ✅
   - Banlieue (92/93/94) : 5-7 km ✅
   - Grande couronne : 8-12 km ✅
   - Nuit (22h-5h) : 10-15 km ✅
   - Capacité 4 abonnés max ✅
   - Détection hybride code postal + GPS fallback ✅
   - Panneau admin API (`GET/PUT/POST /api/admin/algorithm-config`) ✅
- [x] 🚦 Plafond invisible **abonnement 24h** = 5 trajets max ✅
- [x] 🧪 Tests pytest (27/27 passent) ✅

### Sprint Mardi soir 12 mai 2026 (Lot 1 P1) ✅ TERMINÉ
- [x] 🖥️ **UI admin `/admin` → onglet "Algorithme"** — formulaire complet par zone, sauvegarde et reset, badge "modifié" sur les champs édités
- [x] 👤 **Fiche détaillée chauffeur** (`Eye` icon sur chaque ligne du tab Chauffeurs) — symétrie avec usagers : identité, vehicle, IBAN/BIC, revenus mois en cours, virements pending, trajets récents, validation/désactivation depuis la fiche
- [x] 📄 **Script DB nettoyage pionniers** livré dans `/app/memory/DB_CLEANUP_PIONEERS.md` (commandes mongosh prêtes-à-coller, avec backup + réassignation chronologique 1→N + restauration en cas d'erreur)

### Sprint Mercredi-Vendredi 13-15 mai 2026 (Lot 2 P1)
- [ ] 📋 Liste d'attente VIP usagers — page dédiée + email "Membre Fondateur" tarif 53,99€ verrouillé à vie
- [ ] 🔔 **Bippage d'alerte chauffeur** (clic abonné → notification distinctive) — coordonner avec Mode Relais V1.5
- [ ] 🏢 Page "Patron VTC" — formulaire dédié partenariat flotte
- [ ] ⚖️ **Consultation avocat** (voir section JURIDIQUE ci-dessous) (5+ véhicules)

### Sprint moyen terme (Mai-Juin 2026, P1)
- [ ] 📱 Intégration **Twilio WhatsApp Business** (alertes inscriptions vers numéro Bouygues Pro Judée une fois SIM activée)
- [ ] 🔄 Migration paiement Stripe → **Crédit Agricole e-Transactions** (HMAC SHA256) — bloqué attente identifiants bancaires Judée
- [ ] 🌐 Traduction instantanée chat usager↔chauffeur via OpenAI LLM (WebSockets)

---

## ⚖️ JURIDIQUE — Avocats à consulter avant rencontre INPI

**Recherchés et validés 12 mai 2026 (Charly)**. À contacter dans l'ordre de priorité.

### Priorité 1 — Propriété intellectuelle (algorithme + marque INPI)
| Cabinet | Spécialité | Pourquoi | Site |
|---------|------------|----------|------|
| **INFLUXIO** (Paris/Bruxelles) | PI startups tech/SaaS/IA, brevets, INPI/EUIPO/OMPI | +400 startups accompagnées. Réponse <24h. Audit portefeuille PI + protection code/algorithmes | [influxio-avocat.com](https://www.influxio-avocat.com/avocat-propriete-intellectuelle) |
| **Mochon Avocat** (Paris) | PI tech, droit d'auteur algorithmes/SaaS | Stratégie hybride brevet+droit d'auteur pour algorithmes (notre cas) | [mochon-avocat.com](https://www.mochon-avocat.com/expertises/avocat-propriete-intellectuelle-start-up-tech) |

### Priorité 1 — Droit des plateformes VTC/covoiturage 🔥 (LE PLUS IMPORTANT)
| Cabinet | Spécialité | Pourquoi | Site |
|---------|------------|----------|------|
| **Parallel Avocats** (Paris) | Plateformes covoiturage/VTC | **A GAGNÉ pour Citygo contre Heetch** sur le modèle covoiturage (jugement validé). Référence absolue pour notre cas | [parallel.law/casestudy/modele-juridique-covoiturage](https://parallel.law/casestudy/modele-juridique-covoiturage/) |
| **Goldwin Avocats** (Maître Jonathan Bellaiche, Paris) | Droit des plateformes (Uber/Airbnb), concurrence | Référence en droit émergent des plateformes | [goldwin-avocats.com](https://goldwin-avocats.com/fr/nos-competences-categorie/avocat-droit-des-plateformes-paris/) |

### Priorité 2 — CGV/CGU/RGPD/Mentions légales (startup généraliste)
| Cabinet | Site |
|---------|------|
| **Hashtag Avocats** (51 av. Franklin D. Roosevelt, 75008 Paris) | [hashtagavocats.com](https://hashtagavocats.com) |
| **Swim Legal** (réseau, RDV en 48h, 100% remote possible) | [swim.legal](https://www.swim.legal/avocat/technologie-et-numerique) |

### ⚠️ Note technique sur le brevet INPI
- En France, les algorithmes purs **NE SONT PAS** brevetables (art. L611-10 CPI)
- **MAIS** une innovation technique (optimisation mobilité via IA embarquée dans plateforme) **L'EST**
- Stratégie hybride recommandée : **Brevet** (innovation technique) + **Droit d'auteur** (code source, auto-protégé) + **Marque INPI** (nom "Métro-Taxi", logo)
- Coût indicatif : ~350€/classe pour dépôt INPI, devis avocat à demander
- **Conseil de Charly** : Commence par Parallel Avocats (modèle juridique covoiturage) AVANT INPI. Si modèle validé juridiquement, le dépôt INPI est plus facile à défendre.

---

## 🎯 V1.5 — Mode Nocturne Métro-Taxi (Juillet-Septembre 2026)

**Décision** : Validé sur le principe, à reprendre en discussion **dans 2 mois (juillet 2026)**.

### Concept
Marché en or pour Métro-Taxi : jeunes 20-35 ans, sortie boîte/bar 1h-5h du matin, zones dispersées IDF.

### Mécanismes à coder
- [ ] 🌙 **Pré-réservation soirée** : usager réserve son retour AVANT de sortir (créneau horaire flexible)
- [ ] 🗺️ **Zones de retour prédéfinies** (Nord, Est, Sud, Ouest, Banlieue lointaine) avec regroupement par destination
- [ ] 📍 **Hubs nocturnes** (Bastille, Pigalle, Champs-Élysées, Rex, Châtelet, Bercy, République, Gare du Nord) — points de regroupement à pied
- [ ] 💰 **Prime nocturne chauffeur** : 1,80 €/km entre minuit et 5h (au lieu de 1,50€)
- [ ] 🚨 **Bouton SOS chauffeur** + position GPS direct police
- [ ] 💳 **Caution préautorisée 50€** sur carte au moment de la pré-réservation
- [ ] ⏱️ **Règle 3 min d'attente max** au hub + 5€ no-show préautorisé

### Tarification nocturne
- **Décision validée** : Inclus dans abonnement standard (pas de supplément) pour booster acquisition jeunes
- À réévaluer selon ROI réel après 3-6 mois d'opération

### Risques anticipés
- ⚠️ Comportement éméché → caution + notation chauffeur↔usager
- ⚠️ Sécurité chauffeurs nocturnes → bouton SOS + caméra embarquée recommandée
- ⚠️ No-show passager → 5€ pénalité préautorisée

---

## 🎯 V1.5 — SYSTÈME DE RELAIS DORMANT 🔥 (Juillet-Septembre 2026)

**Concept** (idée Judée 11 mai 2026) : résoudre la pénurie de chauffeurs en banlieue / heures creuses / nuit en **réveillant des chauffeurs Métro-Taxi qui dorment chez eux** à proximité d'un point de transbordement à venir.

### Cas d'usage type
- 2h45, Léa, Sylvie, André et Robert (4 abonnés groupés en nocturne) montent dans Métro-Taxi de Marc à Châtelet → direction Sevran
- 2h58, Marc dépose Léa + Sylvie à Aulnay (point de transbordement)
- ⚠️ Aucun chauffeur actif Métro-Taxi à 5 km pour prendre André + Robert sur le segment suivant
- 🔔 L'algo réveille Karim (1,8 km, mode relais ON) avec un **bip distinctif Métro-Taxi**
- Karim clique "J'ACCEPTE" → sort en 3 min → prend André + Robert et les conduit à Sevran
- Karim touche **1,80 €/km** (1,50€/km standard + supplément Relais Nocturne 0,30€/km)

### Modules techniques à coder
- [ ] 🔔 **Notification "Wake Up Driver"** : push + son distinctif (= "bip Métro-Taxi" évoqué par Johny dans vidéo 3/4)
- [ ] 📍 **Géolocalisation persistante** (avec consentement explicite) — chauffeur en "Mode Relais ON"
- [ ] 🧠 **Algorithme prédictif** : 5-7 min avant transbordement, détecte chauffeurs dormants à 2-3 km
- [ ] ⏱️ **Bouton "J'ACCEPTE" valable 30 secondes** → premier arrivé, premier servi
- [ ] 💎 **Supplément Relais Nocturne** : +0,30 €/km (soit 1,80€/km total) — communiqué comme SUPPLÉMENT (pas bonus) pour éviter confusion chauffeurs
- [ ] 📊 **Toggle "Disponible pour relais"** dans dashboard chauffeur (respect vie privée)
- [ ] 🛏️ **Limite anti-burn-out** : max 2 réveils/nuit par chauffeur
- [ ] 🎵 **Production du "Bip Métro-Taxi"** son distinctif via ElevenLabs (~50€ budget)

### Bénéfices stratégiques
- 🛡️ Garantit la satisfaction abonné (jamais bloqué nuit/banlieue)
- 💰 Revenu opportuniste pour chauffeurs dormants → loyauté + ambassadorat
- 🌐 Couverture réseau étendue sans recruter plus de chauffeurs (densité virtuelle)
- 🎯 Différenciation Uber/Bolt absolue (aucun concurrent ne fait ça)

---

## 🎯 V2.0 — Densification & B2B (Septembre 2026 - 2027)

- [ ] 🤝 **Partenariat B2B "Patrons VTC"** : tarif flotte 1,55€/km pour 5+ véhicules + onboarding accéléré 24-48h
- [ ] 🎉 **Partenariat boîtes/bars** : QR code dans les clubs/bars (Rex, La Bellevilloise, Concrete, Petit Bain, etc.) avec commission 0,50€/réservation pour le bar
- [ ] 🚉 **Partenariat RATP/SNCF** — Service de mobilité d'urgence en cas de panne RER/Transilien (idée Judée 8 mai)
- [ ] 🌍 **Lancement Île-de-France complet** (au-delà de la zone pilote Paris + petite couronne)
- [ ] 📊 **Dashboard cartographique** des zones de couverture chauffeurs (où on manque, où on est dense)

---

## 🎯 V3.0+ — Expansion (2027+)

- [ ] 🎪 **Événements ponctuels** : Solidays, Lollapalooza, fan zones Coupe du Monde, etc.
- [ ] 🌍 **Lancement Afrique de l'Ouest** : Cotonou (Bénin), Abidjan (Côte d'Ivoire), Dakar (Sénégal)
   - Lecoeur Blanc identifié comme premier ambassadeur Bénin (DM mai 2026)
- [ ] 🚖 **Mode "Direct sans transbordement"** premium (V3/V4 future) — abandonné en V1, gardé pour quand densité réseau énorme + IA optimisation très avancée

---

## 🛒 ACHATS & LOGISTIQUE — Mai 2026

- [x] ✅ **Vistaprint commande #1** — 1000 flyers **A6** quadrichromie (commande VP_84JC3JFG, 57,46€, livraison mercredi 13 mai 2026)
   - ⚠️ Ces 1000 flyers utilisent l'**URL standard** `metro-taxi.com/chauffeur` (sans `?src=`) — pas de tracking par QR code
- [ ] 📇 **Cartes de visite** Métro-Taxi (250 ex) — pour conversations terrain post-flyer (en attente numéro pro Bouygues)
- [ ] 🖨️ **Vistaprint commande #2 (future)** — Tracker la source d'inscription via QR codes différenciés :
   - CDG : `metro-taxi.com/chauffeur?src=cdg`
   - Orly : `metro-taxi.com/chauffeur?src=orly`
   - Gare du Nord : `metro-taxi.com/chauffeur?src=garedunord`
   - Gare de Lyon : `metro-taxi.com/chauffeur?src=garedelyon`
   - Etc. (Saint-Lazare, Montparnasse, Est, Austerlitz)
- [ ] 📍 **Tournée terrain** :
   - ✅ CDG T1 (9 mai 2026 — 73 flyers, 6 inscriptions liées)
   - [ ] CDG T2 (samedi 16 mai)
   - [ ] Gare du Nord (samedi 23 mai)
   - [ ] Gare de Lyon (samedi 30 mai)
   - [ ] Orly Sud + Ouest (juin 2026)
   - [ ] Gare St-Lazare, Montparnasse, Est, Austerlitz (juin-juillet)

---

## 📞 RDV PROFESSIONNELS

- [x] ✅ **Société Générale** — RDV ouverture compte pro reprogrammé MARDI 12 MAI 2026 (samedi banque fermée à midi)
- [ ] 📞 **Bouygues Pro** — Rappel SIM Pro lundi 11 mai (commande passée 29/04, retard 12+ jours, demander dédommagement)
- [ ] 📞 **Flow Ferron** (vétéran VTC 9 ans) — Appel téléphonique LUNDI 11 MAI 10h30
- [ ] 📩 **Dexter Oulai** (créateur TikTok @dexteroulai) — DM Facebook envoyé 9 mai, attente réponse pour audio Messenger

---

## 🔒 RÈGLES GRAVÉES (alignement trio Judée + Charly + Johny)

1. ✅ **Vocabulaire** : "1,50 €/km parcouru avec **au moins un abonné Métro-Taxi à bord**" (jamais "client", jamais "course")
2. ✅ **Pas de promesse de revenu mensuel** chauffeur — uniquement la formule contractuelle
3. ✅ **Pas de mode direct V1** — full mutualisation obligatoire (covoiturage adaptatif)
4. ✅ **Pas de vente d'abonnements** avant 150 chauffeurs zone pilote (40-50 actifs simultanés)
5. ✅ **Bonus pionnier 1,55€/km** = TEMPORAIRE (100 premiers chauffeurs zone pilote uniquement)
6. ✅ **"Transbordement"** = mot interdit en public tant que dépôt INPI pas validé. Utiliser "covoiturage à maillage intelligent"
7. ✅ **Numéro perso Judée** pour les 9 premiers chauffeurs WhatsApp — basculer pro à 50-80 chauffeurs
8. ✅ **Tarif fondateur 53,99€/mois** verrouillé à vie pour les 9 premiers usagers (Membres Fondateurs)
9. ✅ **"Supplément" ≠ "Bonus"** : un supplément (relais nocturne, prime banlieue) est un **tarif différent** appliqué dans un cas spécifique, pas un additif au standard. Toujours dire "Supplément Relais Nocturne : 1,80€/km" — JAMAIS "Bonus de 0,30€ en plus du 1,50€"

---

## 📊 KPIs DE TRACKING

| KPI | Aujourd'hui (10 mai 2026) | Milestone 1 | Milestone 2 | Milestone 3 |
|-----|---------------------------|-------------|-------------|-------------|
| Chauffeurs inscrits | 9 | 50 | **150** (lancement zone pilote payante) | 300+ (IDF complet) |
| Chauffeurs actifs simultanés | 3 | 15-20 | 40-50 | 80-100 |
| Usagers inscrits (liste d'attente) | 9 | 50+ | 200+ | 1000+ |
| Abonnements payants | 0 | 0 (beta privée gratuite) | Lancement zone pilote | Plein régime |

---

## 👥 LES 9 CHAUFFEURS PIONNIERS HISTORIQUES

| # | Nom | Date inscription | Source |
|---|-----|------------------|--------|
| 1 | Ali Ousmanou | 5 avril 2026 | (organique) |
| 2 | Mohsen Soudane | 26 avril 2026 | (organique) |
| 3 | Brigitte Auguste 👩 | 27 avril 2026 | (organique) — 1ère chauffeuse |
| 4 | Ibrahima Soumare | 9 mai 2026 | CDG T1 |
| 5 | Mayoux Kalonji | 9 mai 2026 | CDG T1 |
| 6 | Nizar Soumaya | 9 mai 2026 | CDG T1 |
| 7-9 | (3 nouveaux) | 10 mai 2026 | À identifier (probablement CDG aussi, vérifier dashboard) |

---

*Document maintenu par Charly (assistant Emergent), validé par Judée (fondateur), enrichi par Johny (stratège).*

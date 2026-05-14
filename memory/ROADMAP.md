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

### Sprint Mercredi 13 mai 2026 — soir (Charly solo pendant que Judée se repose)
- [x] 📋 **Page Liste d'attente VIP "Membre Fondateur"** TERMINÉE
  - Backend : 4 endpoints `/api/founding-members/{stats,join,me}` + `/api/admin/founding-members`
  - Frontend : page `/membre-fondateur` (hero, barre progression chauffeurs vers 150, 4 privilèges, CTA, status banner si déjà membre)
  - Email automatique "Bienvenue Membre Fondateur #X" via Resend (tarif 53,99€/mois verrouillé à vie)
  - Champs DB : `is_founding_member`, `founding_member_number`, `founding_member_joined_at`, `founding_member_locked_price_cents`
  - Testé end-to-end via curl ✅

### Sprint Vendredi 15 mai 2026 — PRÉVU
- [ ] 🛡️ **DÉPLOIEMENT FIX NGINX** sur VPS (warning Chrome Android "app obsolète") — bloqué ce soir 13 mai par box SFR de dépannage qui filtre le port 1117
- [ ] 🚀 Déploiement page `/membre-fondateur` en production
- [ ] 🔔 Bippage d'alerte chauffeur (à coordonner avec V1.5)
- [ ] 🏢 Page "Patron VTC"
- [ ] 💌 Bouton "Envoyer email perso" depuis fiche chauffeur admin

### Sprint Mardi-Jeudi 13-15 mai 2026 (P1 - prochaine session) (5+ véhicules)

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

## 🧮 EN ATTENTE — Système "Maillage Premium" (€/km variable selon remplissage)

**Soulevé par Judée le 12 mai 2026** : un chauffeur a un van 7 places. Il mériterait potentiellement un €/km supérieur quand il transporte 4-7 abonnés vs un véhicule 4 places.

**🔄 Mise à jour 14 mai 2026** : élargir la capacité aux **monospaces/vans jusqu'à 7 places**.

### 💡 RECOMMANDATION CONSOLIDÉE Johny + Charly (14 mai 2026)

Abandon de l'approche "paliers selon remplissage" (trop complexe juridiquement) au profit d'une approche **simple : tarif par catégorie de véhicule**.

| Catégorie | Capacité max | €/km versé chauffeur |
|-----------|--------------|----------------------|
| 🚘 **Berline** (Classe E, Model 3, Série 5, Audi A6...) | 3 abonnés | **1,50 €/km** (base) |
| 🚐 **Monospace** (Espace, Sharan, Touran, Picasso...) | 5 abonnés | **1,70 €/km** |
| 🚐 **Van** (Vito, Trafic, V-Class, Caravelle...) | 7 abonnés | **1,90 €/km** |

### Pourquoi cette grille ?
- ✅ **Simple et lisible** (3 catégories, 3 tarifs fixes)
- ✅ **Pas de variabilité dynamique** (anti-requalification salariat)
- ✅ **Cohérente avec coûts réels** : van consomme +30-40% qu'une berline, amortissement +25%
- ✅ **Plafond 1,90€/km** soutenable pour la marge Métro-Taxi
- ✅ **Présentation marketing** : *"Optimisation réseau"* et **JAMAIS** *"plus gros véhicule = plus gros salaire"*

### 📋 TODOS techniques (Charly — à coder APRÈS validation Parallel)
- [ ] Ajouter champ `vehicle_category` au profil chauffeur (`berline` / `monospace` / `van`)
- [ ] Migration DB : auto-classifier les 9 chauffeurs existants selon leur `vehicle_type` actuel
- [ ] Remplacer constante `MAX_PASSENGERS_PER_VEHICLE = 4` par lookup dynamique selon `vehicle_category` (3/5/7)
- [ ] Adapter `calculate_multi_transfer_route` pour proposer jusqu'à 7 abonnés sur véhicules adaptés
- [ ] Adapter le calcul `driver_revenue` pour multiplier par `tarif_par_categorie[vehicle_category]`
- [ ] Ajouter dans le panneau admin l'override des tarifs par catégorie
- [ ] Tests pytest pour chaque catégorie
- [ ] UI : sur le formulaire d'inscription chauffeur, demander la catégorie (radio buttons avec exemples)

### ❌ IDÉES À NE PAS IMPLÉMENTER V1 (gelées à V2.0)
- ❌ Bonus dynamique heure de pointe (proposé par Johny) → trop proche surge pricing Uber, risque requalification
- ❌ Bonus zone tendue → idem
- ❌ Paliers selon nombre d'abonnés simultanés (1, 2, 3, 4, 5+) → trop complexe juridiquement et complique le calcul des virements mensuels

### 🚦 Statut : **GELÉ — DÉCISION JUDÉE 12 + 14 MAI 2026**
- ⏸️ Attente validation juridique **Parallel Avocats** (priorité absolue)
- ⏸️ Attente densité **30-50 chauffeurs** (échantillon représentatif)
- 📩 **Message à donner au chauffeur de van en attendant** : *"Tu as raison, ton van mérite un traitement particulier. Pour l'instant 1,50€/km uniforme pour tous, mais notre cabinet d'avocats valide actuellement notre grille différenciée par catégorie de véhicule. Toi avec ton van, tu seras à 1,90€/km. Tu seras récompensé sur la valeur réseau que tu apportes, garanti."*

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
10. ✅ **"Contrat chauffeur" = mot INTERDIT** (risque requalification salariat type Uber/Deliveroo). Utiliser :
    - **"Conditions Générales de Partenariat (CGP)"** (juridique/formel)
    - **"Protocole d'accord"** (commercial/marketing)
    - **"Charte du chauffeur partenaire"** (interne)
    - Les chauffeurs VTC sont des PARTENAIRES INDÉPENDANTS, déjà en activité sous leur propre statut (auto-entrepreneur, SASU, EURL...). Métro-Taxi ne fixe ni leurs horaires, ni leurs zones, ni leur volume d'activité.
11. 🚨 **"Au moins un abonné à bord" = formulation INTERDITE** (faille business + faille juridique). Soulevée par Judée le 14 mai 2026.
    - ❌ NE JAMAIS dire : *"avec au moins un abonné à bord"* — un chauffeur peut interpréter "1 seul abonné A→B" = modèle de faillite
    - ❌ NE JAMAIS dire : *"plus tu remplis, plus tu gagnes"* — risque requalification (incitation à la productivité) + contradiction tarif fixe
    - ✅ TOUJOURS dire : *"1,50€/km AVEC DES ABONNÉS MÉTRO-TAXI à bord"* (sous-entendu pluriel = maillage)
    - ✅ TOUJOURS dire : *"L'algorithme te remplit, tu fais ta route"* (transfert charge mentale sur la plateforme)
    - Le maillage multi-abonnés est garanti par l'ALGORITHME, pas par une consigne au chauffeur (anti-requalification)

12. ✅ **"Bonus pionnier" = TERME RÉSERVÉ aux 100 premiers chauffeurs zone pilote** (1,55€/km temporaire). NE JAMAIS l'utiliser pour le parrainage ni pour le maillage. Risque de confusion sémantique + risque schéma pyramidal.
    - Pour parrainage chauffeur→chauffeur : utiliser **reconnaissance non-monétaire** (badge, mention publique sur page pionniers, "Membre du Conseil des Pionniers", etc.)
    - Si parrainage monétaire un jour : terme **"Prime de Coparrainage Réseau"** distinct, après validation Parallel

13. ✅ **Vocabulaire stratégique consolidé (mai 2026)** :
    - "Réseau de mobilité mutualisée" > "plateforme" / "startup"
    - "Chauffeur partenaire" > "chauffeur" / "conducteur"
    - "Abonné Métro-Taxi" > "client" / "usager" / "passager"
    - "Conditions Générales de Partenariat (CGP)" > "contrat chauffeur"
    - "Modèle covoiturage à maillage intelligent" > "VTC nouvelle génération"
    - "Cercle des Membres Fondateurs" > "liste d'attente VIP"
    - Approche patrons VTC : **"canal complémentaire d'activité, pas exclusif"** (idée Johny 14 mai)
    - Approche syndicats : **"nous réfléchissons à un modèle plus soutenable pour les chauffeurs"** (jamais "rejoignez notre startup")

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

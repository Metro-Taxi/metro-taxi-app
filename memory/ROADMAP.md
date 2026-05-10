# 🚖 ROADMAP MÉTRO-TAXI — Plan de route stratégique

**Dernière mise à jour** : 10 mai 2026
**Status global** : 9 chauffeurs pionniers inscrits, 9 usagers en attente, 0 abonnement vendu
**Stratégie** : Pas de vente d'abonnements avant 150 chauffeurs zone pilote (Paris + 92/93/94)

---

## 🎯 PHASE EN COURS — Recrutement chauffeurs (Mai-Septembre 2026)

### Sprint Lundi 11 mai 2026 (P0 critique)
- [ ] 🔔 Alerte EMAIL fondateur à chaque inscription chauffeur (Resend)
- [ ] 📩 Email auto "Bienvenue Pionnier #X" avec stratégie Johny expliquée + numéro de pionnier
- [ ] 📊 Champ "source d'inscription" sur form chauffeur (CDG / Gare du Nord / Gare de Lyon / Orly / Facebook / TikTok / Bouche-à-oreille / Autre)

### Sprint Mardi-Mercredi 12-13 mai 2026 (P0)
- [ ] 🧠 **Algorithme transbordement adaptatif** — segments dynamiques :
   - Paris intra-muros : 3-4 km
   - Banlieue (92/93/94) : 5-7 km
   - Grande couronne : 8-12 km
   - Nuit (22h-5h) : 10-15 km
   - Capacité 4 abonnés max
   - Fenêtre aéroport 30 min
   - Panneau admin pour ajuster les seuils
- [ ] 🚦 Plafond invisible **abonnement 24h** = 5 trajets max
- [ ] 📋 Liste d'attente VIP usagers — page dédiée + email "Membre Fondateur" tarif 53,99€ verrouillé à vie

### Sprint Jeudi-Vendredi 14-15 mai 2026 (P1)
- [ ] 🗺️ Zones pilote sur dashboard admin (Paris + 92/93/94 vs hors zone)
- [ ] 🎁 Bonus pionnier **temporaire** 1,55€/km zone pilote (pour les 100 premiers chauffeurs zone pilote uniquement) — communiqué clairement comme TEMPORAIRE
- [ ] 🔢 Compteur public chauffeurs sur landing page chauffeur ("X chauffeurs nous ont déjà rejoints")
- [ ] 🏢 Page "Patron VTC" — formulaire dédié partenariat flotte (5+ véhicules)

### Sprint moyen terme (Mai-Juin 2026, P1)
- [ ] 📱 Intégration **Twilio WhatsApp Business** (alertes inscriptions vers numéro Bouygues Pro Judée une fois SIM activée)
- [ ] 🔄 Migration paiement Stripe → **Crédit Agricole e-Transactions** (HMAC SHA256) — bloqué attente identifiants bancaires Judée
- [ ] 🌐 Traduction instantanée chat usager↔chauffeur via OpenAI LLM (WebSockets)

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

- [ ] 🖨️ **Vistaprint** — Commande **500 flyers A5 170g** recto-verso quadrichromie
- [ ] 📇 **Cartes de visite** Métro-Taxi (250 ex) — pour conversations terrain post-flyer
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

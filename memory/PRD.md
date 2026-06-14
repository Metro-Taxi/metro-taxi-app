# PRD — MÉTRO-TAXI

## 🎯 PROBLÈME ORIGINAL
Plateforme **Métro-Taxi** (React/FastAPI/MongoDB) — Covoiturage VTC avec transbordement intelligent.
Zone pilote : Saint-Denis (93) — extension Île-de-France.

## ⚠️ STATUT CRITIQUE (13/06/2026)
**LANCEMENT 13 JUIN REPORTÉ AU 26 JUILLET 2026** suite à bugs techniques le jour J :
- GPS positionnement non opérationnel
- Pas d'endpoint "passager monté" → statut courses bloqué à "accepted"
- Plusieurs chauffeurs ont quitté le groupe WhatsApp

## 🆕 NOUVEAU PLAN — LANCEMENT 26 JUILLET 2026
- Demande autorisation Mairie 18e (Porte de Clignancourt)
- Animation musicale + banderoles + démos live
- 6 semaines pour : stabilisation tech, recrutement chauffeurs, campagne digitale
- Compensation 50€ aux chauffeurs présents le 13/06

## 💰 MODÈLE TARIFAIRE (ACTIF)
### Abonnements usagers
- 24h : 6,99€ • 7 jours : 19,99€ • 30 jours : 53,99€

### Chauffeurs (déployé)
- Berline / Sedan : 1,50€/km
- Monospace / Minivan / SUV : 1,70€/km
- Van / Minibus : 1,90€/km

### Partenaires taxiphones
- Commission 15% du 1er abonnement + bonus volume 50€

## 🐛 BUGS CRITIQUES À FIXER (semaine du 14-20 juin)
1. **P0** ✅ **FIXÉ 14/06** : Cycle de vie de course complet + OTP embarquement à 4 chiffres
   - Backend : `RideProgressUpdate` étend `pickup_otp`, transitions linéaires accepted→pickup→in_progress→completed
   - Backend : `calculate_distance` était MANQUANT à l'import dans `admin.py` (cause majeure crash complete_ride)
   - Backend : OTP généré automatiquement à `/rides/request`, masqué pour le chauffeur
   - Frontend Driver : 3 boutons (J'arrive / Saisie OTP+Démarrer / Terminer)
   - Frontend User : code OTP affiché en grand tant que statut ∈ {accepted, pickup}
   - Patch déployable : `/patches/ride_lifecycle_otp_20260614.tar.gz`
2. **P0** : GPS positionnement non fonctionnel → diagnostiquer côté frontend
3. **P1** : Bouton "Cadeau abonnement" → fonctionne (RESEND_API_KEY importé)
4. **P1** : UX 1ère course offerte trop complexe → automatiser (auto-flag pending_promo dès souscription si <30)
5. **P2** : 30 codes promo en base mais UX redeem trop manuelle pour usagers

## ✅ INFRASTRUCTURE EN PLACE
- Site live : https://metro-taxi.com (Hostinger VPS, pm2)
- Backend FastAPI + MongoDB (`metro_taxi_prod`)
- Google Ads campagne (À METTRE EN PAUSE — économies crédits)
- Balise Google `AW-18231977416` installée
- 30 codes promo Saint-Denis en base
- Sogecommerce paiements (Stripe désactivé via kill-switch 410)

## 📦 ACTIFS MARKETING (livrés, prêts pour réemploi)
- Flyer V3.2 A6 Saint-Denis (avec prix + QR)
- Banderole 25×50cm A3 (Point Inscription)
- Contrat partenariat PDF avec cachet préimprimé
- 3 maquettes cachet officiel (logo + tél + URL)
- Logo Métro-Taxi
- Page Facebook Pro Métro-Taxi (publications épinglées)
- Gmail "Métro-Taxi Saint-Denis" actif

## 👥 ÉTAT DES UTILISATEURS (13/06)
- **Chauffeurs** : 39 inscrits (départs partiels après 13/06)
- **Abonnés actifs** : 4 (Boniface, Djamilatou, Jacinta, Judée)
- **Inscrits non abonnés** : 16
- **Partenaires signés** : 1 (Kelly's Paris — code KLYS, gérant Pierre Jacques Abega)
- **Prospects partenaires** : PHONEEXPERT (banderole posée), SMART TECH (signature 14/06)

## 🛠️ ENDPOINTS TRACKING PARTENAIRES (CODÉS, À DÉPLOYER)
Patch prêt : `https://metro-taxi-demo.preview.emergentagent.com/patches/partner_tracking_20260612.tar.gz`
- `GET /api/admin/partner-stats` — Vue d'ensemble par code
- `GET /api/admin/partner-stats/{code}` — Détail 1 partenaire
- `GET /api/admin/partner-payouts/csv?week=YYYY-WW` — Export CSV paiements

## 🎯 PRIORITÉS S1 (14-20 JUIN) — APRÈS REPOS WEEK-END
1. **P0 fix bugs critiques** (P0 list ci-dessus)
2. **P0 verser compensation 50€** aux chauffeurs présents le 13/06 — REPORTÉ (trésorerie, attendre retour Sarah)
3. **P1 deploy partner tracking** sur prod
4. **P1 dossier mairie 18e** pour autorisation Porte Clignancourt
5. **P2 page publique "Points d'inscription"** (Kelly's Paris, PHONEEXPERT, SMART TECH)

## 🔍 AUDIT À FAIRE APRÈS 26/07 (incohérences DB chauffeurs)
- Plusieurs chauffeurs ont déclaré `vehicle_type=van/monospace` mais `seats=4` à l'inscription :
  - Ali (van/4), Nizar (van/4), Mayoux (van/6), Houssem (monospace/4), JEAN CLAUDE MARCEL (suv/4)
- Le formulaire d'inscription doit contraindre min/max selon le type :
  - berline: 3-4 • suv: 4-6 • monospace: 5-7 • van: 7-9
- Action : recontacter les chauffeurs concernés + ajouter validation côté formulaire
- Impact actuel : tarif (€/km par vehicle_type) OK • capacité matching SOUS-ÉVALUÉE

## 📞 CONTACTS
- Capitaine : Judée SOULEYMANE (Fondateur) — Tél : 06 05 78 64 25
- Email : contact@metro-taxi.com
- Gmail : metrotaxi.saintdenis@gmail.com (Google Ads)

## 🔑 FICHIERS CLÉS
- `/app/backend/utils/helpers.py` — DRIVER_RATE_PER_KM_BY_VEHICLE
- `/app/backend/routes/admin.py` — gift_subscription, partner_stats (déployés)
- `/app/backend/routes/promo_codes.py` — Génération codes promo
- `/app/frontend/src/pages/DriverEarnings.js` — UI revenus + IBAN
- `/app/frontend/public/marketing/` — Tous les assets marketing
- `/app/frontend/public/patches/` — Archives tar.gz déploiement VPS

## 💡 LEÇONS DU 13/06 (capitales)
1. **TESTER en conditions réelles AVANT communication publique**
2. **Endpoint /start-trip est NÉCESSAIRE** pour cycle vie course
3. **UX simple > système élégant** (codes promo manuels = mauvaise UX)
4. **Compensation immédiate quand on commet une erreur** = respect chauffeurs
5. **Lancement local = autorisation mairie OBLIGATOIRE** (Porte Clignancourt 18e)

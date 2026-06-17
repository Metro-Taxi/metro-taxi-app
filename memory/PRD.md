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

### Paiement des chauffeurs — RÈGLE NON NÉGOCIABLE
- **JAMAIS en cash** — uniquement par virement SEPA sur IBAN renseigné dans l'app
- **Cadence : TOUS LES LUNDIS** (paye automatique de la semaine ISO précédente)
- Codé dans `server.py` : `PAYOUT_WEEKDAY = 0`, déduplication par `YYYY-Www`
- Email automatique au chauffeur après chaque virement (Resend `send_payout_notification_email`)

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
2. **P0** ✅ **FIXÉ 14/06** : Payout chauffeurs migré du 10 du mois → tous les lundis
   - `PAYOUT_WEEKDAY = 0` dans `server.py`, déduplication par semaine ISO
3. **P0** ✅ **FIXÉ 15/06** : GPS fantôme (chauffeur affiché à ancienne position)
   - Backend : filtre `location_updated_at >= now - 10min` dans `/drivers/available` et `/matching/find-drivers`
   - Backend : tâche background `cleanup_stale_drivers` toutes les minutes (auto-OFFLINE après 10 min sans GPS)
   - Frontend Driver : heartbeat 30s + push GPS au retour foreground (`visibilitychange`)
4. **P0** ✅ **FIXÉ 15/06** : Bip sonore "nouvelle course" pour le chauffeur (jamais implémenté avant)
   - Web Audio API → bip-bip 660/880Hz + vibration `navigator.vibrate`
5. **P1** : Bouton "Cadeau abonnement" → fonctionne (RESEND_API_KEY importé)
6. **P1** : UX 1ère course offerte trop complexe → automatiser (auto-flag pending_promo dès souscription si <30)
7. **P2** : 30 codes promo en base mais UX redeem trop manuelle pour usagers

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

## 🔒 SÉCURITÉ HTTPS — CERTIFICAT SSL (corrigé 17/06/2026)
- **Status** : ✅ Certificat Let's Encrypt valide jusqu'à **mi-septembre 2026** (renouvelé le 17/06)
- **Couverture** : `metro-taxi.com` + `www.metro-taxi.com`
- **Renouvellement automatique** : `snap.certbot.renew.timer` actif (2x/jour)
- **Chaîne SSL** : 2 certificats (R13 + ISRG Root X1) ✅
- **Historique bug** :
  - Ancien `certbot apt 1.21.0` cassé (incompatibilité pyOpenSSL)
  - Aucun renouvellement auto configuré → risque expiration 01/07/2026 (avant relance 26/07)
  - Fix : `snap install certbot 5.6.0` + activation timer auto

## 🎯 PRIORITÉS S2 (15-21 JUIN)
1. **P0 PREMIÈRE COURSE COMMERCIALE RÉUSSIE** — ✅ 17/06 (Maaz Tagari, 4.67 km, 7,94€)
2. **P0 CERTIFICAT SSL RENOUVELÉ + AUTO-RENEW** — ✅ 17/06
3. **P0 Remboursement Mme Vadé** — ⏳ Dylan Fernandes (06 19 70 57 99)
4. **P1 Patch v8 à venir** : auto-fit carte chauffeur + bip iOS + flash visuel
5. **P1 Fix historique trajets vide côté admin** — bug identifié 17/06
6. **P1 Ajouter "Total trajets" sur dashboard chauffeur**
7. **P1 Partenaires Paris** : Golden GSM ✅ + 2 en attente sur Bvd Ornano
8. **P1 Dossier mairie 18e (Clignancourt)** + Plaine Commune (Basilique)
9. **P1 Démarche églises** (Notre-Dame de Clignancourt en priorité)
10. **P2 Dashboard partenaires commerce de proximité** (Golden GSM, Kelly's Paris, etc.) — formulaire dédié à créer
11. **P2 PWA iPhone install** : guide ajouter à l'écran d'accueil via Safari

## 🐛 BUGS RÉSIDUELS POST-TEST LIVE 17/06
- Bip sonore non perçu chez Maaz — diagnostic iOS/Android + vibration en cours
- Zoom carte chauffeur snap-back — ✅ FIXÉ patch v7 (17/06)
- Historique trajets vide côté admin dashboard (alors que rides existent en DB) — à investiguer
- Compte doublon Pierre Jacques — ⏳ EN ATTENTE confirmation utilisateur

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

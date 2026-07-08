# PRD — Métro-Taxi (Saint-Denis pilote)

## Problème
Plateforme VTC + covoiturage avec abonnements hebdomadaires (Sogecommerce) et **système d'affiliation partenaires commerciaux (15% commission)**. Zone pilote Saint-Denis (lancement 26 juillet 2026).

## Stack
- Frontend : React (PWA) — port 3000
- Backend : FastAPI — port 8001
- DB : MongoDB
- Paiements : Sogecommerce (webhooks)
- Génération assets marketing : **PIL/Pillow local UNIQUEMENT** (zéro LLM)

## Identifiants test
`judeemane@hotmail.com` / `MetroTaxi2026` (Admin)

---

## Implémenté (à jour)

### Cœur app
- Cycle de course complet (OTP, départ, transbordement)
- Abonnements hebdo + renouvellements via Sogecommerce
- iOS Wake Lock (oscillateur audio + overlay rouge) — mode silencieux contourné
- Mot de passe oublié + changement de mdp
- Anti-brute force assoupli à 8 tentatives

### Affiliation partenaires
- Backend `/api/partners/apply` + validation admin
- Code 4 lettres (ex: GGSM) lié au champ `referral_code` sur `users`
- Webhook Sogecommerce reverse 15% au partenaire à chaque paiement (initial + renouvellements)
- Payout automatique tous les LUNDIS
- Contrat partenariat PDF (SIRET 918 687 864 RCS Bobigny)

### Assets marketing CLIENT (19/06/2026)
- **Banderole 25×50cm CLIENT V4** (1476×2952) — PNG + PDF
  - Slogan « 1ÈRE COURSE GRATUITE » en bandeau jaune central (~30% hauteur)
  - 3 plans (24h/7j/30j), QR `metro-taxi.com`, SIRET 918 687 864 RCS Bobigny
- **Flyer A6 CLIENT V4** (1240×1748, 300 DPI) — PNG + PDF
  - Basé sur V3_2 existant, mention « SAMEDI 13 JUIN 2026 » masquée proprement (patch background)
- Fix root cause : police DejaVu installée via `apt install fonts-dejavu` (avant : fallback silencieux load_default ⇒ texte 10px illisible)

### ⚠️ RÈGLE D'OR
- Le **15% de commission partenaire** est **CONFIDENTIEL** — uniquement dans le contrat PDF, **JAMAIS** sur un support marketing public (flyer, banderole, site).
- Tous les flyers/banderoles sont destinés aux **CLIENTS** (passagers), pas aux partenaires. Les supports sont affichés DANS les commerces partenaires mais visent à recruter des passagers.


### Push PWA critiques chauffeur (26/02/2026)
- `sw.js` v20 : pour les types `ride_request` et `wake_drivers` (et tout payload `data.critical=true`)
  - Vibration agressive `[400, 150, 400, 150, 400, 150, 600]` (~2,5s en poche)
  - `requireInteraction: true` → la notif reste à l'écran tant que le chauffeur n'a pas tapé dessus
  - `tag` unique par notif critique pour forcer re-vibration sur chaque nouvelle course
- Limite Android assumée : pas de son custom forçable en background depuis une PWA, mitigation via vibration + persistance visuelle
- VersionBadge → `v27.push-critical-vibrate-2026.02.26`

---

### Rattrapage manuel revenus chauffeur (26/02/2026)
- Endpoint `POST /api/admin/driver-earnings/manual-adjust` (driver_id, month YYYY-MM, amount_eur, reason)
  - Upsert dans `driver_earnings`, refuse si mois déjà `paid`, refuse si total devient négatif
  - Audit log obligatoire dans `admin_audit_log` (admin_id, driver_id, mois, montant, raison, timestamp)
- UI : bouton "Rattrapage manuel" dans chaque carte profil de `DriverEarningsDiagnosticDialog`
- Cas d'usage : course exécutée IRL absente de la BDD (ex: reset post-import legacy)
- VersionBadge → `v28.manual-earnings-adjust-2026.02.26` / SW v21


## Backlog priorisé

### P0 — Validation Capitaine
- [ ] User verification du nouveau flyer A6 & banderole V11

### P1
- [ ] Auto-expiration des `ride_requests` pending > 5 min (cron ou modif GET)
- [ ] Gratuité 1ère course (≤10km) pour les 100 premiers abonnés
- [ ] Supprimer compte doublon `heleymouke@gmail.com`

### P0 ajouté — Import legacy VPS (23-24/02/2026)
- Endpoint `/api/admin/import/legacy-vps` + UI MaintenanceTab.jsx
- Parser front-end ultra-tolérant : JSON array, JSONL (mongoexport par défaut), arrays collés `][`, objet unique
- Nettoyage automatique des extensions BSON (`$oid`, `$date`, `$numberLong`, `$numberDouble`) côté front ET back
- Upload de fichier `.json` directement (en plus du copier-coller)
- **✅ Import effectué le 23/06/2026 (29 usagers + 39 chauffeurs en base)**. Fichiers JSON supprimés post-import pour RGPD.

### P1/P2/P3 — Session 24/02/2026
- ✅ Langue par défaut forcée à FR (ignore navigator) + fallback FR (`i18n/index.js`)
- ✅ Reverse-geocode Nominatim côté serveur avec cache 24h + rate-limit 1 req/s (`utils/geocoding.py`)
- ✅ Bouton "Activer notifications" PWA iOS 16.4+ ajouté dans User & Driver Dashboard (`EnableNotificationsButton.jsx`) avec détection iOS standalone

### P3 (non démarré)
- [ ] Refactor `DriverDashboard.js` (>1000 lignes) — risqué sur app prod, skip pour l'instant

### P2 (reste à venir)
- [ ] Reverse-geocode pickup serveur (Nominatim) — adresse parfois tronquée
- [ ] Traduire boutons chauffeur en FR (Accept/Decline → Accepter/Refuser)

### P3
- [ ] Push Notifications PWA iOS 16.4+ (alerte système native)
- [ ] Refactor `DriverDashboard.js` (>1000 lignes)
- [ ] Investiguer install PWA impossible sur certains iPhones (manifest/SSL chain)

---

## Règles agent (à respecter strictement)
1. **Zéro appel LLM payant** sans autorisation explicite du Capitaine (génération image/texte)
2. Tutoiement obligatoire, persona "Charly"
3. Tous les assets marketing : PIL local UNIQUEMENT
4. Police : DejaVu (installer `fonts-dejavu` si absent), pas de fallback silencieux

---

## Session 05/07/2026 — Fixes DNS + Comms

### Réalisé
- **PDF CIS v2** généré (date auto, page cachet supprimée) — user a finalisé côté sien
- **Cachet officiel PDF** (`/app/frontend/public/downloads/cachet-metro-taxi.pdf`) — converti depuis PNG LOGO_CENTRE
- **Endpoints download bypass PWA** : `/api/marketing/cis` + `/api/marketing/cachet` (force `attachment`)
- **DNS Resend metro-taxi.com** via Kodee (Hostinger) :
  - SPF, DKIM, MX déjà OK
  - DMARC ajouté : `v=DMARC1; p=none; rua=mailto:contact@metro-taxi.com; adkim=r; aspf=r`
  - TTL baissé à 3600s
- **Test mail-tester.com** = **10/10** ✅
- **Mail rectification envoyé aux 39 chauffeurs sourds** via bouton admin → Resend delivered
- **Copie test** au user perso Gmail → Delivered dans onglet **Promotions** (pas Spam) ✅

### État actuel
- Chauffeurs validés : 44
- Avec push actif : 5 (dont user)
- SANS push (sourds) : 39 — mail rectification envoyé, en attente d'action utilisateur
- Doublon détecté : Edgar DOUZIMA `eddouz@hotmail.fr` / LUDOVIC EDGAR DOUZIMA `12imaedgar@gmail.com` (à fusionner plus tard)

### Décision en attente
- **Twilio SMS** : mis en pause pour raisons budgétaires. User réfléchit entre :
  - A) Offre promo 100 inscrits gratuits (P1, 0€ opérationnel)
  - B) Twilio en mode minimal (~15-25€/mois)
  - C) Campagne WhatsApp vidéo manuelle aux 10 sourds prioritaires (0€)

### Prochaines actions
- Attendre retour user (demain)
- Attendre retour chauffeurs sur mail rectification (24-48h)
- Nouveau diagnostic push pour mesurer taux de conversion

---

## Session 07/07/2026 — Intégration Twilio SMS + Dossier ADIE

### Livré
- **Backend Twilio SMS** complet (`services/twilio_sms.py`), intégré dans `/api/rides/request` broadcast, mode DRY-RUN par défaut, kill-switch persisté dans `.env`
- **3 endpoints admin** : `/admin/twilio/{status,toggle,send-test}`
- **UI carte "📱 SMS Twilio"** dans onglet 🧹 Maintenance avec toggle + test unitaire
- **Version** : `v43.twilio-sms-broadcast-2026.07.06`

### Twilio — statuts
- ✅ Compte Twilio créé (SID `AC1089ccf3ff...`)
- ✅ Regulatory Bundle FR approuvé le 07/07 (SID `BU6a6c54ff...`)
- ⏳ Customer Profile en vérification (48h annoncées) — bloque l'upgrade compte payant
- ❌ Aucun numéro FR encore acheté définitivement (compte encore trial, achat annulé silencieusement)
- ⏳ À faire post-vérification : upgrade → rachat numéro → assigner Bundle → communiquer nouveau numéro au backend

### Documents ADIE prêts
- Livre Blanc Métro-Taxi v0.1 par Johny → sauvegardé `/app/memory/LIVRE_BLANC_METRO_TAXI_v0.1.md`
- Note stratégique / hypothèses éco par Johny → base de travail expert-comptable
- Mail-type de demande ADIE rédigé (à envoyer via https://www.adie.org/prendre-rendez-vous)
- Liste 8 organismes 93 sauvegardée `/app/memory/ACCOMPAGNEMENT_ENTREPRENEURS_93.md`

### Décisions stratégiques
- ❌ Abandon expert-comptable payant (devis 3 000 € trop élevé)
- ✅ Bascule sur écosystème étatique : ADIE + BGE + Bpifrance Création
- Cible : microcrédit 2 000 € ADIE en secours si SG refuse

### Chiffres actuels app (07/07 fin de journée)
- 45 chauffeurs pionniers (dernier : Abderrahmane Bahri via Flyer CDG)
- 32 usagers pré-inscrits
- 0 abonnement payant vendu

### Next Actions (par ordre)
1. User : contacter ADIE via formulaire online → attendre rappel 48h
2. Twilio : attendre validation Customer Profile (48h) → upgrade + rachat numéro
3. Backend : mise à jour `TWILIO_PHONE_NUMBER` dès communication nouveau numéro
4. Test SMS en réel (5 SMS ≈ 0,38 €)
5. Fusion doublon Douzima (P2, ~2 crédits)
6. Compteur coûts SMS admin (P2, ~4 crédits, après premiers vrais envois)

---

## Session 08/07/2026 — Broadcast Twilio grandeur nature ✅

### Livré
- Endpoint `/admin/twilio/send-test-broadcast-all` (texte fixe "TEST TECHNIQUE")
- Bouton orange dans carte Maintenance SMS Twilio
- Version bumped `v44.twilio-broadcast-test-2026.07.08`
- Twilio Customer Profile validé (~9h52)
- Compte upgradé (rechargement 20 $, crédit trial 15,50 $ perdu)
- Numéro US bonus `+15076206407` utilisé (rewriter opérateur FR → short code `38102`)
- Broadcast test réel aux 44 chauffeurs validés (1 chauffeur skip - phone invalide)

### Résultats broadcast
- 44/44 envoyés
- 39 Delivered en <60 sec (88,6%)
- 4 Sent en cours (Devenir Delivered sous 10 min)
- 1 Undelivered (Iliad, error 30005 - Unknown destination handset - numéro fantôme à identifier)
- Coût : 3,30 $
- Solde restant : ~16,55 $

### Next actions (à reprendre le 09/07)
1. Repasser Twilio en DRY-RUN pour sécuriser jusqu'au lancement (bouton "Désactiver" dans Maintenance)
2. Identifier le chauffeur fantôme (30005) et le supprimer de la base
3. Attendre retours chauffeurs sur SOS 0605786425
4. Contacter ADIE 93 pour dossier microcrédit 5 000 €
5. Envoyer les 3 docs à Sarah SG (si prévisionnel finalisé avec l'ADIE)

### Backlog
- Fusion doublon Edgar/Ludovic Douzima (P2)
- Compteur coûts SMS live dans admin (P2)
- Optimisation géographique GPS avant scale (dès 5 courses/jour)

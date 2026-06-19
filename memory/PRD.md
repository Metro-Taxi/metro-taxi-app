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

### Assets marketing (19/06/2026)
- **Banderole 25×50cm PARTENAIRES V11** (1476×2952, slogan 55% hauteur) — PNG + PDF
- **Flyer A6 PARTENAIRES recto/verso** (1240×1748, 300 DPI) — PNG + PDF VistaPrint
  - Stade de France + silhouette Tour Eiffel + slogan « DEVIENS PARTENAIRE · GAGNE 15% À CHAQUE ABONNEMENT »
  - QR `metro-taxi.com/partners/apply?ref=FLYER`
- Fix root cause : police DejaVu installée (avant fallback silencieux load_default ⇒ texte 10px illisible)

---

## Backlog priorisé

### P0 — Validation Capitaine
- [ ] User verification du nouveau flyer A6 & banderole V11

### P1
- [ ] Auto-expiration des `ride_requests` pending > 5 min (cron ou modif GET)
- [ ] Gratuité 1ère course (≤10km) pour les 100 premiers abonnés
- [ ] Supprimer compte doublon `heleymouke@gmail.com`

### P2
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

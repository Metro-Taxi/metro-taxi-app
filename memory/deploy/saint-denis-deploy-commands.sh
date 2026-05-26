# 📋 Commandes VPS — Lancement Saint-Denis (13 juin 2026)
# Capitaine, copie-colle ces blocs dans l'ordre. À toi de jouer.

# ═══════════════════════════════════════════════════════════════
# BLOC 1 — DÉPLOIEMENT DES NOUVELLES FONCTIONNALITÉS (5 min)
# ═══════════════════════════════════════════════════════════════
# Pousse depuis Emergent via "Save to GitHub" AVANT d'exécuter ça.
# Puis sur ton VPS Hostinger :

cd /var/www/metro-taxi-app && \
git pull origin main && \
cd backend && \
source venv/bin/activate && \
pip install qrcode pillow && \
deactivate && \
cd ../frontend && \
rm -rf build && \
yarn build && \
pm2 restart all --update-env && \
sudo systemctl reload nginx && \
echo "✅ Déploiement OK"


# ═══════════════════════════════════════════════════════════════
# BLOC 2 — PRÉ-GÉNÉRATION DES 8 MP3 D'ALERTES TRANSBORDEMENT
# (1 seul appel, le cache fait le reste)
# ═══════════════════════════════════════════════════════════════
# Étape A : obtiens un token admin via login + OTP (à faire dans le navigateur sur https://metro-taxi.com/login)
# Étape B : récupère le token dans les DevTools (localStorage.token) et exporte-le :

export ADMIN_JWT="COLLE-ICI-TON-TOKEN-ADMIN"

# Étape C : déclenche la pré-génération (cache filesystem, idempotent)
curl -X POST https://metro-taxi.com/api/admin/tts/pregenerate-transfer-alerts \
  -H "Authorization: Bearer $ADMIN_JWT"

# Vérification :
curl https://metro-taxi.com/api/tts/transfer-alerts/info | python3 -m json.tool


# ═══════════════════════════════════════════════════════════════
# BLOC 3 — GÉNÉRATION DES 30 CODES SAINT-DENIS (interface admin)
# ═══════════════════════════════════════════════════════════════
# Va sur : https://metro-taxi.com/admin/promo-codes
#
# Champs par défaut (modifie si besoin) :
#   - Campagne       : saint-denis-2026-06-13
#   - Prefix code    : STDENIS
#   - Quantité       : 30
#   - Distance max   : 10
#   - Région         : saint-denis
#   - Expire le      : 2026-06-30T23:59:59Z
#
# Clique "Générer les codes". Tu auras tes 30 codes uniques.
#
# Ensuite :
#   - "Copier" → copie tous les codes (un par ligne) pour WhatsApp
#   - "CSV" → télécharge le CSV
#   - "ZIP QR" → télécharge les 30 PNG QR codes prêts à imprimer sur les flyers
#   - Petit bouton QR sur chaque ligne → 1 QR à la fois
#
# Chaque QR pointe vers : https://metro-taxi.com/saint-denis?promo={CODE}&src=flyer
# → Scan = landing prérempli = inscription en 1 clic.


# ═══════════════════════════════════════════════════════════════
# BLOC 4 — PATCH NGINX RATE-LIMITING (sécurité anti-flood)
# ═══════════════════════════════════════════════════════════════
# Fichier de référence : /app/memory/deploy/nginx-security-patch-2026-05-20-v3.conf
# (à recopier dans le repo Emergent OU à coller manuellement sur le VPS)

sudo nano /etc/nginx/sites-available/Metro-Taxi
# (colle les blocs limit_req_zone + limit_req au bon endroit dans la config)

sudo nginx -t && sudo systemctl reload nginx
echo "✅ Rate-limit actif sur /api/auth/login et /api/auth/admin/verify-otp"


# ═══════════════════════════════════════════════════════════════
# BLOC 5 — VÉRIFICATIONS POST-DÉPLOIEMENT (smoke tests)
# ═══════════════════════════════════════════════════════════════
# Landing publique
curl -I https://metro-taxi.com/saint-denis | head -3

# Alias court
curl -I https://metro-taxi.com/93 | head -3

# TTS public (1ère fois → génère, 2e fois → cache)
curl -o /tmp/test_alert.mp3 -w "HTTP %{http_code}, Size: %{size_download}\n" \
  "https://metro-taxi.com/api/tts/transfer-alert?lang=fr&role=user"

# Info alertes (vérifie que les 8 sont cached)
curl https://metro-taxi.com/api/tts/transfer-alerts/info | python3 -m json.tool


# ═══════════════════════════════════════════════════════════════
# 🆘 EN CAS DE PÉPIN — ROLLBACK RAPIDE
# ═══════════════════════════════════════════════════════════════
# cd /var/www/metro-taxi-app
# git log --oneline -10            # repère le commit précédent
# git reset --hard <HASH_PRECEDENT>
# cd frontend && yarn build
# pm2 restart all --update-env

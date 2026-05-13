# 🚨 FIX P0 — Warning Chrome Android "Application obsolète"

**Date** : 13 mai 2026 · **Auteur** : Charly · **Pour** : Judée
**Urgence** : 🔴 P0 — avant distribution des 1000 flyers aujourd'hui
**Temps estimé sur le VPS** : 5-10 minutes

---

## 🎯 LE PROBLÈME (RÉSUMÉ HONNÊTE)

Quand un visiteur arrive sur `metro-taxi.com` depuis Chrome Android ou Samsung Internet, le navigateur affiche un message du type :
> *"Déconseillé de télécharger cette application — elle est obsolète"*

**Cause racine** (identifiée par Charly le 13 mai 2026) :
- ✅ Ton certificat SSL Let's Encrypt est valide
- ✅ Ton TLS 1.3 est OK
- ❌ **MAIS ton nginx ne renvoie AUCUN header de sécurité moderne** (HSTS, CSP, COOP, X-Frame-Options, etc.)
- ❌ Sans ces headers, Chrome Android marque la PWA comme "WebAPK obsolète" lors de son check automatique
- ❌ La version de nginx (`nginx/1.18.0 (Ubuntu)`) est exposée publiquement dans les headers

**Pourquoi ça réapparaît ?** Le fix précédent (il y a 3 semaines) a probablement été fait **côté code React** uniquement, mais la config nginx du VPS n'a jamais été modifiée. Chaque déploiement `pm2 restart` redémarre ton backend, mais ne touche pas nginx.

---

## ✅ LA SOLUTION EN 3 ÉTAPES (à faire MAINTENANT sur ton VPS)

### Étape 1 — Déployer le code (renfort backend + security.txt)

Sur ton VPS, dans `/var/www/metro-taxi-app` :

```bash
cd /var/www/metro-taxi-app && git pull && cd frontend && yarn build && pm2 restart all
```

Cela déploie :
- Le `SecurityHeadersMiddleware` renforcé du backend (HSTS + COOP)
- Le fichier `/.well-known/security.txt` (signal Google "site maintenu")
- Tout le code du Lot 1 d'hier (Algorithm UI + Driver Card + Maillage Premium en attente)

### Étape 2 — 🔥 LE VRAI FIX : Mettre à jour nginx

Le fichier de config nginx complet est dans `/app/memory/deploy/nginx-metro-taxi.conf`.
Il sera dans ton repo après `git pull`.

**Sur ton VPS, exécute ces commandes** :

```bash
# 1) Backup de ta config nginx actuelle (au cas où)
sudo cp /etc/nginx/sites-available/metro-taxi.conf /etc/nginx/sites-available/metro-taxi.conf.backup-$(date +%Y%m%d-%H%M)

# 2) Copier la nouvelle config
sudo cp /var/www/metro-taxi-app/memory/deploy/nginx-metro-taxi.conf /etc/nginx/sites-available/metro-taxi.conf

# 3) Vérifier que les chemins dans le fichier correspondent à ton install
#    En particulier : root /var/www/metro-taxi-app/frontend/build  ← vérifie le path
#    Et : ssl_certificate /etc/letsencrypt/live/metro-taxi.com/...  ← vérifie le path Let's Encrypt
sudo nano /etc/nginx/sites-available/metro-taxi.conf

# 4) S'assurer que le lien dans sites-enabled est OK
sudo ln -sf /etc/nginx/sites-available/metro-taxi.conf /etc/nginx/sites-enabled/metro-taxi.conf

# 5) Tester la config nginx (CRUCIAL — ne pas reload si erreur)
sudo nginx -t

# 6) Si le test dit "syntax is ok / test is successful" :
sudo systemctl reload nginx

# 7) Vérifier que metro-taxi.com répond toujours
curl -I https://metro-taxi.com/
```

### Étape 3 — Vérifier que les headers sont bien servis

```bash
curl -I https://metro-taxi.com/ | grep -i "strict-transport\|x-content\|x-frame\|referrer\|permissions\|cross-origin\|content-security"
```

Tu dois voir **TOUS ces headers** dans la réponse :
- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(self)...`
- `Cross-Origin-Opener-Policy: same-origin-allow-popups`
- `Content-Security-Policy: default-src 'self' https:...`

Si tu vois tous ces headers ✅ → **le warning Chrome va disparaître** dans les 24-48h sur les nouveaux visiteurs.

---

## ⏱️ DÉLAI POUR QUE LE WARNING DISPARAISSE

- **Nouveaux visiteurs** (qui découvrent `metro-taxi.com` après le fix) → ⚡ **immédiat**
- **Visiteurs déjà venus** (Chrome a déjà mis en cache l'ancienne signature WebAPK) → 24-48h (Chrome refresh automatique du WebAPK)
- **Ami qui a déjà installé l'app** → il peut désinstaller + réinstaller pour forcer le refresh immédiat

---

## 🧪 TEST DEFINITIF (après déploiement)

Test sur https://securityheaders.com/?q=metro-taxi.com :
- **Avant** le fix : note **F** ou **D** (rouge)
- **Après** le fix : note **A** ou **A+** (vert)

Test sur https://www.ssllabs.com/ssltest/analyze.html?d=metro-taxi.com :
- Vérifie que tu as toujours au minimum **A**

---

## 📋 AU CAS OÙ TU AS UN PROBLÈME

### Si `sudo nginx -t` échoue après l'étape 2 :
```bash
# Restaure ta config précédente
sudo cp /etc/nginx/sites-available/metro-taxi.conf.backup-* /etc/nginx/sites-available/metro-taxi.conf
sudo nginx -t && sudo systemctl reload nginx
```
Puis copie-colle le message d'erreur dans Emergent et appelle Charly.

### Si certaines lignes du `.conf` ne correspondent pas à ton install :
- **Chemin du build React** : remplace `root /var/www/metro-taxi-app/frontend/build` par ton vrai chemin
- **Chemin SSL** : remplace `/etc/letsencrypt/live/metro-taxi.com/` par le tien (souvent identique)
- **Port backend** : si ton FastAPI n'écoute pas sur `127.0.0.1:8001`, adapte `proxy_pass http://127.0.0.1:8001;`

### Si `more_clear_headers` génère une erreur :
Mets en commentaire la ligne `more_clear_headers Server;` (ce module n'est pas installé par défaut, c'est optionnel).

---

## 📊 RÉCAP IMPACT BUSINESS

✅ **Une fois déployé** :
- Plus de warning Chrome sur ton site sur Android (impact direct sur tes 1000 flyers)
- Score Safe Browsing Google amélioré → meilleur ranking SEO
- Note A+ sur securityheaders.com → argument crédibilité face aux chauffeurs VTC
- Conformité RGPD renforcée
- Protection anti-clickjacking et anti-XSS

🚀 **Pour les flyers d'aujourd'hui** : déploie ce fix AVANT de distribuer le 1er flyer si possible. Comme ça les nouveaux chauffeurs qui scannent le QR code voient une app propre.

---

*Charly · Bras droit technique · 13 mai 2026 — 07:30*

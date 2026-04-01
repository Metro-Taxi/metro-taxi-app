# 🚀 Guide de Déploiement Métro-Taxi

## Prérequis

- Un serveur (VPS, Dedicated Server) avec :
  - Ubuntu 20.04+ ou Debian 11+
  - Docker & Docker Compose
  - Nginx
  - Certificat SSL (Let's Encrypt)
  
- Domaine configuré : `metro-taxi.com`

---

## Étape 1 : Configuration DNS

Ajoutez ces enregistrements DNS chez Hostinger :

| Type | Nom | Valeur |
|------|-----|--------|
| A | @ | `IP_DE_VOTRE_SERVEUR` |
| A | www | `IP_DE_VOTRE_SERVEUR` |
| CNAME | api | @ |

---

## Étape 2 : Préparation du Serveur

```bash
# Connexion SSH
ssh root@IP_DE_VOTRE_SERVEUR

# Mise à jour
apt update && apt upgrade -y

# Installation Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Installation Docker Compose
apt install docker-compose -y

# Installation Nginx
apt install nginx certbot python3-certbot-nginx -y
```

---

## Étape 3 : Cloner le Projet

```bash
# Créer le répertoire
mkdir -p /var/www/metro-taxi
cd /var/www/metro-taxi

# Cloner depuis GitHub (si configuré)
git clone https://github.com/VOTRE_REPO/metro-taxi.git .

# Ou télécharger depuis Emergent et extraire
# (Utilisez la fonction "Download Code" sur Emergent)
```

---

## Étape 4 : Configuration des Variables d'Environnement

### Backend (.env)
```bash
# /var/www/metro-taxi/backend/.env
MONGO_URL=mongodb://mongodb:27017
DB_NAME=metro_taxi
JWT_SECRET=VOTRE_SECRET_TRES_SECURISE
STRIPE_API_KEY=sk_live_VOTRE_CLE_STRIPE_LIVE
RESEND_API_KEY=re_VOTRE_CLE_RESEND
SENDER_EMAIL=noreply@metro-taxi.com
```

### Frontend (.env)
```bash
# /var/www/metro-taxi/frontend/.env
REACT_APP_BACKEND_URL=https://metro-taxi.com
```

---

## Étape 5 : Docker Compose

Créez `/var/www/metro-taxi/docker-compose.yml` :

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: metro-taxi-mongodb
    restart: always
    volumes:
      - mongodb_data:/data/db
    networks:
      - metro-network

  backend:
    build: ./backend
    container_name: metro-taxi-backend
    restart: always
    ports:
      - "8001:8001"
    depends_on:
      - mongodb
    env_file:
      - ./backend/.env
    networks:
      - metro-network

  frontend:
    build: ./frontend
    container_name: metro-taxi-frontend
    restart: always
    ports:
      - "3000:3000"
    env_file:
      - ./frontend/.env
    networks:
      - metro-network

volumes:
  mongodb_data:

networks:
  metro-network:
    driver: bridge
```

---

## Étape 6 : Dockerfile Backend

Créez `/var/www/metro-taxi/backend/Dockerfile` :

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

---

## Étape 7 : Dockerfile Frontend

Créez `/var/www/metro-taxi/frontend/Dockerfile` :

```dockerfile
FROM node:18-alpine as builder

WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY . .
RUN yarn build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

---

## Étape 8 : Configuration Nginx

```bash
# /etc/nginx/sites-available/metro-taxi
server {
    listen 80;
    server_name metro-taxi.com www.metro-taxi.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name metro-taxi.com www.metro-taxi.com;

    ssl_certificate /etc/letsencrypt/live/metro-taxi.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/metro-taxi.com/privkey.pem;

    # API Backend
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Activez le site :
```bash
ln -s /etc/nginx/sites-available/metro-taxi /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

---

## Étape 9 : Certificat SSL

```bash
certbot --nginx -d metro-taxi.com -d www.metro-taxi.com
```

---

## Étape 10 : Lancement

```bash
cd /var/www/metro-taxi
docker-compose up -d --build
```

Vérifiez :
```bash
docker-compose ps
docker-compose logs -f
```

---

## 🎉 Votre application est déployée !

Accédez à : https://metro-taxi.com

---

## Maintenance

### Mise à jour
```bash
cd /var/www/metro-taxi
git pull
docker-compose up -d --build
```

### Logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Backup MongoDB
```bash
docker exec metro-taxi-mongodb mongodump --out /backup
docker cp metro-taxi-mongodb:/backup ./backup
```

---

## Support

En cas de problème :
1. Vérifiez les logs Docker
2. Vérifiez la configuration Nginx
3. Vérifiez les variables d'environnement
4. Vérifiez la connexion MongoDB

---

## 🌍 Configuration Multi-Régions (Sous-domaines)

Pour déployer Metro-Taxi avec des sous-domaines par région (paris.metro-taxi.com, lyon.metro-taxi.com, etc.) :

### 1. Configuration DNS

Ajoutez ces enregistrements DNS pour chaque région :

| Type | Nom | Valeur |
|------|-----|--------|
| A | paris | `IP_DE_VOTRE_SERVEUR` |
| A | lyon | `IP_DE_VOTRE_SERVEUR` |
| A | london | `IP_DE_VOTRE_SERVEUR` |

### 2. Configuration Nginx Multi-Régions

```nginx
# /etc/nginx/sites-available/metro-taxi-regions

# Redirection HTTP -> HTTPS pour tous les sous-domaines
server {
    listen 80;
    server_name *.metro-taxi.com;
    return 301 https://$host$request_uri;
}

# Configuration HTTPS pour les sous-domaines régionaux
server {
    listen 443 ssl http2;
    server_name ~^(?<region>.+)\.metro-taxi\.com$;

    ssl_certificate /etc/letsencrypt/live/metro-taxi.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/metro-taxi.com/privkey.pem;

    # API Backend avec région en header
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header X-Region $region;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header X-Region $region;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Region $region;
    }
}
```

### 3. Certificat SSL Wildcard

```bash
# Installer certbot avec plugin DNS (exemple avec Cloudflare)
pip install certbot-dns-cloudflare

# Créer fichier credentials
cat > /root/.cloudflare.ini << EOF
dns_cloudflare_email = votre@email.com
dns_cloudflare_api_key = votre_cle_api_cloudflare
EOF
chmod 600 /root/.cloudflare.ini

# Générer certificat wildcard
certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials /root/.cloudflare.ini \
  -d metro-taxi.com \
  -d *.metro-taxi.com
```

### 4. Détection Région dans le Frontend

Le frontend détecte automatiquement la région via l'URL :

```javascript
// Dans votre code React
const getRegionFromUrl = () => {
  const hostname = window.location.hostname;
  const match = hostname.match(/^([a-z]+)\.metro-taxi\.com$/);
  return match ? match[1] : 'paris'; // Paris par défaut
};
```

### 5. Régions Disponibles

| Région | Sous-domaine | Code |
|--------|--------------|------|
| Île-de-France | paris.metro-taxi.com | `paris` |
| Rhône-Alpes | lyon.metro-taxi.com | `lyon` |
| Greater London | london.metro-taxi.com | `london` |

---

## 📱 PWA - Installation Mobile

L'application est une Progressive Web App installable :

1. Ouvrez https://metro-taxi.com sur mobile
2. Cliquez sur "Ajouter à l'écran d'accueil"
3. L'app fonctionne comme une application native

### Configuration PWA

Les fichiers PWA sont dans `/frontend/public/` :
- `manifest.json` - Configuration de l'app
- `sw.js` - Service Worker pour le cache
- `icons/` - Icônes de l'app

---

## 🔔 Notifications Push (VAPID)

Les clés VAPID sont configurées dans `/backend/.env` :

```bash
VAPID_PUBLIC_KEY=votre_cle_publique
VAPID_PRIVATE_KEY=votre_cle_privee
VAPID_CONTACT=mailto:contact@metro-taxi.com
```

Pour générer de nouvelles clés :
```bash
python3 -c "
from py_vapid import Vapid
v = Vapid()
v.generate_keys()
print('PUBLIC:', v.public_key_urlsafe_base64())
print('PRIVATE:', v.private_pem().decode())
"
```

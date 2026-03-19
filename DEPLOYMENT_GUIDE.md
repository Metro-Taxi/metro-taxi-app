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

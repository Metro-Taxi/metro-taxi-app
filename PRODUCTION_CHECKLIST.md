# 🚀 Checklist de Déploiement Production - Métro-Taxi

## ✅ Pré-Déploiement

### 1. Variables d'Environnement
- [ ] `MONGO_URL` - URL MongoDB production
- [ ] `JWT_SECRET` - Clé secrète unique (générer avec `openssl rand -hex 32`)
- [ ] `STRIPE_SECRET_KEY` - Clé Stripe LIVE (sk_live_...)
- [ ] `STRIPE_WEBHOOK_SECRET` - Secret webhook Stripe
- [ ] `RESEND_API_KEY` - Clé API Resend pour emails
- [ ] `VAPID_PUBLIC_KEY` - Clé publique notifications push
- [ ] `VAPID_PRIVATE_KEY` - Clé privée notifications push
- [ ] `VAPID_CONTACT` - Email de contact (mailto:...)
- [ ] `EMERGENT_API_KEY` - Clé API pour LLM/Chatbot
- [ ] `FRONTEND_URL` - URL de production (https://metro-taxi.com)
- [ ] `CORS_ORIGINS` - Origines autorisées

### 2. Base de Données MongoDB
- [ ] Créer les index nécessaires :
  ```javascript
  db.users.createIndex({ "email": 1 }, { unique: true })
  db.drivers.createIndex({ "email": 1 }, { unique: true })
  db.drivers.createIndex({ "location": "2dsphere" })
  db.drivers.createIndex({ "is_active": 1, "is_validated": 1 })
  db.ride_requests.createIndex({ "status": 1 })
  ```
- [ ] Sauvegardes automatiques configurées
- [ ] Utilisateur MongoDB dédié avec permissions restreintes

### 3. SSL/TLS
- [ ] Certificat SSL valide (Let's Encrypt ou autre)
- [ ] Redirection HTTP → HTTPS
- [ ] Headers de sécurité (HSTS, CSP, etc.)

### 4. Stripe
- [ ] Mode LIVE activé
- [ ] Webhook configuré sur `https://votre-domaine.com/api/webhooks/stripe`
- [ ] Plans d'abonnement créés dans le dashboard Stripe
- [ ] Stripe Connect activé pour les virements chauffeurs

### 5. DNS
- [ ] Enregistrement A pour domaine principal
- [ ] Enregistrements A pour sous-domaines régionaux (optionnel)
- [ ] Enregistrement MX pour emails (si applicable)

## ✅ Déploiement

### 6. Backend
- [ ] `pip install -r requirements.txt`
- [ ] Variables d'environnement chargées
- [ ] Service systemd ou supervisor configuré
- [ ] Logs configurés (rotation, niveau INFO en prod)

### 7. Frontend
- [ ] `yarn build` exécuté
- [ ] Build servi par Nginx ou CDN
- [ ] Service Worker enregistré
- [ ] manifest.json accessible

### 8. Nginx / Reverse Proxy
- [ ] Configuration SSL
- [ ] Proxy vers backend (port 8001)
- [ ] Proxy WebSocket (/ws)
- [ ] Gzip compression activée
- [ ] Cache headers pour assets statiques

## ✅ Post-Déploiement

### 9. Tests de Fumée
- [ ] Page d'accueil charge
- [ ] Inscription utilisateur fonctionne
- [ ] Inscription chauffeur fonctionne
- [ ] Login fonctionne
- [ ] Carte s'affiche
- [ ] Paiement test réussi
- [ ] Email de confirmation reçu
- [ ] Notifications push fonctionnent

### 10. Monitoring
- [ ] Alertes sur erreurs 500
- [ ] Monitoring uptime
- [ ] Logs centralisés
- [ ] Métriques de performance

### 11. Sécurité
- [ ] Authentification admin changée (pas admin123!)
- [ ] Rate limiting configuré
- [ ] Firewall configuré
- [ ] Accès SSH sécurisé

## 📞 Contacts d'Urgence

- **Stripe Support**: https://support.stripe.com
- **MongoDB Atlas**: https://cloud.mongodb.com/support
- **Resend**: https://resend.com/support

## 🔄 Procédure de Rollback

1. Arrêter les services : `sudo systemctl stop metro-taxi-backend metro-taxi-frontend`
2. Restaurer la version précédente du code
3. Restaurer la base de données si nécessaire
4. Redémarrer les services
5. Vérifier les logs

# 🧹 Script de nettoyage DB Production — Réassignation des Pionniers

**Auteur** : Charly · **Date** : 12 mai 2026 · **Pour** : Judée
**À exécuter sur le VPS** : `srv1551870` · **DB** : `metro_taxi_prod` (ou nom configuré dans `backend/.env`)

---

## ⚠️ AVANT DE COMMENCER

1. **FAIS UN BACKUP** de la collection `drivers` :
   ```bash
   mongodump --db=$(grep DB_NAME /var/www/metro-taxi-app/backend/.env | cut -d '=' -f2) \
     --collection=drivers \
     --out=/root/backups/drivers-$(date +%Y%m%d-%H%M)
   ```

2. **Connecte-toi à Mongo Shell** :
   ```bash
   mongosh
   ```

3. Dans `mongosh`, sélectionne la base :
   ```javascript
   use $(grep DB_NAME /var/www/metro-taxi-app/backend/.env | cut -d '=' -f2)
   // ou directement, si tu connais le nom :
   // use metro_taxi_prod
   ```

---

## 📋 ÉTAPE 1 — Inventaire actuel (lecture seule)

Voir tous les chauffeurs triés par date d'inscription (les vrais pionniers d'abord) :

```javascript
db.drivers.find({}, {
  first_name: 1, last_name: 1, email: 1,
  pioneer_number: 1, created_at: 1, _id: 0
}).sort({ created_at: 1 }).pretty()
```

**Objectif** : repérer les 9 vrais chauffeurs pionniers (par ordre chronologique) vs les comptes de test à supprimer.

Selon la roadmap, les 9 pionniers historiques sont :

| # | Nom | Email attendu | Date |
|---|-----|---------------|------|
| 1 | Ali Ousmanou | (à confirmer) | 5 avril 2026 |
| 2 | Mohsen Soudane | (à confirmer) | 26 avril 2026 |
| 3 | Brigitte Auguste | (à confirmer) | 27 avril 2026 |
| 4 | Ibrahima Soumare | (à confirmer) | 9 mai 2026 (CDG T1) |
| 5 | Mayoux Kalonji | (à confirmer) | 9 mai 2026 (CDG T1) |
| 6 | Nizar Soumaya | (à confirmer) | 9 mai 2026 (CDG T1) |
| 7-9 | (3 nouveaux) | (à confirmer) | 10 mai 2026 |

---

## 🗑️ ÉTAPE 2 — Supprimer les comptes de test (À ADAPTER)

⚠️ **Adapte la liste des emails ci-dessous AVANT de lancer.**
Vérifie 2 fois — la suppression est définitive.

```javascript
// Exemple : adapte cette liste à TES comptes de test réels
const testEmails = [
  "test@example.com",
  "demo@metro-taxi.com",
  "agent-test@example.com",
  // ... ajoute ici les emails de tes faux comptes
];

// Affiche d'abord ce qui sera supprimé (DRY RUN)
db.drivers.find({ email: { $in: testEmails } }, { first_name: 1, last_name: 1, email: 1, _id: 0 }).pretty()

// Quand tu es sûr, lance la suppression :
db.drivers.deleteMany({ email: { $in: testEmails } })
```

---

## 🔢 ÉTAPE 3 — Réassigner les numéros de pionniers (1 → N) par ordre chronologique

```javascript
// Lit tous les chauffeurs restants triés par date d'inscription (les plus anciens d'abord)
const drivers = db.drivers.find({}, { _id: 0, id: 1, email: 1, created_at: 1, first_name: 1, last_name: 1 })
  .sort({ created_at: 1 })
  .toArray();

print(`Total chauffeurs à renuméroter : ${drivers.length}`);

// Réassigne pioneer_number = 1, 2, 3, ... dans l'ordre chronologique
drivers.forEach((d, idx) => {
  const newPioneerNumber = idx + 1;
  db.drivers.updateOne(
    { id: d.id },
    { $set: { pioneer_number: newPioneerNumber } }
  );
  print(`Pionnier #${newPioneerNumber} → ${d.first_name} ${d.last_name} (${d.email})`);
});

print("✅ Réassignation terminée");
```

---

## ✅ ÉTAPE 4 — Vérification finale

```javascript
// Vérifier que tous les chauffeurs ont bien un pioneer_number unique et consécutif
db.drivers.find({}, {
  pioneer_number: 1, first_name: 1, last_name: 1, email: 1, created_at: 1, _id: 0
}).sort({ pioneer_number: 1 }).pretty()
```

Attendu :
- Pionnier #1 → Ali Ousmanou (le 1er inscrit)
- Pionnier #2 → Mohsen Soudane
- ... etc.
- Pas de trou (1, 2, 3, ..., N sans saut)

---

## 🚨 EN CAS DE PROBLÈME — Restauration du backup

```bash
mongorestore --db=$(grep DB_NAME /var/www/metro-taxi-app/backend/.env | cut -d '=' -f2) \
  --collection=drivers \
  --drop \
  /root/backups/drivers-YYYYMMDD-HHMM/$(grep DB_NAME /var/www/metro-taxi-app/backend/.env | cut -d '=' -f2)/drivers.bson
```

---

## 📝 Notes Charly

- **Pourquoi par `created_at` ?** Parce que c'est le critère le plus juste : le 1er à s'être inscrit est le pionnier #1, point. Pas de subjectivité.
- **Pourquoi pas par email ?** Parce que tu pourrais te tromper si tu fais le mapping manuel. L'ordre chronologique est gravé dans la DB, c'est plus sûr.
- Si jamais 2 chauffeurs ont exactement le même `created_at` (ultra rare), Mongo départage par ObjectId — pas de souci.
- Si tu veux **forcer manuellement** un mapping spécifique (par ex. mettre Brigitte en #1 parce qu'elle est ta 1ère chauffeuse femme, etc.), tu peux remplacer l'étape 3 par :
  ```javascript
  db.drivers.updateOne({ email: "brigitte@example.com" }, { $set: { pioneer_number: 1 } });
  db.drivers.updateOne({ email: "ali@example.com" },      { $set: { pioneer_number: 2 } });
  // etc.
  ```

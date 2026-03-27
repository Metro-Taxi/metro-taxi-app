# DOCUMENT CONFIDENTIEL - PROPRIÉTÉ EXCLUSIVE
# MÉTRO-TAXI - ALGORITHME DE TRANSBORDEMENTS INTELLIGENTS
# =========================================================
# Inventeur : Judee Hamadjoulde Souleymane Nazim
# Date de création du concept : [À compléter]
# Marque déposée INPI : MÉTRO-TAXI (il y a 7 ans)
# =========================================================
# CE DOCUMENT CONSTITUE UN SECRET COMMERCIAL
# Toute reproduction ou divulgation est strictement interdite
# =========================================================

## 1. RÉSUMÉ DE L'INNOVATION

### Le concept unique "Métro sur route"
Métro-Taxi révolutionne le transport urbain en combinant :
- **Le modèle économique du métro** : Abonnement à prix fixe, trajets illimités
- **La flexibilité du taxi** : Service porte-à-porte personnalisé
- **L'intelligence du covoiturage** : Optimisation multi-chauffeurs avec transbordements

### Différenciation vs concurrents
| Critère | Métro-Taxi | Uber/Bolt/Heetch |
|---------|------------|------------------|
| Modèle tarifaire | Abonnement fixe (~17€/semaine) | Paiement à la course |
| Trajets | Illimités | Chaque trajet facturé |
| Transbordements | OUI (jusqu'à 2) | NON |
| Rémunération chauffeur | 1,50€/km (attractive) | Commission 25-30% |
| Optimisation réseau | Intelligente | Point A → Point B simple |

---

## 2. ALGORITHME CENTRAL - SPÉCIFICATIONS TECHNIQUES

### 2.1 Constantes de l'algorithme
```
SEGMENT_MIN_KM = 1.5      # Distance minimale d'un segment
SEGMENT_MAX_KM = 3.0      # Distance maximale avant transbordement suggéré
MAX_PICKUP_DISTANCE = 2.0 # Distance max de prise en charge
MAX_TRANSFERS = 2         # Nombre maximum de transbordements
DIRECTION_THRESHOLD = 60  # Score minimum de compatibilité directionnelle (0-100)
```

### 2.2 Calcul de compatibilité directionnelle
L'algorithme utilise la **similarité cosinus** pour évaluer si un chauffeur 
va dans la même direction que la destination de l'usager :

```
Score = ((vecteur_chauffeur · vecteur_usager) / (|chauffeur| × |usager|) + 1) × 50
```

- Score 100 = Même direction exacte
- Score 50 = Direction perpendiculaire
- Score 0 = Direction opposée
- Seuil d'acceptation = 60

### 2.3 Logique de segmentation intelligente
1. **Trajet court (< 3km)** : Route directe, 1 seul chauffeur
2. **Trajet moyen (3-6km)** : 1 transbordement, 2 segments
3. **Trajet long (> 6km)** : Jusqu'à 2 transbordements, 3 segments

### 2.4 Calcul du point de transbordement optimal
```
Point_transfert = Point_départ + (Point_arrivée - Point_départ) × (distance_segment / distance_totale)
```
L'algorithme utilise l'interpolation linéaire pour positionner les points 
de transbordement de manière équidistante le long du trajet.

### 2.5 Sélection des chauffeurs par segment
Pour chaque segment, l'algorithme :
1. Recherche les chauffeurs disponibles dans un rayon de 2km
2. Calcule le score de compatibilité directionnelle
3. Exclut les chauffeurs déjà utilisés sur les segments précédents
4. Classe par score et propose des alternatives

---

## 3. MODÈLE ÉCONOMIQUE RÉVOLUTIONNAIRE

### 3.1 Grille tarifaire usagers
| Abonnement | Prix | Trajets | Coût par trajet estimé* |
|------------|------|---------|-------------------------|
| 24 heures | 6,99€ | Illimités | ~1,40€ (5 trajets) |
| 1 semaine | 16,99€ | Illimités | ~0,61€ (28 trajets) |
| 1 mois | 53,99€ | Illimités | ~0,45€ (120 trajets) |

*Estimé sur usage moyen

### 3.2 Rémunération chauffeurs
```
Revenu = Distance_parcourue_avec_usager × 1,50€/km
```

- **Pas de commission plateforme** sur les revenus des chauffeurs
- **Virement automatique** le 10 de chaque mois via Stripe Connect
- **Transparence totale** : Dashboard avec KM, revenus, historique

### 3.3 Viabilité économique
Le modèle fonctionne car :
1. Les transbordements maximisent le taux de remplissage des véhicules
2. Les chauffeurs optimisent leurs trajets (pas de retour à vide)
3. Le volume d'abonnés compense le prix bas individuel
4. La fidélisation client réduit les coûts d'acquisition

---

## 4. FICHIERS SOURCE CLÉS

| Fichier | Contenu |
|---------|---------|
| `/app/backend/server.py` | Algorithme central (lignes 65-520) |
| Fonction `calculate_direction_score()` | Compatibilité chauffeur/usager |
| Fonction `find_optimal_transfer_point()` | Calcul points de transbordement |
| Fonction `calculate_multi_transfer_route()` | Planification trajet complet |
| Fonction `find_drivers_for_segment()` | Sélection chauffeurs par segment |

---

## 5. PROTECTION INTELLECTUELLE

### 5.1 Protections existantes
- ✅ Marque "MÉTRO-TAXI" déposée INPI (valide ~3 ans)
- ✅ Droit d'auteur automatique sur le code source
- ✅ Secret commercial (ce document)

### 5.2 Protections recommandées
- [ ] Dépôt de brevet européen (OEB) pour l'algorithme de transbordements
- [ ] Enveloppe Soleau pour preuve d'antériorité
- [ ] Renouvellement marque INPI avant expiration
- [ ] Dépôt dessin/modèle pour l'interface utilisateur

### 5.3 Démarches de protection
1. Conserver ce document en lieu sûr
2. Consulter un avocat spécialisé en brevets logiciels
3. Envisager dépôt PCT pour protection internationale

---

## 6. HISTORIQUE DES VERSIONS

| Date | Version | Modifications |
|------|---------|---------------|
| Mars 2026 | 1.0 | Création du document |

---

**RAPPEL : CE DOCUMENT EST STRICTEMENT CONFIDENTIEL**
Propriété exclusive de Judee Hamadjoulde Souleymane Nazim
© 2026 Métro-Taxi - Tous droits réservés

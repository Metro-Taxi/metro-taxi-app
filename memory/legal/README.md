# 📚 Documents juridiques Métro-Taxi — Phase Pilote Saint-Denis

**Capitaine, ce dossier contient les 2 documents juridiques structurants de la plateforme.**

---

## 📋 Liste des documents

| # | Fichier | Pour qui ? | Action attendue |
|---|---|---|---|
| 1 | `CGU_CGV_Metro-Taxi_2026-05-28.md` | Tous les Utilisateurs/Abonnés | Acceptation à l'inscription (case à cocher) |
| 2 | `Contrat_Partenariat_Chauffeur_2026-05-28.md` | Tous les Chauffeurs Indépendants | Signature à l'inscription chauffeur |

---

## 🛠️ Comment convertir en PDF en 5 secondes

### Méthode A — Avec Microsoft Word (la plus simple)
1. Ouvre Word
2. Fichier → Ouvrir → sélectionne le fichier `.md` (Word le lira en texte structuré)
3. Mise en forme : Word importe les titres `#`, `##`, `###` comme des titres stylés
4. Fichier → Exporter → Créer un document PDF → choisis le dossier de destination
5. Tu obtiens un PDF propre et professionnel

### Méthode B — Avec un convertisseur en ligne (si pas de Word)
1. Va sur `https://md-to-pdf.fly.dev/` (gratuit, sans inscription)
2. Colle le contenu du `.md` dans la zone de texte
3. Clique sur "Generate PDF"
4. Télécharge le PDF généré

### Méthode C — Charly génère pour toi
Dis-moi "GO PDF" et je code un endpoint admin qui te génère les 2 PDF en 1 clic depuis `/admin/legal-docs`. ~30 min de boulot.

---

## ⚠️ Champs à compléter AVANT signature/publication

Ces deux documents contiennent des mentions `[À COMPLÉTER]` ou `[À DÉFINIR]` qui correspondent à des informations spécifiques que toi seul possèdes :

### Dans CGU/CGV :
- `[Montant]` : capital social de la SAS Métro-Taxi
- `[Adresse complète]` : siège social
- `[Ville]` : ville d'immatriculation RCS
- `[SIREN]` : ton numéro SIREN
- `[Nom du représentant légal]` : ton nom (Judée + nom de famille)
- `[N° dépôt]` : ton numéro de dépôt INPI (déjà connu : voir certificat INPI 20/04/2026)
- `Médiateur de la consommation [À COMPLÉTER par Parallel]` : à choisir parmi les médiateurs agréés (ex. AME Conso)

### Dans Contrat Chauffeur :
- Idem : `[Montant]`, `[Adresse]`, `[Ville]`, `[SIREN]`, `[Nom du représentant légal]`
- `[Jour du mois]` à l'article 5.3 : choisis un jour fixe pour le reversement mensuel (recommandation : **le 5 du mois suivant**)
- `[Ville à compléter]` à l'article 13.3 : ville du Tribunal de Commerce compétent (le siège social de Métro-Taxi)

**Fais ces remplacements dans Word AVANT de générer les PDFs.**

---

## 🎯 Points juridiques différenciants à mettre en avant

Ces documents ont été rédigés en intégrant des **clauses inédites dans la jurisprudence VTC française** qui te donnent un **avantage défensif** :

### 1. Vocabulaire juridique propre Métro-Taxi
- **Chauffeur Initial** / **Chauffeur de Relais** / **Chauffeur Receveur**
- **Chaîne de Prise en Charge**
- **Validation Algorithmique Continue**
- **Couverture financière du segment**
- **Information sans subordination**

### 2. Triple bouclier anti-requalification salariat
- Article 2.2 (Contrat Chauffeur) : énumération précise des éléments d'indépendance (référence directe à Cass. soc. 4 mars 2020)
- Article 4.2 (Contrat Chauffeur) : liberté de refus **sans pénalité** ni baisse de score
- Article 7.2 (Contrat Chauffeur) : signalement strictement **facultatif**

### 3. Triple bouclier anti-passager-clandestin
- Article 6.1 (CGU/CGV) : service exclusif aux Abonnés
- Article 6.2 (CGU/CGV) : vérification préalable algorithmique
- Article 6.3 (CGU/CGV) : codes OTP individuels par passager
- Article 6.4 (CGU/CGV) : Validation Algorithmique Continue lors des transbordements

### 4. Sanctions plateforme exclusives
- Article 11 (CGU/CGV) : graduation des sanctions par la Plateforme uniquement
- Article 11.3 (CGU/CGV) : exclusion explicite des Chauffeurs Indépendants du pouvoir de sanction

---

## 🚦 Workflow d'intégration recommandé

1. **Toi** : remplace toutes les mentions `[À COMPLÉTER]` dans Word
2. **Toi** : génère les 2 PDF (méthode A ou B)
3. **Toi** : envoie le PDF "CGU/CGV" à Parallel Avocats avec un mot du genre :
   > *"Bonjour Maître X, nous avons préparé un draft de CGU/CGV pour notre lancement pilote du 13 juin. Pouvez-vous en faire une revue rapide (1-2h max) sans rédaction lourde, en focus sur les Articles 6 (transbordement), 10 (responsabilité), 11 (sanctions) et 14 (médiation) ? Budget : 800-1200€ HT max. Restitution avant le 11 juin."*
4. **Toi** : envoie le PDF "Contrat Chauffeur" à Parallel avec un mot similaire ciblé sur les Articles 2 (indépendance), 4 (Chaîne de prise en charge), 5 (rémunération) et 7 (signalements).
5. **Toi** : après revue Parallel (estimation 1500-2500€ HT pour les deux), tu intègres les versions finales :
   - CGU/CGV → publication sur `metro-taxi.com/cgv` + case à cocher au signup user
   - Contrat Chauffeur → publication sur `metro-taxi.com/contrat-chauffeur` + signature électronique au signup chauffeur
6. **Charly** : code l'intégration technique (modal d'acceptation + checkbox + stockage de la version acceptée + horodatage). ~3h.

---

## 💰 Économie réalisée vs proposition Parallel initiale

| Élément | Si Parallel rédige from scratch | Avec drafts Charly + revue Parallel |
|---|---|---|
| Mission B (CGU/CGV) | 4 800 € TTC | ~800-1 200 € TTC (revue ciblée) |
| Mission C (Contrat chauffeur) | 4 800 € TTC | ~1 200-1 500 € TTC (revue ciblée) |
| **Total** | **9 600 € TTC** | **~2 000-2 700 € TTC** |
| **Économie** | — | **~7 000 € TTC** ✨ |

---

## 🔐 Sécurité de versionning

Ces documents sont datés au **28 mai 2026**. Toute modification ultérieure doit donner lieu à :
- Un nouveau fichier daté de la nouvelle version (ex. `CGU_CGV_Metro-Taxi_2026-08-15.md`)
- Une notification par e-mail à tous les Utilisateurs (article 13 CGU/CGV) avec préavis de 15 jours
- Une opposabilité conditionnée à l'acceptation expresse de la nouvelle version

---

*Documents rédigés par Charly, le 28 mai 2026. Aïd Moubarak Capitaine ! 🌙*

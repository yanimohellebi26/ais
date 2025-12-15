# Spécifications Techniques - Phase 8 : Machine Learning - Niveau 1

> **Objectif** : Implémenter algorithmes ML de base pour clustering, classification et détection d'anomalies
> **Durée estimée** : 3-4 semaines
> **Priorité** : ⭐⭐⭐ HAUTE (Intelligence artificielle)

---

## 📋 Vue d'ensemble

Cette phase introduit les premiers algorithmes de machine learning pour automatiser l'analyse des données AIS : clustering spatial et comportemental, classification de types/statuts, détection d'anomalies non-supervisée. Focus sur approches traditionnelles (non deep learning) robustes et interprétables.

**Prérequis** :
- Phases 1-7 complétées
- Features engineerées disponibles
- Données nettoyées et validées
- Infrastructure Python + scikit-learn

**Objectifs** :
- Clustering automatique routes et comportements
- Classification types navires et statuts
- Détection anomalies navigation
- Prédictions simples (destination, ETA)
- Modèles interprétables et explicables
- Foundation pour Deep Learning (Phase 9)

**Technologies ML** :
- scikit-learn 1.3+
- XGBoost, LightGBM
- statsmodels
- imbalanced-learn
- SHAP pour explicabilité
- MLflow pour tracking

---

## 8.1 Clustering Non-Supervisé

### 8.1.1 K-Means sur positions géographiques

**Objectif** : Segmentation spatiale automatique du trafic maritime

**Fonctionnalités** :
- Clustering positions en K groupes géographiques
- Détermination automatique K optimal (Elbow, Silhouette)
- Identification centres de clusters (zones haute activité)
- Visualisation clusters sur carte
- Profil statistique par cluster
- Évolution temporelle clusters

**Technologies** :
- **scikit-learn** : KMeans, MiniBatchKMeans
- **Metrics** : silhouette_score, calinski_harabasz_score
- **Visualisation** : matplotlib, seaborn, plotly
- **Scaling** : MiniBatchKMeans pour millions positions
- **Projection** : pyproj pour coordonnées

**Preprocessing** :
- Extraction lat/lon positions valides
- Normalisation coordonnées (StandardScaler)
- Échantillonnage stratifié si volume élevé
- Filtrage positions is_valid=true
- Conversion degrés → distances métriques

**Détermination K optimal** :
1. **Elbow method** : inertia vs K (5-50)
2. **Silhouette score** : qualité clusters
3. **Gap statistic** : comparaison référence
4. **Davies-Bouldin index** : séparation clusters
5. **Validation domaine** : cohérence géographique

**Features clustering** :
- Latitude (normalisée)
- Longitude (normalisée)
- Optionnel : SOG, COG comme poids

**Analyse clusters** :
- Coordonnées centroïdes
- Rayon moyen (km)
- Nombre positions par cluster
- Types navires dominants
- Vitesses moyennes
- Périodes activité

**Applications** :
- Identifier zones géographiques naturelles
- Zones haute/faible activité
- Segmentation pour analyses ciblées
- Base pour route extraction

**Livrables** :
- Modèle K-Means pickled
- Table : `kmeans_position_clusters`
- Notebook : analyse K optimal
- Carte clusters colorés
- Rapport profils clusters

---

### 8.1.2 DBSCAN pour routes maritimes

**Objectif** : Extraction routes sans nombre clusters prédéfini

**Fonctionnalités** :
- Clustering density-based (formes arbitraires)
- Pas besoin spécifier K
- Détection automatique corridors
- Identification noise (positions isolées)
- Extraction routes complexes (non-linéaires)
- Clustering hiérarchique zones

**Technologies** :
- **scikit-learn** : DBSCAN
- **HDBSCAN** : version hiérarchique (pip install hdbscan)
- **Parameters** : eps (distance), min_samples
- **Metrics** : haversine pour coordonnées sphériques
- **Optimization** : ball_tree algorithm

**Paramétrage** :
- **eps** : rayon voisinage (0.01-0.1° ≈ 1-11 km)
- **min_samples** : points minimum cluster (10-100)
- **metric** : 'haversine' pour lat/lon
- **algorithm** : 'ball_tree' pour performance
- Tuning via grid search ou domaine expertise

**Preprocessing** :
- Conversion lat/lon en radians (haversine)
- Filtrage is_moving=true
- Sous-échantillonnage intelligent
- Par type navire séparément

**HDBSCAN avancé** :
- Clustering hiérarchique adaptatif
- min_cluster_size variable
- cluster_selection_method : 'eom' ou 'leaf'
- Meilleure gestion densités variables
- Extraction clusters multi-niveaux

**Extraction routes** :
- Clusters = corridors trafic
- Noise = positions hors routes
- Convex hull polygones clusters
- Centerline extraction (medial axis)
- Largeur route moyenne

**Post-processing** :
- Merger clusters adjacents similaires
- Filtrer clusters trop petits (< 50 positions)
- Valider cohérence directionnelle (COG)
- Nommer routes (ports connexion)

**Livrables** :
- Modèle DBSCAN par type navire
- Table : `dbscan_maritime_routes`
- Polygones routes (GeoJSON)
- Paramètres optimaux documentés
- Comparaison DBSCAN vs HDBSCAN

---

### 8.1.3 Clustering de comportements (SOG, COG patterns)

**Objectif** : Identifier profils comportementaux similaires

**Fonctionnalités** :
- Clustering multi-dimensionnel (SOG, COG, trajectoire)
- Identification patterns navigation
- Segmentation comportements types
- Profiling navires similaires
- Détection groupes opérationnels

**Technologies** :
- **scikit-learn** : KMeans, AgglomerativeClustering
- **Gaussian Mixture Models** : soft clustering
- **Feature engineering** : statistiques agrégées
- **Dimensionality reduction** : PCA préalable
- **Distance metrics** : Euclidean, Manhattan, DTW

**Features comportementales** :
1. **Vitesse** :
   - SOG moyenne, médiane, std
   - SOG max, percentiles (95%)
   - Temps < 1 nœud (%)
2. **Cap** :
   - COG variabilité (std)
   - Fréquence changements (> 30°)
   - Linéarité trajectoire
3. **Temporel** :
   - Patterns horaires (jour/nuit)
   - Durée moyenne voyages
   - Fréquence activité
4. **Spatial** :
   - Zones fréquentées
   - Distance côte moyenne
   - Tortuosité trajectoires
5. **Opérationnel** :
   - Ratio mouvement/arrêt
   - Temps ports vs mer
   - Fréquence gaps AIS

**Preprocessing** :
- Agrégation par navire (vessel_id)
- Normalisation features (StandardScaler)
- Imputation valeurs manquantes (median)
- Détection outliers (IQR method)

**Méthodes clustering** :

1. **K-Means**
   - Rapide, scalable
   - K optimal via Elbow + Silhouette
   - Profiles types distincts

2. **Hierarchical (Agglomerative)**
   - Dendrogramme visualisation
   - Cutting height optimal
   - Interprétabilité hiérarchie

3. **Gaussian Mixture Models**
   - Soft clustering (probabilités)
   - Gestion overlap comportements
   - BIC/AIC pour sélection composantes

**Profils comportementaux** :
- Cluster 1 : "Fast Movers" (cargo longue distance)
- Cluster 2 : "Coastal Cruisers" (cabotage)
- Cluster 3 : "Stationary Workers" (fishing, platform supply)
- Cluster 4 : "Port Hoppers" (short-sea shipping)
- Cluster 5 : "Irregular Patterns" (anomalies)

**Validation** :
- Cohérence avec vessel_type
- Stabilité clusters (resampling)
- Interprétabilité domaine
- Comparaison supervised baseline

**Livrables** :
- Modèles clustering comportemental
- Table : `vessel_behavior_clusters`
- Profils clusters documentés
- Visualisations PCA/t-SNE
- Assignment nouveau navire

---

### 8.1.4 Clustering temporel (patterns horaires)

**Objectif** : Segmenter navires par patterns temps d'activité

**Fonctionnalités** :
- Clustering patterns jour/nuit
- Identification horaires opération
- Segmentation week-end vs semaine
- Profils saisonniers
- Régularité activité

**Technologies** :
- **Time-series clustering** : tslearn
- **DTW** (Dynamic Time Warping) : distance séries
- **K-Shape** : clustering forme séries
- **Soft-DTW** : différentiable DTW
- **Seasonal decomposition** : statsmodels

**Features temporelles** :
1. **Patterns horaires** :
   - Activité par heure (24 bins)
   - Distribution jour/nuit
   - Pics activité

2. **Patterns hebdomadaires** :
   - Activité par jour semaine
   - Week-end vs semaine ratio
   - Régularité

3. **Patterns mensuels** :
   - Saisonnalité
   - Périodes haute/basse activité

**Construction time-series** :
- Vecteur 24D : positions par heure
- Vecteur 7D : positions par jour semaine
- Vecteur 12D : positions par mois
- Normalisation (sum=1 ou z-score)

**Méthodes** :

1. **K-Means sur time-series**
   - Distance euclidienne normalized
   - Centroïdes = patterns moyens

2. **DTW K-Means**
   - Distance DTW (elastic)
   - Gestion décalages temporels
   - tslearn.clustering.TimeSeriesKMeans

3. **K-Shape**
   - Shape-based clustering
   - Invariant amplitude
   - Cross-correlation distance

**Profils temporels** :
- **24/7 Operations** : cargo international
- **Business Hours** : services portuaires
- **Night Movers** : fishing, illegal activities
- **Weekend Warriors** : pleasure craft
- **Seasonal Workers** : tourism, fishing

**Applications** :
- Détection activités nocturnes suspectes
- Identification lignes régulières
- Prévision disponibilité navires
- Optimisation surveillance

**Livrables** :
- Modèle clustering temporel
- Table : `vessel_temporal_clusters`
- Visualisations patterns
- Heatmaps activité
- Calendriers opération

---

### 8.1.5 Hierarchical clustering par type de navire

**Objectif** : Taxonomie hiérarchique basée caractéristiques

**Fonctionnalités** :
- Clustering hiérarchique navires
- Dendrogramme visualisation
- Multi-niveau granularité
- Identification sous-groupes
- Validation vessel_type déclaré

**Technologies** :
- **scikit-learn** : AgglomerativeClustering
- **scipy** : dendrogram, linkage
- **Linkage methods** : ward, average, complete
- **Distance metrics** : euclidean, manhattan, cosine
- **Cut tree** : fcluster, inconsistency

**Features navire** :
1. **Physiques** :
   - Length, width, draft
   - Tonnage (si disponible)
   - Ratio L/W

2. **Comportementales** :
   - Vitesse moyenne, max
   - Tortuosité trajectoires
   - Zones fréquentées

3. **Opérationnelles** :
   - Temps mer vs port
   - Fréquence voyages
   - Distance moyenne voyage

4. **Déclaratives** :
   - vessel_type (one-hot)
   - Pavillon (encodé)

**Linkage methods** :
- **Ward** : minimise variance (recommandé)
- **Average** : moyenne distances inter-cluster
- **Complete** : max distance (compact clusters)
- **Single** : min distance (chaînes)

**Détermination hauteur cut** :
- Inconsistency coefficient
- Cophenetic correlation
- Gap statistic
- Domain validation

**Analyse hiérarchie** :
- Niveau 1 : Super-catégories (Commercial, Pleasure, Service)
- Niveau 2 : vessel_group actuel
- Niveau 3 : Sous-types opérationnels
- Feuilles : Navires individuels

**Validation** :
- Concordance avec vessel_type
- Homogénéité clusters
- Pureté taxonomique
- Stabilité dendrogramme (bootstrap)

**Applications** :
- Validation types déclarés
- Détection erreurs classification
- Recommandation type navire
- Raffinement taxonomie AIS

**Livrables** :
- Dendrogramme interactif
- Table : `vessel_hierarchical_clusters`
- Taxonomie enrichie
- Mapping type_déclaré → type_inféré
- Rapport discordances

---

## 8.2 Détection d'Anomalies (Unsupervised)

### 8.2.1 Isolation Forest sur features de navigation

**Objectif** : Détection anomalies multi-dimensionnelles automatique

**Fonctionnalités** :
- Détection outliers positions/vitesse/cap
- Scoring anomalie (0-1)
- Identitification comportements atypiques
- Pas besoin labels (unsupervised)
- Robuste aux imbalanced data

**Technologies** :
- **scikit-learn** : IsolationForest
- **Contamination** : proportion anomalies (0.01-0.1)
- **n_estimators** : nombre arbres (100-500)
- **max_samples** : taille sous-échantillons
- **Random state** : reproductibilité

**Features anomalies** :
1. **Navigation** :
   - SOG (vitesse)
   - COG (cap)
   - Delta SOG (accélération)
   - Delta COG (changement cap)

2. **Spatiales** :
   - Distance côte
   - Distance port proche
   - Zone inhabituelle pour type

3. **Temporelles** :
   - Durée gap AIS
   - Heure jour (nuit suspect)
   - Fréquence positions

4. **Comportementales** :
   - Tortuosité trajectoire
   - Ratio arrêt/mouvement
   - Cohérence type vs comportement

**Preprocessing** :
- Normalisation features (StandardScaler)
- Gestion valeurs manquantes (imputation)
- Feature selection (importance)
- Filtrage bruit extrême

**Paramètres** :
- **contamination** : 0.05 (5% anomalies attendues)
- **n_estimators** : 200 (compromise speed/accuracy)
- **max_samples** : 'auto' ou 256
- **bootstrap** : True (variance reduction)

**Interprétation scores** :
- Score < -0.5 : Très anormal (critical)
- -0.5 < Score < 0 : Anormal (warning)
- Score ≥ 0 : Normal
- Seuil ajustable selon tolérance

**Post-processing** :
- Agrégation par navire (% positions anormales)
- Filtrage faux positifs (règles métier)
- Enrichissement contexte (météo, zones)
- Priorisation investigations

**Validation** :
- Inspection manuelle top anomalies
- Concordance alertes Phase 6
- Precision/Recall sur subset labellé
- Feedback loop amélioration

**Livrables** :
- Modèle Isolation Forest
- Table : `anomaly_scores_isolation_forest`
- Dashboard anomalies détectées
- Règles interprétation scores
- Rapport top 100 anomalies

---

### 8.2.2 One-Class SVM pour comportements normaux

**Objectif** : Apprendre frontière comportement normal, détecter déviations

**Fonctionnalités** :
- Modélisation région normalité
- Détection outliers hors région
- Support pour données haute dimension
- Kernel trick pour non-linéarité
- Sensible à scaling

**Technologies** :
- **scikit-learn** : OneClassSVM
- **Kernel** : RBF (radial basis function)
- **nu** : upper bound fraction outliers
- **gamma** : influence samples (kernel coefficient)
- **Optimization** : Sequential Minimal Optimization (SMO)

**Features normalité** :
- Identiques Isolation Forest
- Focus comportements type navire
- Features normalisées obligatoire (SVM sensitive)

**Paramètres clés** :
- **kernel** : 'rbf' (non-linéaire)
- **nu** : 0.05 (5% outliers max)
- **gamma** : 'scale' ou 'auto'
- Tuning via grid search validation

**Stratégie** :
1. **Global model** : tous navires
2. **Per-type models** : un SVM par vessel_type
3. **Ensemble** : vote majoritaire

**Training** :
- Uniquement données "normales" (filtrées)
- Exclusion anomalies connues
- Balance classes si applicable
- Cross-validation temporelle

**Prédiction** :
- Score décision : distance à hyperplan
- Signe : +1 (normal), -1 (outlier)
- Distance normalité utilisable comme score

**Avantages vs Isolation Forest** :
- Meilleur haute dimension
- Frontière décision plus flexible (kernel)
- Théorie mathématique solide

**Inconvénients** :
- Plus lent (scaling O(n²) à O(n³))
- Sensible paramètres (nu, gamma)
- Nécessite normalisation stricte

**Comparaison méthodes** :
- IF : plus rapide, moins paramètres
- OCSVM : plus précis, flexible frontière
- Usage : IF pour screening, OCSVM pour confirmation

**Livrables** :
- Modèle One-Class SVM par type
- Table : `anomaly_scores_ocsvm`
- Comparaison IF vs OCSVM
- Hyperplan visualisation (PCA)
- Tuning parameters documentation

---

### 8.2.3 Autoencoder pour patterns de trajectoires

**Objectif** : Reconstruction error comme mesure anormalité

**Fonctionnalités** :
- Apprentissage représentation compressée trajectoires
- Reconstruction trajectoires normales
- Erreur reconstruction = anomalie
- Capture patterns complexes
- Dimensionality reduction implicite

**Technologies** :
- **TensorFlow/Keras** ou **PyTorch**
- **Architecture** : Encoder-Decoder
- **Activation** : ReLU, tanh
- **Loss** : MSE (Mean Squared Error)
- **Optimizer** : Adam

**Préparation trajectoires** :
- Séquences lat/lon fixée longueur (padding/truncate)
- Normalisation (MinMaxScaler [0,1])
- Fenêtre glissante (sliding window)
- Augmentation données (rotation, translation)

**Architecture Autoencoder** :

```
Input: [batch, sequence_length, 2] (lat, lon)

Encoder:
  - Dense(128) + ReLU
  - Dense(64) + ReLU
  - Dense(32) + ReLU (bottleneck/latent space)

Decoder:
  - Dense(64) + ReLU
  - Dense(128) + ReLU
  - Dense(sequence_length * 2) + linear (reconstruction)

Output: [batch, sequence_length, 2]
```

**Training** :
- Uniquement trajectoires normales
- Loss: MSE entre input et reconstruction
- Epochs: 50-100
- Batch size: 32-128
- Early stopping (validation loss)
- Learning rate: 0.001

**Détection anomalies** :
- Reconstruction error par trajectoire
- Seuil = mean + k*std (k=2 ou 3)
- Erreur > seuil → anomalie
- Visualisation trajectoire originale vs reconstruite

**Reconstruction error** :
```
error = mean(|input - output|²)
```

**Avantages** :
- Capture patterns séquentiels
- Pas besoin features engineerées
- Apprentissage représentation latente
- Visualisation embedding (t-SNE)

**Inconvénients** :
- Plus complexe (deep learning)
- Nécessite GPU (optionnel mais recommandé)
- Plus de données nécessaires
- Hyperparamètres à tuner

**Variantes** :
- **Variational Autoencoder (VAE)** : distribution latente
- **LSTM Autoencoder** : séquences variable
- **Convolutional AE** : patterns spatiaux

**Livrables** :
- Modèle Autoencoder (HDF5/PTH)
- Table : `anomaly_scores_autoencoder`
- Visualisation latent space
- Exemples reconstructions
- Seuil anomalie justifié

---

### 8.2.4 LOF (Local Outlier Factor) sur positions

**Objectif** : Détection anomalies basée densité locale

**Fonctionnalités** :
- Détection outliers dans zones faible densité
- Comparaison densité locale vs voisins
- Adaptatif (densités variables)
- Pas besoin contamination pré-définie
- Scores interprétables (LOF score)

**Technologies** :
- **scikit-learn** : LocalOutlierFactor
- **n_neighbors** : nombre voisins (10-50)
- **metric** : 'haversine' pour lat/lon
- **algorithm** : 'ball_tree' ou 'kd_tree'
- **novelty** : False (outlier detection) ou True (novelty detection)

**Principe LOF** :
1. Calculer k-distance (distance au k-ème voisin)
2. Calculer reachability distance
3. Calculer Local Reachability Density (LRD)
4. Calculer LOF = LRD(voisins) / LRD(point)
5. LOF ≈ 1 : normal, LOF >> 1 : outlier

**Features** :
- Lat/lon (radians pour haversine)
- Optionnel : SOG, COG comme dimensions

**Paramètres** :
- **n_neighbors** : 20 (default 20)
- **contamination** : 'auto' ou fraction
- **metric** : 'haversine'
- **novelty** : False pour batch

**Applications** :
- Positions isolées géographiquement
- Navires hors routes habituelles
- Détection erreurs GPS (sauts)
- Complémentaire Isolation Forest

**LOF score interprétation** :
- LOF < 1.0 : Inlier (zone dense)
- 1.0 ≤ LOF < 1.5 : Normal
- 1.5 ≤ LOF < 2.0 : Suspect
- LOF ≥ 2.0 : Outlier (zone peu dense)

**Avantages** :
- Détecte anomalies dans clusters (local)
- Pas d'hypothèse distribution
- Scores continus

**Inconvénients** :
- Sensible n_neighbors
- Coûteux calculs (O(n²))
- Difficile haute dimension

**Optimisation** :
- Sous-échantillonnage spatial
- Approximation (sklearn.neighbors.NearestNeighbors)
- Batch processing par région

**Livrables** :
- Scores LOF par position
- Table : `anomaly_scores_lof`
- Carte anomalies LOF
- Comparaison densités locales
- Top outliers investigation

---

### 8.2.5 Détecter navires avec comportement atypique

**Objectif** : Agrégation anomalies pour profiling navires suspects

**Fonctionnalités** :
- Fusion scores multiples méthodes
- Profil anormalité par navire
- Ranking navires suspects
- Historique comportement
- Alertes multi-critères

**Technologies** :
- **Ensemble anomaly detection**
- **Voting** : majorité méthodes
- **Weighted average** : pondération scores
- **Stacking** : meta-classifier
- **SQL** : agrégations par vessel_id

**Agrégation scores** :

**Méthode 1: Vote majoritaire**
```
anomaly_count = sum([IF, OCSVM, AE, LOF] > threshold)
if anomaly_count >= 2:
    vessel_anomalous = True
```

**Méthode 2: Moyenne pondérée**
```
score_final = w1*score_IF + w2*score_OCSVM + w3*score_AE + w4*score_LOF
weights: [0.3, 0.2, 0.3, 0.2] (empirique ou learned)
```

**Méthode 3: Min/Max/Median**
```
score_conservative = min(scores)  # Strict
score_aggressive = max(scores)    # Sensible
score_balanced = median(scores)   # Équilibré
```

**Profil navire** :
- **Anomaly frequency** : % positions anormales
- **Anomaly severity** : score moyen
- **Anomaly types** : spatial, temporel, comportemental
- **Consistency** : agreement entre méthodes
- **Trend** : augmentation dans temps

**Features profil** :
- Nombre positions totales
- Nombre positions anormales
- Ratio anomalies (%)
- Score anomalie moyen
- Méthodes concordantes
- Zones anomalies
- Périodes anomalies

**Ranking critères** :
1. Ratio anomalies élevé (> 20%)
2. Score moyen élevé
3. Concordance méthodes (3+/4)
4. Persistance temporelle
5. Zones sensibles impliquées

**Catégorisation** :
- **Très suspect** : ratio > 30%, score > 0.8
- **Suspect** : ratio > 15%, score > 0.6
- **Attention** : ratio > 5%, score > 0.4
- **Normal** : ratio < 5%

**Validation** :
- Investigation manuelle top 50
- Corrélation alertes Phase 6
- Feedback experts domaine
- False positive analysis

**Actions** :
- Alertes automatiques
- Priorisation surveillance
- Investigation approfondie
- Enrichissement blacklist

**Livrables** :
- Table : `vessel_anomaly_profiles`
- Ranking navires suspects (CSV)
- Dashboard surveillance
- Rapports hebdomadaires top anomalies
- Règles scoring documentées

---

## 8.3 Classification Simple

### 8.3.1 Prédire type de navire depuis comportement

**Objectif** : Validation/correction type déclaré via ML

**Fonctionnalités** :
- Classification multi-classe types navires
- Features comportementales uniquement
- Validation cohérence type déclaré
- Correction types erronés
- Confidence scores prédictions

**Technologies** :
- **scikit-learn** : RandomForestClassifier, GradientBoostingClassifier
- **XGBoost** : XGBClassifier
- **LightGBM** : LGBMClassifier
- **Metrics** : accuracy, precision, recall, F1, confusion matrix
- **Imbalanced** : SMOTE, class_weight

**Features prédictives** :
1. **Vitesse** :
   - SOG moyenne, médiane, std, max
   - Percentiles (25, 50, 75, 95)
   - Temps SOG < 1 nœud

2. **Navigation** :
   - COG std (directionnalité)
   - Tortuosité trajectoires
   - Distance moyenne legs
   - Ratio lignes droites/courbes

3. **Spatiale** :
   - Distance côte moyenne
   - Distance ports moyenne
   - Types zones fréquentées
   - Bounding box area

4. **Temporelle** :
   - Durée voyages moyenne
   - Ratio mer/port
   - Patterns horaires (features)
   - Fréquence activité

5. **Dimensionnelle** :
   - Length, width, draft
   - Ratio L/W

**Target classes** :
- Vessel_group (10-15 classes principales)
- Filtrage classes rares (< 100 samples)
- Groupement types similaires si besoin

**Preprocessing** :
- Feature scaling (StandardScaler)
- Imputation missing (median/mode)
- Feature engineering (ratios, interactions)
- Train/test split : 80/20 stratifié

**Modèles** :

**1. Random Forest**
- n_estimators: 200-500
- max_depth: None ou 20
- class_weight: 'balanced'
- Avantage: interprétable, robuste

**2. XGBoost**
- n_estimators: 200
- learning_rate: 0.1
- max_depth: 6
- Avantage: meilleure performance

**3. LightGBM**
- Plus rapide XGBoost
- Gestion catégories native

**Gestion imbalance** :
- Class weights automatiques
- SMOTE oversampling minoritaires
- Stratified sampling
- Evaluation weighted metrics

**Evaluation** :
- Accuracy globale
- Precision/Recall/F1 par classe
- Confusion matrix
- Classification report
- Cross-validation 5-fold

**Feature importance** :
- SHAP values (explicabilité)
- Permutation importance
- Ranking features critiques

**Applications** :
- Détection erreurs type déclaré
- Enrichissement type manquant
- Validation cohérence flotte
- Détection fraude identité

**Livrables** :
- Modèle classifier type navire
- Confusion matrix
- Feature importance plot
- Table : `predicted_vessel_types`
- Rapport incohérences type
- API prédiction nouveau navire

---

### 8.3.2 Classifier statut navigation depuis vitesse/cap

**Objectif** : Prédire vessel_status depuis features navigation

**Fonctionnalités** :
- Classification statut (0-15)
- Features simples (SOG, COG, distance port)
- Validation statut déclaré
- Imputation statut manquant
- Real-time classification

**Technologies** :
- **scikit-learn** : LogisticRegression, DecisionTreeClassifier, RandomForest
- **Multiclass** : one-vs-rest ou softmax
- **Metrics** : accuracy, macro F1
- **Fast inference** : modèle léger (Decision Tree)

**Features prédictives** :
- **SOG** : vitesse actuelle
- **Delta SOG** : variation vitesse
- **COG** : cap actuel
- **Delta COG** : changement cap
- **Distance port** : proximité
- **Zone type** : port/mer/côte
- **Durée position** : temps écoulé dernier mouvement

**Target statuts principaux** :
- 0: Under way using engine
- 1: At anchor
- 2: Not under command
- 3: Restricted maneuverability
- 5: Moored
- 7: Engaged in fishing
- 8: Under way sailing
- 15: Default/Not defined

**Règles métier** (baseline) :
```
if SOG < 0.5 and distance_port < 2nm:
    status = "Moored" (5)
elif SOG < 0.5 and distance_port > 2nm:
    status = "At anchor" (1)
elif SOG > 1 and vessel_type == Fishing:
    if tortuosity > threshold:
        status = "Engaged in fishing" (7)
    else:
        status = "Under way" (0)
elif SOG > 1:
    status = "Under way" (0)
```

**ML Approach** :
- Decision Tree pour interprétabilité
- Random Forest pour performance
- Comparaison vs règles métier

**Training** :
- Données avec statut déclaré valide
- Balance classes (under-sampling majoritaire)
- Validation croisée

**Evaluation** :
- Accuracy par statut
- Confusion matrix
- Comparaison règles vs ML
- Agreement rate avec déclaré

**Applications** :
- Imputation statut manquant (80% positions)
- Validation statut incohérent
- Monitoring conformité déclarations
- Détection manipulations statut

**Livrables** :
- Modèle classifier statut
- Decision tree visualisation
- Table : `predicted_vessel_status`
- Règles métier codifiées
- Comparatif règles/ML

---

### 8.3.3 Prédire zone géographique depuis historique

**Objectif** : Classification zone actuelle/future depuis patterns

**Fonctionnalités** :
- Prédire zone présence navire
- Features historique déplacements
- Patterns zones fréquentées
- Prévision zone prochaine
- Probabilités multi-zones

**Technologies** :
- **scikit-learn** : RandomForestClassifier, KNeighborsClassifier
- **Naive Bayes** : MultinomialNB (probabilités)
- **Markov Chains** : transitions zones
- **Features** : spatial + temporel

**Définition zones** :
- Grille spatiale (Phase 2)
- ROI prédéfinies
- Zones portuaires
- Zones pêche
- Zones à risque

**Features** :
1. **Position actuelle** :
   - Lat/lon (discrétisé ou embedding)
   - Zone actuelle

2. **Historique** :
   - Zones visitées dernières 24h
   - Fréquence visite par zone
   - Temps passé par zone
   - Séquence zones (n-grams)

3. **Temporel** :
   - Heure jour
   - Jour semaine
   - Saison

4. **Navire** :
   - Type navire
   - Comportement patterns

**Approches** :

**1. Classification directe**
- Target: zone_id (classification multi-classe)
- Features: historique + contexte
- Model: Random Forest

**2. Markov Chain**
- États = zones
- Transitions = probabilités zone_i → zone_j
- Prédiction = argmax(P(zone_next | zone_current, historique))

**3. Sequential (preparatory for LSTM)**
- Séquences zones visitées
- Prédire prochaine zone
- Approche n-gram ou Naive Bayes

**Matrice transition zones** :
```
        Zone_A  Zone_B  Zone_C
Zone_A    0.7     0.2     0.1
Zone_B    0.3     0.5     0.2
Zone_C    0.1     0.3     0.6
```

**Evaluation** :
- Accuracy prédiction zone
- Top-3 accuracy (3 zones probables)
- Precision par zone
- Temporal consistency

**Applications** :
- Prévision zones surveillance
- Allocation ressources patrouilles
- Détection déviations route
- Estimation congestion zones

**Livrables** :
- Modèle prédiction zone
- Matrice transition zones
- Probabilités par navire/zone
- Carte prédictions
- Dashboard zones futures

---

### 8.3.4 Classifier "en route" vs "à quai" vs "mouillage"

**Objectif** : Classification ternaire état opérationnel

**Fonctionnalités** :
- Classification simple 3 états
- Features simples robustes
- Real-time classification
- Haute accuracy attendue (> 95%)
- Validation croisée statut déclaré

**Technologies** :
- **scikit-learn** : LogisticRegression (baseline), RandomForest
- **Binary first** : moving vs stationary → then refine
- **Threshold-based** : règles simples performantes
- **Ensemble** : vote modèles

**Classes** :
1. **En route** : navire en déplacement
2. **À quai** : amarré port/terminal
3. **Mouillage** : ancré en mer

**Features discriminantes** :
- **SOG** : clé (> 1 nœud → en route)
- **Distance port** : < 1 km → à quai
- **Durée stationnaire** : temps SOG < 0.5
- **Zone** : port/mer
- **COG variance** : élevée → mouillage (dérive)

**Règles simples (baseline 95%+)** :
```python
if SOG > 1:
    return "en_route"
elif distance_port < 1000 and SOG < 0.5:
    return "a_quai"
elif distance_port > 1000 and SOG < 0.5:
    return "mouillage"
```

**ML approach** :
- Logistic Regression (3 classes)
- Random Forest (confirmation)
- Features: SOG, distance_port, duration, zone, COG_std

**Refinements** :
- Seuils adaptatifs par type navire
- Contexte temporel (transitions)
- Validation cohérence séquentielle
- Lissage prédictions (filtrage)

**Challenges** :
- Manœuvres portuaires (ambiguës)
- Mouillage temporaire en route
- Drift vs vraie navigation
- Tug assistance (vitesse faible)

**Evaluation** :
- Confusion matrix 3x3
- Precision/Recall par classe
- Agreement avec statut déclaré
- Temporal stability (pas flip-flop)

**Applications** :
- Statistiques temps opération
- Facturation services portuaires
- Monitoring activité flotte
- Input pour analyses avancées

**Livrables** :
- Classifier 3 états
- Règles seuils par type
- Table : `operational_state`
- Validation temporelle
- API classification temps réel

---

### 8.3.5 Random Forest pour classification multi-classe

**Objectif** : Modèle ensembliste robuste classifications complexes

**Fonctionnalités** :
- Ensemble decision trees
- Robuste overfitting
- Gestion features hétérogènes
- Feature importance natif
- Parallélisable (scalable)

**Technologies** :
- **scikit-learn** : RandomForestClassifier
- **n_estimators** : 100-500 arbres
- **max_depth** : None ou limité
- **class_weight** : 'balanced' pour imbalance
- **n_jobs** : -1 (all cores)

**Hyperparamètres tuning** :
- **n_estimators** : [100, 200, 500] (plus = mieux mais lent)
- **max_depth** : [None, 10, 20, 30] (None = full)
- **min_samples_split** : [2, 5, 10] (split control)
- **min_samples_leaf** : [1, 2, 4] (leaf size)
- **max_features** : ['sqrt', 'log2', None] (split features)
- **bootstrap** : True (recommended)
- **class_weight** : 'balanced' (imbalance)

**Grid Search** :
```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'n_estimators': [200, 500],
    'max_depth': [None, 20],
    'min_samples_split': [2, 5],
    'max_features': ['sqrt', 'log2']
}

grid_search = GridSearchCV(
    RandomForestClassifier(random_state=42),
    param_grid,
    cv=5,
    scoring='f1_weighted',
    n_jobs=-1
)
```

**Applications RF** :

**1. Type navire prédiction**
- Multi-class (10+ types)
- Features: comportement + dimensions
- Imbalance: class_weight

**2. Statut navigation**
- Multi-class (8 statuts principaux)
- Features: SOG, COG, distance
- Rapide inference

**3. Zone prédiction**
- Multi-class (50+ zones)
- Features: position + historique
- Probabilités zones

**4. Anomalie vs Normal**
- Binary classification
- Features: tous scores anomalies
- Métamodèle sur détecteurs

**Feature importance** :
```python
importances = rf_model.feature_importances_
feature_names = X.columns
sorted_idx = importances.argsort()[::-1]

# Top 10 features
for i in range(10):
    print(f"{feature_names[sorted_idx[i]]}: {importances[sorted_idx[i]]:.4f}")
```

**Avantages RF** :
- Peu sensible hyperparamètres (robuste)
- Gère features non-linéaires
- Pas besoin normalisation
- Gère missing values (sklearn)
- Interprétable (feature importance)
- OOB error estimation

**Inconvénients** :
- Mémoire (stockage arbres)
- Inference plus lente (vs Logistic Regression)
- Peut over-smooth (average arbres)

**Optimization** :
- Réduire n_estimators si latence critique
- Limiter max_depth pour speed
- Feature selection pré-RF
- Compression modèle (pruning)

**Comparison autres** :
- **XGBoost** : meilleur accuracy, plus complexe
- **Logistic Regression** : plus simple, linéaire
- **SVM** : théorique, lent grande data
- **KNN** : lazy, mémoire

**Livrables** :
- Modèle RF optimisé (pickle)
- Feature importances rapport
- Hyperparamètres optimaux
- Comparaison modèles benchmark
- Guidelines utilisation RF

---

## 📊 Livrables Phase 8

### Modèles ML
```
models/
├── kmeans_positions.pkl
├── dbscan_routes.pkl
├── behavior_clustering.pkl
├── temporal_clustering.pkl
├── hierarchical_vessels.pkl
├── isolation_forest.pkl
├── onesvm_anomaly.pkl
├── autoencoder_trajectories.h5
├── lof_detector.pkl
├── vessel_type_classifier.pkl
├── status_classifier.pkl
├── zone_predictor.pkl
├── operational_state_classifier.pkl
└── random_forest_ensemble.pkl
```

### Tables PostgreSQL
```sql
kmeans_position_clusters
dbscan_maritime_routes
vessel_behavior_clusters
vessel_temporal_clusters
vessel_hierarchical_clusters
anomaly_scores_isolation_forest
anomaly_scores_ocsvm
anomaly_scores_autoencoder
anomaly_scores_lof
vessel_anomaly_profiles
predicted_vessel_types
predicted_vessel_status
predicted_zones
operational_state
model_performance_metrics
```

### Notebooks Analyse
```
notebooks/
├── 8.1_clustering_analysis.ipynb
├── 8.2_anomaly_detection_comparison.ipynb
├── 8.3_classification_models.ipynb
├── model_evaluation.ipynb
├── feature_importance.ipynb
└── hyperparameter_tuning.ipynb
```

### Documentation
```
docs/
├── ml_models_documentation.md
├── feature_engineering_guide.md
├── model_selection_rationale.md
├── hyperparameters_tuning.md
├── performance_benchmarks.md
└── ml_pipeline_architecture.md
```

### Scripts
```
ml/
├── clustering/
│   ├── kmeans_clustering.py
│   ├── dbscan_routes.py
│   └── behavior_clustering.py
├── anomaly/
│   ├── isolation_forest.py
│   ├── onesvm.py
│   ├── autoencoder.py
│   └── lof_detector.py
├── classification/
│   ├── vessel_type_classifier.py
│   ├── status_classifier.py
│   └── zone_predictor.py
├── utils/
│   ├── preprocessing.py
│   ├── feature_engineering.py
│   └── evaluation.py
└── pipeline/
    ├── train_pipeline.py
    ├── inference_pipeline.py
    └── model_registry.py
```

### Rapports
```
reports/
├── clustering_results.pdf
├── anomaly_detection_report.pdf
├── classification_performance.pdf
├── top_anomalous_vessels.csv
├── feature_importance_ranking.csv
└── model_comparison_metrics.xlsx
```

---

## ✅ Critères de Validation Phase 8

**Phase 8 considérée terminée si** :

1. ✅ **Clustering opérationnel**
   - K-Means et DBSCAN déployés
   - Routes maritimes extraites
   - Clusters comportements identifiés

2. ✅ **Détection anomalies fonctionnelle**
   - Minimum 3 détecteurs (IF, OCSVM, LOF)
   - Scores anomalies calculés
   - Top navires suspects identifiés

3. ✅ **Classification précise**
   - Modèles type navire (accuracy > 85%)
   - Classifier statut (accuracy > 90%)
   - État opérationnel (accuracy > 95%)

4. ✅ **Modèles évalués**
   - Métriques complètes (Precision/Recall/F1)
   - Confusion matrices
   - Feature importance analysée
   - Cross-validation réalisée

5. ✅ **Pipeline ML complet**
   - Preprocessing automatisé
   - Training pipeline
   - Inference pipeline
   - Model versioning (MLflow)

6. ✅ **Documentation livrée**
   - Notebooks reproductibles
   - Documentation modèles
   - Guidelines utilisation
   - Performance benchmarks

7. ✅ **Intégration système**
   - Modèles sauvegardés (pickle/h5)
   - Tables résultats peuplées
   - API inference disponible
   - Monitoring déployé

---

## 🚀 Prochaines Étapes

Après Phase 8 :
- **Phase 9** : Deep Learning - Trajectoires (LSTM, Transformers)
- **Phase 10** : Prédiction et Forecast (ETA, destination, trafic)
- **Phase 11** : Reinforcement Learning (optimisation routes)
- **Phase 12** : Production ML Ops (monitoring, retraining)

---

**Fin SPECS_PHASE_08.md**

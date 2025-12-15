# Checklist Features - Projet AIS Analytics

> **Base de données disponible :** PostgreSQL + PostGIS
> - Tables: `vessel`, `vessel_type`, `position_vessel`, `vessel_status`, `users`, `user_vessel`, `file_uploads`, `request_property`
> - Données principales: MMSI, positions (lat/lon), SOG, COG, heading, status, timestamps, dimensions navires

---

## 📊 PHASE 1 : DATA QUALITY & PREPROCESSING

### 1.1 Nettoyage des Données
- [x] Détecter et supprimer les positions GPS aberrantes (latitude/longitude invalides) ✅ `transform_general_ais.py::remove_rows_with_wrong_format`
- [x] Identifier et traiter les outliers de vitesse (SOG > vitesse max par type) ✅ `transform_vessel_position.py::detect_vessel_incoherent_positions` (max 130 km/h)
- [x] Détecter les valeurs négatives ou nulles incorrectes ✅ `transform_general_ais.py::remove_rows_with_wrong_format`
- [x] Gérer les positions terrestres (navires sur terre) ✅ Notebook `terrestrial_positions_detection.ipynb`
- [x] Nettoyer les heading invalides (> 360°) ✅ `transform_general_ais.py::remove_rows_with_wrong_format` + `transform_ais_cleanup.py`
- [x] Normaliser les données de cap (COG 0-360°) ✅ `transform_general_ais.py::normalize_ais`

### 1.2 Gestion des Gaps Temporels
- [ ] Identifier les gaps AIS par navire (> 4h sans signal)
- [ ] Calculer statistiques des gaps (durée moyenne, fréquence)
- [ ] Détecter les désactivations suspectes d'AIS
- [ ] Interpolation linéaire pour petits gaps (< 1h)
- [ ] Flaguer les trajectoires avec gaps importants

### 1.3 Feature Engineering de Base
- [x] Calculer delta_time entre positions successives ✅ `transform_vessel_position.py::detect_vessel_incoherent_positions`
- [x] Calculer distance parcourue (haversine distance) ✅ `transform_vessel_position.py::haversine_km`
- [x] Calculer vitesse dérivée (distance/temps) ✅ `transform_vessel_position.py::speed_kmh`
- [ ] Calculer accélération (delta SOG)
- [ ] Calculer changement de cap (delta COG)
- [ ] Calculer temps total en mer par navire
- [ ] Créer flag "navire en mouvement" (SOG > 1 nœud)

### 1.4 Validation et Indexation

- [x] Vérifier intégrité référentielle (vessel_id, status_id) ✅ `load_positions_db.py::load_position_db`
- [x] Optimiser index PostGIS sur geom ✅ Migration `V8__new_index_vessel_position.sql`
- [x] Créer index composite (vessel_id, base_date_time) ✅ Migration SQL
- [x] Créer index sur vessel_type_id ✅ Migration SQL
- [x] Valider cohérence temporelle (ordre timestamps) ✅ `transform_vessel_delta.py`

### 1.5 Gestion des Doublons et Duplications

- [x] Détecter et supprimer les doublons (même MMSI, même timestamp) ✅ `transform_vessel_duplication.py::clean_vessel_duplication`
- [x] Filtrer les petits mouvements (< 0.1km) ✅ `transform_vessel_position.py::filter_small_movements`
- [x] Downsampling intelligent (garder première et dernière position par groupe) ✅ `transform_ais_downsampling.py::downsample_ais`

### 1.6 ETL & Pipeline

- [x] Extract: Charger données depuis fichier CSV ✅ `extract_ais.py::extract_data_from_file`
- [x] Extract: Downloader automatique AIS ✅ `AISDownloader.py`
- [x] Transform: Delta detection pour nouveaux navires ✅ `transform_vessel_delta.py::transform_vessel_delta`
- [x] Load: Insertion bulk des vessels ✅ `load_vessel_db.py::load_vessel_to_db`
- [x] Load: Insertion bulk des positions ✅ `load_positions_db.py::load_position_db`
- [x] Pipeline: Système de registry et runner ✅ `registry.py`, `runner.py`, `loader.py`

---

## 🗺️ PHASE 2 : ANALYSE SPATIALE

### 2.1 Zones Géographiques
- [ ] Identifier bounding box global des données
- [ ] Créer grille spatiale (hexagones ou carrés)
- [ ] Calculer densité de trafic par cellule
- [ ] Identifier zones de forte activité (hotspots)
- [ ] Créer zones d'intérêt géographiques (ROI)

### 2.2 Proximité Portuaire
- [ ] Définir positions approximatives des ports principaux
- [ ] Calculer distance au port le plus proche par position
- [ ] Identifier entrées/sorties de zones portuaires
- [ ] Calculer temps passé en zone portuaire par navire
- [ ] Détecter navires à quai (vitesse nulle en zone port)

### 2.3 Analyse de Trajectoires

- [x] Extraire trajectoires complètes par MMSI ✅ Notebook `trajectoire_bateau.ipynb`
- [ ] Calculer longueur totale des trajectoires
- [ ] Identifier points de départ et arrivée
- [ ] Détecter boucles et retours en arrière
- [ ] Calculer tortuosité des trajectoires

---

## 🚢 PHASE 3 : ANALYSE PAR TYPE DE NAVIRE

### 3.1 Segmentation par Groupe
- [ ] Statistiques par vessel_group (Cargo, Tanker, Passenger, etc.)
- [ ] Nombre de navires uniques par type
- [ ] Distribution des dimensions (length, width, draft) par type
- [ ] Vitesse moyenne par type de navire
- [ ] Distance moyenne parcourue par type

### 3.2 Comportements Spécifiques
- [ ] Identifier pattern de pêche (Fishing vessels)
- [ ] Identifier pattern de remorquage (Tug Tow)
- [ ] Identifier pattern de plaisance (Pleasure Craft)
- [ ] Identifier pattern de passagers (lignes régulières)
- [ ] Identifier pattern de cargo/tanker (routes commerciales)

### 3.3 Comparaisons Inter-Types
- [ ] Comparer vitesses moyennes entre types
- [ ] Comparer zones d'activité entre types
- [ ] Comparer durées de voyage entre types
- [ ] Identifier types avec plus de gaps AIS
- [ ] Analyser statut de navigation par type (vessel_status)

---

## 🛣️ PHASE 4 : EXTRACTION DE ROUTES MARITIMES

### 4.1 Clustering Spatial (DBSCAN/HDBSCAN)

- [x] Clustering global de toutes les positions ✅ Notebook `clustering_analysis.ipynb`
- [x] Clustering par type de navire ✅ Notebook `clustering_analysis.ipynb`
- [ ] Identifier corridors de trafic dense
- [ ] Calculer largeur m10oyenne des corridors
- [ ] Créer lignes centrales des routes

### 4.2 Routes Commerciales
- [ ] Extraire routes Cargo (70-79)
- [ ] Extraire routes Tanker (80-89)
- [ ] Identifier routes principales (> 100 passages)
- [ ] Calculer fréquence de passage par route
- [ ] Identifier heures de pointe par route

### 4.3 Routes Spécialisées
- [ ] Extraire routes de pêche (zone + retour port)
- [ ] Extraire routes de ferries/passenger
- [ ] Extraire routes de plaisance (côtières)
- [ ] Identifier routes saisonnières
- [ ] Créer carte des routes par catégorie

### 4.4 Points d'Intérêt
- [ ] Identifier points de croisement majeurs
- [ ] Identifier zones d'attente (ancrage)
- [ ] Identifier zones de transbordement
- [ ] Calculer temps moyen par segment de route
- [ ] Identifier goulots d'étranglement

---

## ⏱️ PHASE 5 : ANALYSE TEMPORELLE

### 5.1 Patterns Temporels
- [ ] Distribution horaire du trafic (0-24h)
- [ ] Distribution journalière (lundi-dimanche)
- [ ] Distribution mensuelle/saisonnière
- [ ] Identifier heures creuses et heures de pointe
- [ ] Détecter patterns week-end vs semaine

### 5.2 Séries Temporelles
- [ ] Nombre de navires actifs par jour
- [ ] Volume de positions enregistrées par jour
- [ ] Évolution du trafic dans le temps
- [ ] Détecter tendances (croissance/décroissance)
- [ ] Identifier événements anormaux (pics, creux)

### 5.3 Durées et Fréquences
- [ ] Calculer durée moyenne des voyages par type
- [ ] Calculer fréquence de passage par zone
- [ ] Identifier navires les plus actifs
- [ ] Calculer temps moyen entre deux voyages
- [ ] Analyser régularité des lignes régulières

---

## 🎯 PHASE 6 : DÉTECTION DE COMPORTEMENTS

### 6.1 Classification de Statuts
- [ ] Statistiques par vessel_status (0-15)
- [ ] Temps passé par statut par navire
- [ ] Transitions de statuts (mouillage → navigation)
- [ ] Identifier statuts anormaux par type de navire
- [ ] Corrélation statut vs vitesse/cap

### 6.2 Détection d'Événements
- [ ] Détecter arrêts prolongés en mer (> 2h)
- [ ] Détecter changements brusques de cap (> 90°)
- [ ] Détecter accélérations/décélérations rapides
- [ ] Détecter navigations en zigzag
- [ ] Identifier comportements de recherche (pêche)

### 6.3 Anomalies de Navigation
- [ ] Vitesse anormale pour le type de navire
- [ ] Cap constant sur longue distance (autopilote)
- [ ] Position statique avec statut "en mouvement"
- [ ] Trajectoires illogiques (retours arrière fréquents)
- [ ] Navires hors zones habituelles pour leur type

---

## 🤖 PHASE 7 : MACHINE LEARNING - NIVEAU 1

### 7.1 Clustering Non-Supervisé

- [x] K-Means sur positions géographiques ✅ Notebook `clustering_analysis.ipynb`
- [x] DBSCAN pour routes maritimes ✅ Notebook `clustering_analysis.ipynb`
- [ ] Clustering de comportements (SOG, COG patterns)
- [ ] Clustering temporel (patterns horaires)
- [ ] Hiérarchical clustering par type de navire

### 7.2 Détection d'Anomalies (Unsupervised)
- [ ] Isolation Forest sur features de navigation
- [ ] One-Class SVM pour comportements normaux
- [ ] Autoencoder pour patterns de trajectoires
- [ ] LOF (Local Outlier Factor) sur positions
- [ ] Détecter navires avec comportement atypique

### 7.3 Classification Simple
- [ ] Prédire type de navire depuis comportement
- [ ] Classifier statut de navigation depuis vitesse/cap
- [ ] Prédire zone géographique depuis historique
- [ ] Classifier "en route" vs "à quai" vs "mouillage"
- [ ] Random Forest pour classification multi-classe

---

## 🧠 PHASE 8 : DEEP LEARNING - TRAJECTOIRES

### 8.1 Préparation Données Séquentielles
- [ ] Créer séquences temporelles par MMSI
- [ ] Normaliser features (MinMaxScaler, StandardScaler)
- [ ] Padding/truncation séquences à longueur fixe
- [ ] Train/validation/test split temporel (80/10/10)
- [ ] Data augmentation (rotation, translation)

### 8.2 Modèles LSTM
- [ ] LSTM simple pour prédiction next position
- [ ] LSTM bidirectionnel pour analyse trajectoires
- [ ] Stacked LSTM pour patterns complexes
- [ ] LSTM avec attention pour focus zones
- [ ] Encoder-Decoder LSTM pour séquence complète

### 8.3 Modèles CNN
- [ ] CNN 1D sur séquences temporelles
- [ ] CNN pour classification de comportements
- [ ] CNN pour détection d'événements
- [ ] ResNet 1D pour patterns profonds
- [ ] CNN + LSTM hybride

### 8.4 Transformers
- [ ] Transformer pour prédiction de trajectoire
- [ ] Self-attention sur séquences de positions
- [ ] Multi-head attention temporelle
- [ ] Positional encoding pour timestamps
- [ ] BERT-like pour masked trajectory prediction

---

## 🔮 PHASE 9 : PRÉDICTION ET FORECAST

### 9.1 Prédiction de Position
- [ ] Prédire position à T+5min, T+30min, T+1h
- [ ] Prédire trajectoire complète (10 prochaines positions)
- [ ] Calculer intervalle de confiance des prédictions
- [ ] Prédire destination finale du voyage
- [ ] Prédire heure d'arrivée estimée (ETA)

### 9.2 Prédiction de Comportement
- [ ] Prédire prochain changement de statut
- [ ] Prédire probabilité d'arrêt en mer
- [ ] Prédire changement de route
- [ ] Prédire entrée en zone portuaire
- [ ] Prédire durée restante du voyage

### 9.3 Forecast Trafic
- [ ] Prédire trafic horaire à J+1
- [ ] Prédire densité de trafic par zone
- [ ] Prédire congestion portuaire
- [ ] Prédire volume de trafic hebdomadaire
- [ ] Forecast saisonnalité (mensuel)

---

## ⚠️ PHASE 10 : SÉCURITÉ MARITIME

### 10.1 Détection de Proximité
- [ ] Calculer distances entre navires proches (< 1nm)
- [ ] Identifier paires de navires en collision potentielle
- [ ] Calculer DCPA (Distance at Closest Point of Approach)
- [ ] Calculer TCPA (Time to Closest Point of Approach)
- [ ] Créer alertes de proximité en temps réel

### 10.2 Zones de Risque
- [ ] Identifier zones à forte densité (> N navires/km²)
- [ ] Identifier zones de croisement dangereuses
- [ ] Calculer risque par zone géographique
- [ ] Détecter navigations à contre-sens
- [ ] Mapper zones de collision historiques

### 10.3 Comportements Dangereux
- [ ] Détecter vitesse excessive en zone restreinte
- [ ] Détecter manœuvres dangereuses
- [ ] Identifier navires ne respectant pas corridors
- [ ] Détecter navigation erratique
- [ ] Scorer niveau de risque par navire

---

## 🌍 PHASE 11 : ANALYSE ENVIRONNEMENTALE

### 11.1 Estimation Émissions
- [ ] Modèle de consommation carburant par type
- [ ] Calculer émissions CO2 par navire
- [ ] Calculer émissions totales par zone
- [ ] Identifier navires les plus polluants
- [ ] Comparer émissions par type de navire

### 11.2 Efficacité Énergétique
- [ ] Calculer ratio distance/vitesse optimale
- [ ] Identifier navigations inefficaces
- [ ] Calculer score d'efficacité par navire
- [ ] Comparer efficacité intra-flotte
- [ ] Proposer routes optimisées (fuel-efficient)

### 11.3 Impact Environnemental
- [ ] Identifier passages en zones protégées
- [ ] Calculer temps passé en zones sensibles
- [ ] Analyser respect des vitesses réduites (baleines)
- [ ] Estimer pollution sonore sous-marine
- [ ] Mapper impact cumulatif par zone

---

## 📈 PHASE 12 : ANALYSE PORTUAIRE

### 12.1 Statistiques Portuaires
- [ ] Nombre de visites par port
- [ ] Durée moyenne au port par type de navire
- [ ] Temps d'attente avant entrée au port
- [ ] Taux d'occupation portuaire
- [ ] Identifier ports les plus fréquentés

### 12.2 Performance Portuaire
- [ ] Calculer turnaround time par port
- [ ] Identifier goulots d'étranglement
- [ ] Analyser efficacité des manœuvres portuaires
- [ ] Comparer performance entre ports
- [ ] Détecter congestion portuaire

### 12.3 Prédiction Portuaire
- [ ] Prédire arrivées de navires à J+1
- [ ] Prédire durée au port
- [ ] Prédire congestion future
- [ ] Optimiser allocation des quais
- [ ] Prédire demande de remorqueurs

---

## 🕵️ PHASE 13 : INTELLIGENCE MARITIME

### 13.1 Détection d'Activités Suspectes
- [ ] Identifier gaps AIS prolongés (> 8h)
- [ ] Détecter rencontres en mer (ship-to-ship)
- [ ] Identifier changements de trajectoire suspects
- [ ] Détecter loitering (zone stationnaire prolongée)
- [ ] Identifier navigations dans zones interdites

### 13.2 Analyse de Pêche IUU
- [ ] Identifier comportements de pêche (Fishing type)
- [ ] Détecter pêche dans zones protégées
- [ ] Identifier fishing vessels sans transpondeur actif
- [ ] Détecter transbordements illégaux
- [ ] Calculer temps de pêche vs temps au port

### 13.3 Tracking et Surveillance
- [ ] Créer profil comportemental par navire
- [ ] Détecter écarts au profil habituel
- [ ] Identifier navires changeant fréquemment d'identité
- [ ] Tracker flottes spécifiques (user_vessel)
- [ ] Générer alertes automatiques

---

## 🎨 PHASE 14 : VISUALISATION

### 14.1 Cartes Statiques
- [ ] Heatmap de densité de trafic
- [ ] Carte des routes maritimes par type
- [ ] Carte des zones de risque
- [ ] Carte des ports avec statistiques
- [ ] Carte des zones de pêche

### 14.2 Cartes Interactives
- [ ] Carte Folium avec layers par type
- [ ] Trajectoires animées (animation temporelle)
- [ ] Clusters interactifs (zoom adaptatif)
- [ ] Popups avec infos navire détaillées
- [ ] Filtres interactifs (date, type, zone)

### 14.3 Dashboards
- [ ] Dashboard trafic en temps réel
- [ ] Dashboard statistiques globales
- [ ] Dashboard par type de navire
- [ ] Dashboard sécurité maritime
- [ ] Dashboard environnemental

### 14.4 Graphiques Analytiques
- [ ] Timeline du trafic
- [ ] Distribution vitesses par type
- [ ] Diagrammes de flux (Sankey)
- [ ] Graphes de réseau (navires connectés)
- [ ] Matrices de corrélation

---

## 🔬 PHASE 15 : ANALYSES AVANCÉES

### 15.1 Graph Neural Networks (GNN)
- [ ] Construire graphe de navires (nœuds = navires)
- [ ] Définir arêtes (proximité spatiale/temporelle)
- [ ] GCN pour prédiction d'interactions
- [ ] Détection de communautés de navires
- [ ] Prédiction de congestion via GNN

### 15.2 Reinforcement Learning
- [ ] Environnement de navigation simulé
- [ ] Agent RL pour optimisation de route
- [ ] Reward function (fuel, temps, sécurité)
- [ ] Q-Learning pour décisions de navigation
- [ ] Policy gradient pour trajectoires optimales

### 15.3 Time Series Avancées
- [ ] Prophet pour forecast trafic saisonnier
- [ ] ARIMA/SARIMA pour prédictions court terme
- [ ] LSTM + Attention pour forecast multi-horizon
- [ ] Détection de changements (changepoint detection)
- [ ] Décomposition saisonnalité + trend

### 15.4 Ensemble Methods
- [ ] Stacking de modèles (LSTM + RF + XGBoost)
- [ ] Bagging pour réduction variance
- [ ] Boosting pour amélioration performance
- [ ] Voting classifier pour robustesse
- [ ] Meta-learning pour adaptation rapide

---

## 👥 PHASE 16 : FEATURES UTILISATEURS

### 16.1 Gestion des Utilisateurs (users, role)
- [ ] Dashboard personnalisé par utilisateur
- [ ] Favoris navires (user_vessel)
- [ ] Alertes personnalisées (email/SMS)
- [ ] Historique des recherches
- [ ] Préférences d'affichage

### 16.2 Propriété de Navires (user_vessel)
- [ ] Vue propriétaire (1 OWNER par vessel)
- [ ] Suivi de flotte pour propriétaires
- [ ] Statistiques de flotte
- [ ] Rapports automatiques pour OWNER
- [ ] Comparaison performance flotte

### 16.3 Gestion de Fichiers (file_uploads)
- [ ] Upload de nouvelles données AIS
- [ ] Historique des uploads par utilisateur
- [ ] Validation format fichiers
- [ ] Processing asynchrone des uploads
- [ ] Logs de traitement

### 16.4 Demandes de Propriété (request_property)
- [ ] Système de demande de propriété (MMSI)
- [ ] Validation des demandes (avec justificatifs)
- [ ] Workflow d'approbation
- [ ] Notifications de statut
- [ ] Historique des demandes

---

## 🚀 PHASE 17 : API & INTÉGRATION

### 17.1 API REST
- [ ] Endpoint GET /vessels (liste + filtres)
- [ ] Endpoint GET /vessel/{mmsi}/positions
- [ ] Endpoint GET /vessel/{mmsi}/trajectory
- [ ] Endpoint GET /routes (routes maritimes)
- [ ] Endpoint GET /statistics
- [ ] Endpoint POST /predict (prédictions)
- [ ] Endpoint GET /alerts (alertes sécurité)
- [ ] Authentification JWT
- [ ] Rate limiting
- [ ] Documentation Swagger/OpenAPI

### 17.2 WebSockets (Temps Réel)
- [ ] Stream positions en temps réel
- [ ] Notifications d'alertes live
- [ ] Mise à jour carte en temps réel
- [ ] Broadcast événements importants
- [ ] Room par zone géographique

### 17.3 Intégrations Externes
- [ ] API météo marine (conditions actuelles)
- [ ] API données portuaires
- [ ] Export vers formats standards (KML, GeoJSON)
- [ ] Intégration avec systèmes VTS
- [ ] Webhooks pour événements

---

## 📊 PHASE 18 : MONITORING & PRODUCTION

### 18.1 Métriques Système
- [ ] Latence des requêtes API
- [ ] Volume de données traitées
- [ ] Taux d'erreur
- [ ] Utilisation CPU/RAM
- [ ] Temps de réponse DB

### 18.2 Métriques Modèles ML
- [ ] Accuracy des prédictions en production
- [ ] Drift detection (data drift, concept drift)
- [ ] Latence d'inférence
- [ ] Distribution des prédictions
- [ ] Retraining automatique

### 18.3 Logs & Alertes
- [ ] Logs structurés (ELK stack)
- [ ] Alertes performance
- [ ] Alertes erreurs critiques
- [ ] Monitoring santé des services
- [ ] Dashboards Grafana

---

## 📚 PHASE 19 : DOCUMENTATION & TESTS

### 19.1 Documentation Technique
- [ ] Documentation API (Swagger)
- [ ] Documentation modèles ML (MLflow)
- [ ] Architecture système (diagrammes)
- [ ] Guide de déploiement
- [ ] Documentation base de données (schéma ER)

### 19.2 Tests
- [ ] Tests unitaires (pytest)
- [ ] Tests d'intégration (API)
- [ ] Tests de charge (locust)
- [ ] Tests de régression (ML)
- [ ] Tests end-to-end

### 19.3 Rapports
- [ ] Rapport d'analyse exploratoire (EDA)
- [ ] Rapport de performance modèles
- [ ] Rapport d'impact business
- [ ] Études de cas (success stories)
- [ ] Documentation utilisateur

---

## 🎯 PHASE 20 : OPTIMISATION & SCALABILITÉ

### 20.1 Optimisation Base de Données
- [ ] Partitioning table position_vessel (par date)
- [ ] Matérialized views pour agrégations
- [ ] Query optimization (EXPLAIN ANALYZE)
- [ ] Index adaptatifs
- [ ] Archivage données anciennes

### 20.2 Optimisation ML
- [ ] Quantization des modèles
- [ ] Pruning de réseaux de neurones
- [ ] Model compression
- [ ] Batch inference
- [ ] Caching des prédictions fréquentes

### 20.3 Infrastructure Scalable
- [ ] Containerization (Docker)
- [ ] Orchestration (Kubernetes)
- [ ] Load balancing
- [ ] Auto-scaling
- [ ] CDN pour assets statiques
- [ ] Database replication (read replicas)

---

## ✅ QUICK WINS (Priorité Haute)

### À Implémenter en Premier
- [x] Pipeline ETL fonctionnel (déjà fait)
- [ ] Statistiques descriptives de base
- [ ] Carte de densité de trafic (heatmap)
- [ ] Extraction routes principales (DBSCAN)
- [ ] Dashboard de monitoring simple
- [ ] API REST basique (GET vessels/positions)
- [ ] Détection d'anomalies (Isolation Forest)
- [ ] Visualisation trajectoires par MMSI
- [ ] Statistiques par type de navire
- [ ] Export données (CSV, GeoJSON)

---

## 🎓 FEATURES PAR NIVEAU DE COMPLEXITÉ

### 🟢 Facile (1-3 jours)
- Statistiques descriptives
- Filtres et requêtes SQL
- Graphiques simples
- Cartes basiques

### 🟡 Moyen (1-2 semaines)
- Clustering spatial
- Détection d'anomalies simples
- API REST complète
- Dashboard interactif

### 🟠 Avancé (2-4 semaines)
- Modèles LSTM
- Prédiction trajectoires
- GNN pour interactions
- Système d'alertes temps réel

### 🔴 Expert (1-3 mois)
- Reinforcement Learning
- Transformers complexes
- Système complet de surveillance
- Infrastructure scalable en production

---

**Total Features Identifiées : 400+**
**Durée Estimation Complète : 12-18 mois (équipe 2-3 personnes)**

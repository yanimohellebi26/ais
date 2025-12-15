# 🗺️ ROADMAP CHRONOLOGIQUE - Projet AIS

> **Créé le** : 10 novembre 2025  
> **Type** : Plan d'exécution avec livrables techniques (sans code)  
> **Référence** : `CHECKLIST_FEATURES_AIS.md` pour les 400+ fonctionnalités  
> **Implémentation** : `PLANIFICATION_DEV.md` pour les exemples de code

---

## 📊 DÉJÀ FAIT

### Infrastructure
- ✅ PostgreSQL + PostGIS, Docker Compose, 9 migrations BD
- ✅ Tables : vessel, position_vessel, vessel_type, users, file_uploads

### ETL
- ✅ 12 fonctions Extract/Transform/Load opérationnelles
- ✅ Nettoyage GPS, détection outliers, calculs distance/vitesse

### Notebooks
- ✅ 5 notebooks : nettoyage, trajectoires, clustering K-Means/DBSCAN

### Référence CHECKLIST
> ✅ Phase 1 : Data Quality 60% (sections 1.1, 1.4, 1.5, 1.6 complètes)

---

## 🎯 ROADMAP - 27 SEMAINES

### PHASE 1 : ETL & Statistiques (Sem 1-3) 🔴 CRITIQUE

**Objectif** : Pipeline ETL complet avec features avancées

**Livrables ETL**
- [ ] 4 fichiers Transform : feature_engineering, gap_detection, status_validation, temporal_coherence
- [ ] 2 fichiers Load : statistics, gaps
- [ ] 4 tests unitaires

**Livrables BD**
- [ ] V10 : table vessel_statistics
- [ ] V11 : table position_gaps

**Livrables Config**
- [ ] Mise à jour pipelines.yaml
- [ ] Documentation techniques

**Validation**
- [ ] Tests coverage > 80%
- [ ] Performance < 5 min pour 1M positions

**Référence** : CHECKLIST Phase 1, sections 1.2 et 1.3

---

### PHASE 2 : Analyses Spatiales (Sem 4-5) 🟡 MOYENNE

**Objectif** : Analyses géographiques et temporelles

**Livrables Notebooks (6 fichiers)**
- [ ] spatial_analysis_zones.ipynb
- [ ] port_proximity_analysis.ipynb
- [ ] trajectory_analysis_advanced.ipynb
- [ ] temporal_patterns_analysis.ipynb
- [ ] gap_statistics_analysis.ipynb
- [ ] vessel_type_behavior_analysis.ipynb

**Livrables Documentation**
- [ ] Rapport PDF synthèse insights
- [ ] Visualisations exportées

**Validation**
- [ ] 6 notebooks exécutables
- [ ] Temps exécution < 10 min chacun

**Référence** : CHECKLIST Phases 2, 3, 5

---

### PHASE 3 : Table Ports (Sem 6) 🟡 MOYENNE

**Objectif** : Référentiel ports

**Livrables BD**
- [ ] V12 : table ports
- [ ] Seed data : 50+ ports

**Livrables ETL (optionnel)**
- [ ] transform_port_proximity.py

**Validation**
- [ ] Requêtes spatiales < 100ms

**Référence** : CHECKLIST Phase 12

---

### PHASE 4 : ML Anomalies (Sem 7-8) 🔴 HAUTE

**Objectif** : Détection comportements atypiques

**Livrables Notebook**
- [ ] anomaly_detection_ml.ipynb

**Livrables Modèles**
- [ ] 5 fichiers dans /models/anomaly_detection/
- [ ] isolation_forest_v1.pkl, scaler.pkl, metadata.json

**Livrables BD**
- [ ] V13 : table vessel_anomaly_score

**Validation**
- [ ] Accuracy > 85%

**Référence** : CHECKLIST Phase 7, section 7.2

---

### PHASE 5 : ML Routes (Sem 9-10) 🟡 MOYENNE

**Objectif** : Extraction routes maritimes

**Livrables Notebook**
- [ ] route_extraction_clustering.ipynb

**Livrables Modèles**
- [ ] 3 fichiers dans /models/clustering/

**Livrables BD**
- [ ] V14 : table maritime_routes

**Livrables Export**
- [ ] GeoJSON routes

**Validation**
- [ ] > 20 routes extraites

**Référence** : CHECKLIST Phases 4 et 7.1

---

### PHASE 6 : ML LSTM (Sem 11-13) 🟠 MOYENNE

**Objectif** : Prédiction trajectoires

**Livrables Notebook**
- [ ] prediction_trajectory.ipynb

**Livrables Modèles**
- [ ] 4 fichiers dans /models/trajectory_prediction/
- [ ] lstm_model_v1.h5

**Validation**
- [ ] MAE < 5 km

**Référence** : CHECKLIST Phases 8 et 9

---

### PHASE 7 : Backend Services (Sem 14-15) 🔴 CRITIQUE

**Objectif** : Logique métier

**Livrables Services (8 fichiers)**
- [ ] StatisticsService
- [ ] TrajectoryService
- [ ] RouteService
- [ ] AnomalyService
- [ ] FilterService
- [ ] PortService
- [ ] PredictionService
- [ ] MLModelService

**Livrables Tests**
- [ ] 8 fichiers tests unitaires

**Validation**
- [ ] Coverage > 80%
- [ ] Requêtes BD < 500ms

---

### PHASE 8 : API REST (Sem 16-17) 🔴 CRITIQUE

**Objectif** : Endpoints REST

**Livrables Controllers (7 fichiers)**
- [ ] StatisticsController
- [ ] TrajectoryController
- [ ] RouteController
- [ ] AnomalyController
- [ ] PortController
- [ ] PredictionController
- [ ] HeatmapController

**Livrables Endpoints (~30 total)**
- [ ] /api/statistics/* (4 endpoints)
- [ ] /api/trajectory/* (4 endpoints)
- [ ] /api/routes/* (4 endpoints)
- [ ] /api/anomalies/* (4 endpoints)
- [ ] /api/ports/* (4 endpoints)
- [ ] /api/predict/* (3 endpoints)
- [ ] /api/heatmap/* (3 endpoints)
- [ ] /api/vessels/* (2 endpoints)
- [ ] /api/search/* (2 endpoints)

**Livrables Documentation**
- [ ] Swagger/OpenAPI configuré
- [ ] Collection Postman

**Validation**
- [ ] Tous endpoints fonctionnels
- [ ] Temps réponse < 1s

**Référence** : CHECKLIST Phase 17

---

### PHASE 9 : Frontend Composants (Sem 18-20) 🔴 CRITIQUE

**Objectif** : Composants React réutilisables

**Livrables Composants Carte (5)**
- [ ] MapView, TrafficHeatmap, VesselMarkers, RouteLayer, TrajectoryLayer

**Livrables Composants Filtres (4)**
- [ ] VesselFilterPanel, DateRangePicker, VesselTypeSelector, SpeedRangeSlider

**Livrables Composants Stats (5)**
- [ ] GlobalStatsCard, VesselStatsPanel, TrafficChart, VesselTypeDistribution, SpeedDistributionChart

**Livrables Composants Listes (3)**
- [ ] VesselList, VesselTable, AnomalyList

**Livrables Composants Modals (3)**
- [ ] VesselDetailModal, VesselInfoCard, TrajectoryViewer

**Livrables Composants Utils (3)**
- [ ] SearchBar, LoadingSpinner, ErrorBoundary

**Livrables Services API (5)**
- [ ] api.js, vesselService.js, statisticsService.js, routeService.js, anomalyService.js

**Total** : ~28 fichiers composants

**Validation**
- [ ] Carte interactive fonctionnelle
- [ ] Tests coverage > 70%

---

### PHASE 10 : Frontend Pages (Sem 21-22) 🔴 CRITIQUE

**Objectif** : Pages complètes

**Livrables Pages (7)**
- [ ] Dashboard.jsx
- [ ] MapExplorer.jsx
- [ ] VesselDetails.jsx
- [ ] Statistics.jsx
- [ ] RoutesAnalysis.jsx
- [ ] Anomalies.jsx
- [ ] Predictions.jsx

**Livrables Navigation (4)**
- [ ] Header, Sidebar, Footer, routes.js

**Livrables Tests**
- [ ] Tests E2E Cypress

**Validation**
- [ ] Navigation fluide
- [ ] Responsive design
- [ ] Lighthouse > 80

**Référence** : CHECKLIST Phase 14

---

### PHASE 11 : Optimisations (Sem 23-24) 🟠 MOYENNE

**Objectif** : Performance

**Livrables BD**
- [ ] Partitionnement position_vessel
- [ ] Materialized views
- [ ] Audit index

**Livrables Backend**
- [ ] Cache Redis
- [ ] Pagination cursor-based
- [ ] Rate limiting

**Livrables Frontend**
- [ ] Lazy loading
- [ ] Code splitting
- [ ] Service Worker

**Livrables Monitoring**
- [ ] Prometheus + Grafana
- [ ] Dashboards métriques

**Validation**
- [ ] API < 500ms (p95)
- [ ] Page < 3s
- [ ] ETL 2x plus rapide

**Référence** : CHECKLIST Phase 20

---

### PHASE 12 : Tests & Docs (Sem 25-26) 🔴 CRITIQUE

**Objectif** : Production-ready

**Livrables Tests**
- [ ] Tests unitaires backend (coverage > 80%)
- [ ] Tests intégration API
- [ ] Tests E2E frontend
- [ ] Tests charge (JMeter)

**Livrables Documentation**
- [ ] Documentation API Swagger
- [ ] Guide utilisateur
- [ ] Documentation technique
- [ ] Diagrammes architecture

**Livrables CI/CD**
- [ ] GitHub Actions configuré
- [ ] Pipeline test/build/deploy

**Livrables Monitoring**
- [ ] Logs structurés
- [ ] Alertes configurées
- [ ] Health checks

**Livrables Déploiement**
- [ ] Config environnements (dev/staging/prod)
- [ ] Backup automatique BD
- [ ] SSL/TLS

**Validation**
- [ ] Coverage > 75%
- [ ] CI/CD opérationnel

**Référence** : CHECKLIST Phases 18 et 19

---

### PHASE 13 : Production (Sem 27) 🔴 CRITIQUE

**Objectif** : Go-live

**Livrables**
- [ ] Migration BD production
- [ ] Déploiement application
- [ ] Configuration DNS
- [ ] Tests smoke
- [ ] Formation utilisateurs
- [ ] Support actif

**Validation**
- [ ] Application accessible
- [ ] Aucune erreur critique
- [ ] Monitoring 24/7

---

## 📊 RÉSUMÉ PAR TYPE

### ETL : 20 modules
- ✅ 12 déjà faits
- ➕ 8 à créer

### BD : 14 migrations
- ✅ 9 déjà faites (V1-V9)
- ➕ 5 à créer (V10-V14)

### Notebooks : 14 total
- ✅ 5 déjà faits
- ➕ 9 à créer

### Modèles ML : 5 modèles
- ➕ Anomalies (2)
- ➕ Clustering (2)
- ➕ LSTM (1)

### Backend : 15 fichiers
- ➕ Services (8)
- ➕ Controllers (7)

### API : ~30 endpoints

### Frontend : ~40 fichiers
- ➕ Composants (28)
- ➕ Pages (7)
- ➕ Services (5)

### Tests : ~50 fichiers

---

## 🎯 JALONS CLÉS

| Semaine | Jalon | Livrable |
|---------|-------|----------|
| 3 | ETL Complet | Tables stats créées |
| 6 | Analyses | 6 notebooks + ports |
| 8 | ML Anomalies | Modèles entraînés |
| 10 | Routes | Table routes peuplée |
| 13 | Prédictions | LSTM opérationnel |
| 15 | Services | Backend logique métier |
| 17 | API | 30 endpoints REST |
| 20 | Composants | Frontend UI |
| 22 | Pages | 7 pages fonctionnelles |
| 24 | Performance | Optimisé |
| 26 | Tests | Coverage > 75% |
| 27 | 🚀 PRODUCTION | Go-live |

---

## 📋 PROGRESSION

### Phases Critiques (🔴)
- [ ] Phase 1 : 0/12 livrables
- [ ] Phase 4 : 0/7 livrables
- [ ] Phase 7 : 0/8 livrables
- [ ] Phase 8 : 0/37 livrables
- [ ] Phase 9 : 0/28 livrables
- [ ] Phase 10 : 0/11 livrables
- [ ] Phase 12 : 0/10 livrables
- [ ] Phase 13 : 0/1 livrable

### Phases Moyennes (🟡)
- [ ] Phase 2 : 0/6 livrables
- [ ] Phase 3 : 0/2 livrables
- [ ] Phase 5 : 0/5 livrables

### Phases Basses (🟠)
- [ ] Phase 6 : 0/5 livrables
- [ ] Phase 11 : 0/4 livrables

**Global : 0% complété**

---

## 🚀 ACTIONS IMMÉDIATES

### Cette Semaine
1. [ ] Créer branch `feature/phase-1-etl`
2. [ ] Créer `transform_feature_engineering.py`
3. [ ] Tests sur 10k positions
4. [ ] Documenter algorithmes

### Semaine Prochaine
1. [ ] 3 autres fichiers transform
2. [ ] Migrations V10 et V11
3. [ ] Loaders statistics/gaps
4. [ ] Tests intégration

### Semaine 3
1. [ ] Validation Phase 1
2. [ ] Merge vers main
3. [ ] Démarrer Phase 2

---

## 💡 RÈGLES

**ETL (.py)** : Traitement répétitif, production, performance
**Notebook (.ipynb)** : Exploration, visualisation, ML prototypage
**Table BD** : Données fréquentes, indexation, jointures SQL
**Pas de table** : Analyses ponctuelles, agrégations volée

---

## 📚 RÉFÉRENCES

- **CHECKLIST_FEATURES_AIS.md** : 400+ fonctionnalités détaillées
- **PLANIFICATION_DEV.md** : Code, architecture, implémentation
- **SPECS_PHASE_XX.md** : Spécifications techniques

---

> **Version** : 2.0 - Livrables techniques uniquement  
> **Auteur** : Yani + GitHub Copilot  
> **Statut** : Prêt pour exécution 🚀

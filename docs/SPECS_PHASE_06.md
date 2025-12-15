# Spécifications Techniques - Phase 6 : Détection de Comportements Anormaux & Alertes

> **Objectif** : Identifier comportements suspects et anomalies opérationnelles pour surveillance maritime
> **Durée estimée** : 3-4 semaines
> **Priorité** : ⭐⭐⭐ HAUTE (Sécurité maritime)

---

## 📋 Vue d'ensemble

Cette phase se concentre sur la détection automatique de comportements anormaux des navires pour des applications de sécurité maritime, surveillance des zones réglementées, détection de pêche illégale (IUU), et prévention d'incidents. Utilise des techniques de machine learning et d'analyse de patterns.

**Prérequis** :
- Phases 1-5 complétées
- Données nettoyées avec features calculées
- Trajectoires et routes extraites
- Python avec scikit-learn, xgboost, tensorflow/keras (optionnel)

**Cas d'usage** :
- Détection de pêche illégale (dark fishing)
- Surveillance zones protégées (AMP, ZEE)
- Détection collisions potentielles
- Identification transbordements suspects
- Alertes entrées zones interdites
- Détection défaillances AIS

---

## 6.1 Comportements de Navigation Anormaux

### 6.1.1 Détection changements brusques de trajectoire

**Objectif** : Identifier manœuvres d'évitement ou comportements suspects

**Fonctionnalités** :
- Calcul variations angulaires (delta COG) sur fenêtre glissante
- Détection virages > 90° en moins de 5 minutes
- Identification zigzags répétitifs
- Comparaison avec patterns normaux par type de navire

**Technologies** :
- PostgreSQL : Window functions pour calculs temporels
- PostGIS : Calculs géométriques sur trajectoires
- Python pandas : Analyse séries temporelles
- Méthode Z-score pour détection outliers

**Métriques** :
- Angle de changement (degrés)
- Taux de changement (degrés/minute)
- Fréquence des changements
- Score d'anormalité (0-100)

**Livrables** :
- Table : `trajectory_anomalies`
- Vue : `sudden_course_changes`
- Alertes temps réel via triggers PostgreSQL

---

### 6.1.2 Détection arrêts prolongés en pleine mer

**Objectif** : Identifier zones de mouillage inhabituelles ou transbordements

**Fonctionnalités** :
- Détection stationnement (SOG < 0.5 nœud) > 2h
- Exclusion zones portuaires et ancrage connues
- Vérification distance côte (> 10 nm)
- Clustering positions stationnaires proches

**Technologies** :
- PostGIS : ST_Distance pour calculs distances
- DBSCAN : Clustering positions stationnaires
- PostgreSQL : Filtres géographiques avec index GIST

**Critères d'alerte** :
- Durée arrêt > 2 heures
- Distance port > 10 nm
- Distance côte > 5 nm
- Profondeur eau > 50m (zones inhabituelles)

**Livrables** :
- Table : `offshore_stops`
- Vue : `suspicious_anchorages`
- Carte interactive des arrêts suspects

---

### 6.1.3 Vitesses anormales (trop rapide/lent pour le type)

**Objectif** : Détecter comportements opérationnels anormaux

**Fonctionnalités** :
- Comparaison vitesse observée vs normale par type
- Détection vitesses excessives (risque collision)
- Détection vitesses anormalement basses (panne moteur)
- Analyse contexte géographique (zones restreintes)

**Technologies** :
- Statistical Process Control (SPC)
- Percentiles dynamiques par vessel_type
- Isolation Forest (scikit-learn)
- Méthode IQR (Interquartile Range)

**Seuils par type** :
- Cargo : [5-25 nœuds] (en route)
- Tanker : [3-20 nœuds]
- Fishing : [0-15 nœuds]
- Passenger : [10-35 nœuds]

**Livrables** :
- Vue : `abnormal_speeds`
- Dashboard : vitesses en temps réel
- Alertes automatiques via email/SMS

---

### 6.1.4 Loitering (rôdage dans zone suspecte)

**Objectif** : Identifier surveillance ou activité suspecte

**Fonctionnalités** :
- Détection présence prolongée zone restreinte
- Calcul temps passé dans rayon géographique
- Identification patterns circulaires répétitifs
- Corrélation avec autres navires (rencontres)

**Technologies** :
- PostGIS : ST_Contains, ST_Within pour zones
- Convex Hull pour délimiter zones de rôdage
- Tortuosité élevée comme indicateur
- Time-in-zone analysis

**Définition loitering** :
- Temps dans zone > 4 heures
- Rayon déplacement < 2 nm
- Vitesse moyenne < 5 nœuds
- Pas de justification portuaire

**Livrables** :
- Table : `loitering_events`
- Zones sensibles définies (militaires, infrastructures)
- Système scoring gravité (1-10)

---

### 6.1.5 Entrée zones interdites/réglementées

**Objectif** : Surveillance respect réglementations maritimes

**Fonctionnalités** :
- Définition zones : AMP, ZEE, zones militaires, TSS
- Détection intersections trajectoires/zones
- Vérification autorisations (type navire, pavillon)
- Historique violations par navire

**Technologies** :
- PostGIS : ST_Intersects pour détection temps réel
- Table zones réglementées (polygones)
- Triggers PostgreSQL pour alertes instantanées
- API REST pour notifications externes

**Types de zones** :
- Aires Marines Protégées (AMP)
- Zones Économiques Exclusives (ZEE)
- Traffic Separation Schemes (TSS)
- Zones militaires / restricted areas
- Zones de pêche réglementées

**Livrables** :
- Table : `regulated_zones`
- Table : `zone_violations`
- Système alertes hiérarchisé (warning/critical)
- Rapport violations mensuel

---

## 6.2 Détection de Désactivation AIS

### 6.2.1 Identification gaps AIS suspects

**Objectif** : Détecter désactivations intentionnelles (dark shipping)

**Fonctionnalités** :
- Analyse gaps > 4h hors zones portuaires
- Calcul distance réapparition vs position prévue
- Détection patterns répétitifs (même zone/heure)
- Corrélation avec zones sensibles

**Technologies** :
- Analyse temporelle avec LAG/LEAD functions
- Calcul trajectoire prédite (dead reckoning)
- Machine Learning : Random Forest pour classification
- Anomaly scoring basé sur contexte

**Critères de suspicion** :
- Gap > 4h en pleine mer (> 20 nm côte)
- Réapparition > 100 nm de position prévue
- Gap dans zone de pêche réglementée
- Répétition > 3 gaps/mois même pattern

**Livrables** :
- Vue : `suspicious_ais_gaps`
- Modèle ML : classification gap légitime/suspect
- Score de risque par gap (0-100)
- Alertes autorités maritimes

---

### 6.2.2 Calcul position théorique pendant gap

**Objectif** : Estimer où devrait être le navire

**Fonctionnalités** :
- Dead reckoning depuis dernière position
- Utilisation derniers SOG/COG connus
- Prise en compte courants marins (optionnel)
- Calcul zone probable (ellipse d'incertitude)

**Technologies** :
- Algorithmes navigation dead reckoning
- PostGIS : ST_Project pour projections géographiques
- Calcul géodésique (formule Vincenty)
- Modèles courants océaniques (HYCOM, optionnel)

**Paramètres** :
- Vitesse constante (dernière SOG)
- Cap constant (dernier COG)
- Incertitude croissante avec durée gap
- Rayon ellipse : fonction temps écoulé

**Livrables** :
- Fonction : `calculate_predicted_position()`
- Table : `gap_predictions`
- Visualisation : ellipses d'incertitude sur carte

---

### 6.2.3 Comparaison réapparition vs position prévue

**Objectif** : Mesurer écart pour détecter anomalie

**Fonctionnalités** :
- Calcul distance position prévue vs réelle
- Scoring écart (fonction distance et temps)
- Alerte si écart > seuil (100 nm)
- Historique écarts par navire

**Technologies** :
- PostGIS : ST_Distance pour calculs
- Statistical analysis des écarts
- Classification binaire (normal/anormal)
- Tableau de bord visualisation écarts

**Seuils d'alerte** :
- Écart < 50 nm : Normal
- 50-100 nm : Suspect
- 100-200 nm : Très suspect
- > 200 nm : Critique (investigation)

**Livrables** :
- Table : `gap_reappearance_analysis`
- Graphique : distribution écarts
- Liste navires récidivistes

---

### 6.2.4 Dark fishing detection

**Objectif** : Identifier pêche avec AIS désactivé (IUU fishing)

**Fonctionnalités** :
- Détection gaps dans zones de pêche
- Analyse patterns fishing vessels
- Corrélation gaps avec saisons pêche
- Vérification licences/quotas (si data disponible)

**Technologies** :
- Zones FAO (Food and Agriculture Organization)
- Pattern recognition sur historique navire
- Geofencing zones pêche réglementées
- ML classifier : pêche légale vs IUU

**Indicateurs IUU** :
- Gap > 12h dans zone de pêche
- Réapparition port différent (écoulement capture)
- Répétition pattern sur période
- Non-respect saisons/quotas

**Livrables** :
- Table : `suspected_iuu_fishing`
- Intégration zones FAO
- Rapport mensuel autorités pêche
- Carte hotspots IUU

---

### 6.2.5 Zones fréquentes de désactivation

**Objectif** : Identifier zones à risque systématique

**Fonctionnalités** :
- Clustering géographique des gaps
- Heatmap intensité désactivations
- Analyse temporelle (jour/nuit, saison)
- Corrélation avec caractéristiques zone

**Technologies** :
- HDBSCAN pour clustering adaptatif
- Kernel Density Estimation (KDE)
- PostGIS pour agrégation spatiale
- Folium/Leaflet pour visualisation

**Analyse croisée** :
- Type navires désactivant AIS
- Profondeur eau moyenne
- Distance surveillance côtière
- Événements géopolitiques

**Livrables** :
- Table : `ais_blackout_zones`
- Heatmap interactive
- Rapport risques par zone
- Recommandations surveillance

---

## 6.3 Rencontres et Collisions

### 6.3.1 Détection navires trop proches (< 500m)

**Objectif** : Prévenir collisions et identifier transbordements

**Fonctionnalités** :
- Calcul distances inter-navires temps réel
- Détection proximité < 500m pendant > 5 min
- Exclusion zones portuaires (normal)
- Alerte collision imminente

**Technologies** :
- PostGIS : ST_DWithin pour requêtes proximité
- Index spatial R-tree pour performance
- PostgreSQL : JOIN auto-spatial
- Alertes push notifications

**Critères détection** :
- Distance < 500m
- Durée proximité > 5 minutes
- Hors zones portuaires
- Vitesses relatives compatibles

**Livrables** :
- Vue : `vessel_proximity_events`
- Système alertes temps réel
- Dashboard distances critiques
- Logs rencontres pour analyse

---

### 6.3.2 Calcul CPA (Closest Point of Approach)

**Objectif** : Prédire distance minimale future entre navires

**Fonctionnalités** :
- Calcul trajectoires prédites (SOG/COG)
- Détermination point approche minimale
- Calcul TCPA (Time to CPA)
- Alerte si CPA < seuil sécurité

**Technologies** :
- Algorithmes navigation (CPA calculation)
- Projections géodésiques
- Python NumPy pour calculs vectoriels
- Visualisation trajectoires prédites

**Paramètres** :
- Horizon prédiction : 30 minutes
- CPA critique : < 0.5 nm (926m)
- TCPA critique : < 10 minutes
- Mise à jour toutes les 5 minutes

**Livrables** :
- Fonction : `calculate_cpa()`
- Table : `collision_risks`
- Alertes prédictives
- Interface visualisation risques

---

### 6.3.3 Identification trajectoires de collision

**Objectif** : Détecter caps convergents dangereux

**Fonctionnalités** :
- Analyse angles relatifs entre navires
- Détection crossing situations (COLREGS)
- Identification head-on situations
- Overtaking detection

**Technologies** :
- Règlement COLREGS (Convention maritime)
- Calculs géométrie vectorielle
- Classification situations (8 types COLREGS)
- Decision support system

**Types situations** :
1. Head-on (face à face)
2. Crossing (croisement)
3. Overtaking (dépassement)
4. Give-way vessel (navire non-prioritaire)
5. Stand-on vessel (navire prioritaire)

**Livrables** :
- Table : `collision_scenarios`
- Classifier type situation
- Recommandations manœuvre
- Système scoring dangerosité

---

### 6.3.4 Alertes risque collision

**Objectif** : Notification proactive avant incident

**Fonctionnalités** :
- Surveillance continue proximité
- Calcul scoring risque multi-facteurs
- Notifications hiérarchisées (info/warning/critical)
- Intégration systèmes VTS (Vessel Traffic Service)

**Technologies** :
- Event-driven architecture
- PostgreSQL triggers pour détection temps réel
- Message queuing (RabbitMQ/Redis)
- API REST pour intégrations externes
- WebSockets pour updates temps réel

**Scoring risque** :
- Distance actuelle (poids 30%)
- CPA prédit (poids 25%)
- TCPA (poids 25%)
- Vitesses relatives (poids 10%)
- Conditions météo (poids 10%)

**Niveaux alerte** :
- INFO : CPA < 2 nm, TCPA > 30 min
- WARNING : CPA < 1 nm, TCPA 10-30 min
- CRITICAL : CPA < 0.5 nm, TCPA < 10 min
- EMERGENCY : Distance < 0.5 nm actuelle

**Livrables** :
- Système alertes multi-canal
- Dashboard temps réel
- Logs incidents évités
- Intégration email/SMS/push

---

### 6.3.5 Historique incidents évités

**Objectif** : Analyse rétrospective et amélioration système

**Fonctionnalités** :
- Logging toutes alertes déclenchées
- Tracking résolution (manœuvre effectuée)
- Analyse faux positifs/négatifs
- Statistiques efficacité système

**Technologies** :
- Time-series database (TimescaleDB)
- Business Intelligence (BI) tools
- Python pour analyse statistique
- Tableau de bord Grafana/Metabase

**Métriques KPI** :
- Nombre alertes/jour
- Taux faux positifs
- Temps moyen résolution
- Incidents réels évités
- Zones à risque récurrentes

**Livrables** :
- Base données historique
- Rapports mensuels incidents
- Analyse patterns incidents
- Recommandations amélioration

---

## 6.4 Transbordements Suspects

### 6.4.1 Détection rencontres prolongées en mer

**Objectif** : Identifier transferts potentiels illégaux

**Fonctionnalités** :
- Détection 2 navires proches (< 200m) > 1h
- Vérification hors zones portuaires (> 5 nm)
- Analyse types navires impliqués
- Corrélation avec liste navires suspects

**Technologies** :
- Self-join spatial-temporal sur position_vessel
- DBSCAN clustering sur positions proches
- Graph analysis (NetworkX) pour réseaux
- Pattern matching avec historique

**Critères suspicion** :
- Proximité < 200m pendant > 1h
- Distance port > 5 nm
- Vitesses < 2 nœuds (stationnaires)
- Navires types différents (ex: cargo + fishing)
- Zone eaux internationales

**Livrables** :
- Table : `suspected_transshipments`
- Réseau navires connectés
- Alertes autorités douanières
- Carte événements transbordement

---

### 6.4.2 Analyse patterns navires ravitailleurs

**Objectif** : Identifier navires supports de flotte

**Fonctionnalités** :
- Détection navires avec multiples rencontres
- Identification hubs transbordement
- Analyse fréquence rencontres par navire
- Profilage comportement ravitailleurs

**Technologies** :
- Graph database (Neo4j) pour réseaux
- Social Network Analysis (SNA)
- Centrality measures (degree, betweenness)
- Community detection algorithms

**Indicateurs ravitailleur** :
- > 5 rencontres/mois différents navires
- Temps cumulé proximité > 20h/mois
- Pattern routes en étoile (hub)
- Réapparitions zones transbordement

**Livrables** :
- Liste navires ravitailleurs identifiés
- Graphe réseau maritime
- Analyse communautés navires
- Monitoring continu flotte

---

### 6.4.3 Zones fréquentes de transbordement

**Objectif** : Cartographier hotspots activité

**Fonctionnalités** :
- Clustering géographique transbordements
- Heatmap densité événements
- Analyse caractéristiques zones (profondeur, distance côte)
- Évolution temporelle zones

**Technologies** :
- DBSCAN/HDBSCAN pour clustering
- Kernel Density Estimation
- PostGIS pour agrégations spatiales
- Time-series analysis évolution

**Caractéristiques zones** :
- Profondeur eau moyenne
- Distance surveillance (radar, patrouilles)
- Zones EEZ frontières
- Courants favorables
- Visibilité satellite limitée

**Livrables** :
- Table : `transshipment_hotspots`
- Carte interactive zones à risque
- Profil géographique zones
- Recommandations surveillance

---

### 6.4.4 Corrélation avec listes navires suspects

**Objectif** : Intégrer renseignement externe

**Fonctionnalités** :
- Import listes noires (IUU vessels, sanctions)
- Matching MMSI/IMO avec bases externes
- Enrichissement profil navire
- Scoring risque enrichi

**Technologies** :
- API intégrations (IMO, Interpol, NOAA)
- ETL pour import listes externes
- Data matching fuzzy (noms navires)
- Knowledge base enrichissement

**Sources données** :
- IUU Vessel Lists (FAO, RFMO)
- Sanctions lists (OFAC, UN, EU)
- Port State Control detentions
- Historical violations database
- Insurance/classification status

**Livrables** :
- Table : `blacklisted_vessels`
- Système matching automatique
- Alertes navires blacklist
- Enrichissement fiches navires

---

### 6.4.5 Système scoring de suspicion

**Objectif** : Prioriser investigations

**Fonctionnalités** :
- Agrégation multi-indicateurs
- Calcul score composite (0-100)
- Pondération facteurs selon gravité
- Classification niveaux risque

**Technologies** :
- Machine Learning : Ensemble methods
- Feature engineering (20+ features)
- XGBoost pour scoring
- SHAP pour explicabilité

**Facteurs scoring** :
1. Nombre rencontres (poids 20%)
2. Durée proximité (15%)
3. Zones sensibles (15%)
4. Gaps AIS (15%)
5. Présence blacklist (20%)
6. Historique violations (10%)
7. Pavillon navire (5%)

**Niveaux risque** :
- Score 0-30 : Faible
- 30-50 : Modéré
- 50-70 : Élevé
- 70-100 : Critique

**Livrables** :
- Modèle ML scoring
- Dashboard priorisation
- Alertes automatiques > seuil
- Rapports investigations recommandées

---

## 6.5 Patterns Opérationnels

### 6.5.1 Détection changements patterns habituels

**Objectif** : Identifier déviation comportement normal

**Fonctionnalités** :
- Profilage comportement normal par navire
- Détection déviation statistique
- Analyse multidimensionnelle (vitesse, zones, horaires)
- Alertes changement significatif

**Technologies** :
- Unsupervised learning (clustering)
- Statistical Process Control (SPC)
- K-Means pour profils types
- Change point detection algorithms

**Dimensions analysées** :
- Zones fréquentées
- Horaires opération
- Vitesses typiques
- Ports habituels
- Durée voyages
- Fréquence activité

**Livrables** :
- Table : `vessel_behavior_profiles`
- Détecteur anomalies comportementales
- Alertes changement pattern
- Analyse causes changements

---

### 6.5.2 Identification navires avec comportements multiples

**Objectif** : Détecter navires versatiles ou suspects

**Fonctionnalités** :
- Classification activités par navire
- Détection changements type opération
- Analyse cohérence type déclaré vs observé
- Identification navires caméléons

**Technologies** :
- Multi-label classification
- Clustering hiérarchique
- Decision trees pour règles
- Mixture models

**Exemples comportements** :
- Cargo faisant du fishing (suspect)
- Tanker avec patterns passenger
- Fishing avec vitesses cargo
- Type déclaré vs pattern observé

**Livrables** :
- Table : `vessel_activity_classifications`
- Liste navires multi-comportements
- Cohérence type vs activité
- Investigations recommandées

---

### 6.5.3 Analyse cohérence type navire vs activité

**Objectif** : Vérifier authenticité déclarations

**Fonctionnalités** :
- Comparaison features observées vs attendues
- Validation type AIS vs comportement
- Détection usurpation identité
- Vérification dimensions déclarées

**Technologies** :
- Supervised learning (classifier)
- Règles métier domaine maritime
- Validation croisée bases IMO
- Anomaly detection multi-features

**Vérifications** :
- Vitesse cohérente type
- Zones cohérentes activité
- Dimensions physiques réalistes
- Pattern temporel logique
- Ports visités appropriés

**Livrables** :
- Validation automatique cohérence
- Alertes incohérences critiques
- Recommandations inspections
- Statistiques taux incohérence

---

### 6.5.4 Détection usurpation MMSI

**Objectif** : Identifier spoofing identité navire

**Fonctionnalités** :
- Détection MMSI multiples positions simultanées
- Vérification cohérence position vs historique
- Analyse patterns transmission AIS
- Détection clonage MMSI

**Technologies** :
- Conflict detection algorithms
- Geofencing avec impossibilité physique
- Digital fingerprinting (AIS signals)
- Blockchain pour traçabilité (futur)

**Indicateurs spoofing** :
- Même MMSI 2 positions éloignées simultanées
- Téléportation impossible (distance/temps)
- Changements caractéristiques navire
- Patterns transmission anormaux
- Incohérence type navire

**Livrables** :
- Table : `mmsi_spoofing_events`
- Système détection temps réel
- Alertes autorités maritimes
- Base navires authentifiés

---

### 6.5.5 Navires "fantômes" (MMSI invalides)

**Objectif** : Identifier navires non-enregistrés

**Fonctionnalités** :
- Validation format MMSI (9 chiffres, MID valide)
- Vérification enregistrement bases officielles
- Détection MMSI tests/fictifs
- Monitoring navires non-identifiés

**Technologies** :
- Validation ITU MID codes
- API IMO ship database
- Pattern matching MMSI invalides
- Watch list maintenance

**MMSI invalides** :
- Format incorrect (≠ 9 chiffres)
- MID inexistant (Maritime ID)
- MMSI réservés tests (111, 999, etc.)
- Non-trouvé bases IMO/flag state

**Livrables** :
- Table : `invalid_mmsi_vessels`
- Système validation temps réel
- Blacklist MMSI suspects
- Rapports autorités

---

## 6.6 Système d'Alertes

### 6.6.1 Configuration règles d'alerte personnalisées

**Objectif** : Système flexible adapté besoins utilisateurs

**Fonctionnalités** :
- Interface configuration règles
- Builder requêtes visuelles (no-code)
- Templates alertes pré-configurés
- Gestion seuils dynamiques

**Technologies** :
- Rule engine (Drools ou custom)
- JSON-based rule definitions
- Web interface (React/Vue.js)
- REST API configuration

**Exemples règles** :
- "Alerte si cargo entre zone pêche"
- "Notification si gap AIS > 6h"
- "Warning vitesse > 30 nœuds zone portuaire"
- "Critical si collision risk TCPA < 5 min"

**Livrables** :
- Interface web configuration
- Base règles personnalisées
- Template library
- Documentation API règles

---

### 6.6.2 Niveaux de priorité (info/warning/critical)

**Objectif** : Hiérarchiser alertes selon gravité

**Fonctionnalités** :
- Classification automatique gravité
- Escalation selon non-résolution
- Priorisation dashboard
- Routage selon niveau

**Technologies** :
- Severity classification algorithm
- Priority queue management
- Event correlation engine
- Escalation policies

**Niveaux** :
1. **INFO** : Informationnel, pas action immédiate
2. **WARNING** : Attention requise, monitoring
3. **CRITICAL** : Action urgente nécessaire
4. **EMERGENCY** : Danger imminent, intervention

**Critères classification** :
- Type anomalie
- Historique navire
- Zone géographique
- Contexte opérationnel
- Impact potentiel

**Livrables** :
- Système classification automatique
- Politique escalation configurable
- Dashboard priorisation
- SLA par niveau

---

### 6.6.3 Notifications multi-canaux (email, SMS, dashboard)

**Objectif** : Assurer réception alertes critiques

**Fonctionnalités** :
- Routage intelligent selon urgence
- Multi-destinataires par type alerte
- Accusés réception
- Retry automatique échecs

**Technologies** :
- SMTP pour emails (SendGrid, SES)
- SMS gateway (Twilio, Nexmo)
- Push notifications (Firebase, OneSignal)
- WebSockets pour dashboard temps réel
- Message broker (RabbitMQ, Kafka)

**Canaux** :
1. **Dashboard** : Toutes alertes temps réel
2. **Email** : Warning + Critical
3. **SMS** : Critical + Emergency uniquement
4. **Push mobile** : Critical personnalisé
5. **API webhooks** : Intégrations systèmes tiers

**Livrables** :
- Service notifications unifié
- Configuration préférences utilisateur
- Templates messages
- Logs délivrance

---

### 6.6.4 Dashboard temps réel surveillance

**Objectif** : Interface centralisée monitoring

**Fonctionnalités** :
- Carte interactive navires temps réel
- Panel alertes actives
- Graphiques KPI
- Filtres multi-critères
- Drill-down détails alertes

**Technologies** :
- Frontend : React + Redux
- Cartographie : Leaflet ou Mapbox GL JS
- WebSockets pour real-time updates
- Backend API : FastAPI ou Node.js
- Database : PostgreSQL + Redis cache

**Composants dashboard** :
1. Carte principale (positions navires)
2. Panel alertes actives (liste)
3. Timeline événements
4. Statistiques jour/semaine/mois
5. Zones à risque overlay
6. Filtres navires/alertes
7. Details pane navire sélectionné

**Livrables** :
- Application web dashboard
- Mobile responsive
- Auto-refresh configurable
- Export rapports PDF

---

### 6.6.5 Logs et historique des alertes

**Objectif** : Traçabilité et analyse rétrospective

**Fonctionnalités** :
- Enregistrement toutes alertes
- Statut résolution (open/ack/closed)
- Actions prises documentation
- Audit trail complet
- Recherche avancée historique

**Technologies** :
- TimescaleDB pour time-series
- Elasticsearch pour recherche full-text
- Retention policies automatiques
- Archivage long terme (S3, GCS)

**Informations loggées** :
- Timestamp alerte
- Type et niveau
- Navire concerné
- Détails anomalie
- Utilisateur notifié
- Action prise
- Temps résolution
- Feedback efficacité

**Livrables** :
- Base historique alertes
- Interface recherche avancée
- Rapports statistiques
- Export formats multiples (CSV, JSON, PDF)

---

## 6.7 Machine Learning pour Prédictions

### 6.7.1 Modèle prédiction comportement futur

**Objectif** : Anticiper actions navires

**Fonctionnalités** :
- Prédiction destination probable
- Estimation heure arrivée (ETA)
- Prévision prochain comportement
- Détection intentions cachées

**Technologies** :
- Recurrent Neural Networks (LSTM, GRU)
- Transformer models pour séquences
- Feature engineering temporel
- TensorFlow/Keras ou PyTorch

**Features modèle** :
- Historique trajectoires navire
- Séquences positions récentes
- SOG/COG séries temporelles
- Patterns saisonniers
- Type navire et caractéristiques
- Contexte géographique

**Livrables** :
- Modèle ML prédiction trajectoire
- API prédictions temps réel
- Visualisation trajectoires prédites
- Métriques accuracy (MAE, RMSE)

---

### 6.7.2 Classification automatique niveau risque

**Objectif** : Scoring risque automatisé navires

**Fonctionnalités** :
- Classification multi-classe (low/medium/high/critical)
- Features multidimensionnelles
- Mise à jour continue scoring
- Explicabilité prédictions (SHAP)

**Technologies** :
- Gradient Boosting (XGBoost, LightGBM)
- Random Forest ensemble
- Neural Networks (MLP)
- SMOTE pour imbalanced classes
- Cross-validation k-fold

**Features (50+)** :
- Historique violations
- Patterns navigation
- Gaps AIS fréquence
- Zones fréquentées
- Vitesses anormales
- Rencontres suspects
- Pavillon risque
- Âge navire
- Classification société
- Résultats inspections

**Livrables** :
- Modèle classifier risque
- Score risque par navire
- Explication facteurs contributifs
- Dashboard priorités inspection

---

### 6.7.3 Détection anomalies par apprentissage

**Objectif** : Auto-learning patterns anormaux

**Fonctionnalités** :
- Apprentissage non-supervisé patterns normaux
- Détection déviation automatique
- Adaptation continue (online learning)
- Réduction faux positifs

**Technologies** :
- Autoencoders (reconstruction error)
- Isolation Forest
- One-Class SVM
- Local Outlier Factor (LOF)
- Deep learning unsupervised

**Approches** :
1. **Reconstruction-based** : Autoencoder
2. **Density-based** : LOF, DBSCAN
3. **Isolation-based** : iForest
4. **Statistical** : Z-score, IQR

**Livrables** :
- Modèles anomaly detection par type
- Pipeline auto-retraining
- Feedback loop amélioration
- Métriques performance (Precision/Recall)

---

### 6.7.4 Système de scoring composite

**Objectif** : Agrégation intelligente indicateurs

**Fonctionnalités** :
- Intégration 20+ sources données
- Pondération dynamique facteurs
- Normalisation scores hétérogènes
- Interprétabilité résultats

**Technologies** :
- Feature engineering avancé
- Weighted ensemble methods
- Bayesian aggregation
- Multi-criteria decision analysis (MCDA)

**Composantes score** :
1. **Comportement navigation** (30%)
   - Trajectoires anormales
   - Vitesses suspectes
   - Zones interdites
2. **Transparence AIS** (25%)
   - Gaps fréquence
   - Désactivations
3. **Interactions** (20%)
   - Rencontres prolongées
   - Transbordements
4. **Conformité** (15%)
   - Violations réglementaires
   - Inspections
5. **Renseignement** (10%)
   - Listes noires
   - Sanctions

**Livrables** :
- Score composite 0-100
- Décomposition par composante
- Visualisation radar chart
- Évolution temporelle score

---

### 6.7.5 Amélioration continue via feedback

**Objectif** : Optimisation itérative modèles

**Fonctionnalités** :
- Collecte feedback utilisateurs
- Labellisation alertes (TP/FP/FN)
- Retraining automatique périodique
- A/B testing nouvelles versions

**Technologies** :
- MLOps pipeline (MLflow, Kubeflow)
- Active learning strategies
- Human-in-the-loop validation
- Model versioning (DVC)
- CI/CD pour ML (GitHub Actions)

**Boucle feedback** :
1. Alerte générée
2. Investigation utilisateur
3. Validation outcome (vrai/faux positif)
4. Labellisation dataset
5. Retraining modèle
6. Déploiement nouvelle version
7. A/B test performance

**Métriques suivi** :
- Precision/Recall par type alerte
- Taux faux positifs
- Temps investigation moyen
- Satisfaction utilisateurs
- ROI système détection

**Livrables** :
- Interface feedback utilisateur
- Pipeline retraining automatique
- Versioning modèles
- Rapports performance évolution
- Documentation amélioration continue

---

## 📊 Architecture Technique Globale

### Stack Technologique Recommandée

**Base de données** :
- PostgreSQL 15+ avec PostGIS 3.3+
- TimescaleDB pour time-series
- Redis pour cache temps réel
- Elasticsearch pour recherche (optionnel)

**Backend API** :
- Python FastAPI ou Flask
- Celery pour tâches asynchrones
- RabbitMQ/Redis pour message queue
- WebSockets (Socket.io) temps réel

**Machine Learning** :
- Python 3.10+
- scikit-learn 1.3+
- XGBoost, LightGBM
- TensorFlow/Keras ou PyTorch
- SHAP pour explicabilité

**Frontend** :
- React 18+ ou Vue.js 3+
- Leaflet ou Mapbox GL JS
- Chart.js ou D3.js
- Material-UI ou Ant Design

**DevOps** :
- Docker + Docker Compose
- Kubernetes (production)
- GitHub Actions CI/CD
- Monitoring : Prometheus + Grafana

**Notifications** :
- SendGrid (email)
- Twilio (SMS)
- Firebase Cloud Messaging (push)

---

## 📊 Livrables Phase 6

### Tables PostgreSQL
```
trajectory_anomalies
sudden_course_changes
offshore_stops
suspicious_anchorages
abnormal_speeds
loitering_events
regulated_zones
zone_violations
suspicious_ais_gaps
gap_predictions
gap_reappearance_analysis
suspected_iuu_fishing
ais_blackout_zones
vessel_proximity_events
collision_risks
collision_scenarios
suspected_transshipments
transshipment_hotspots
blacklisted_vessels
vessel_behavior_profiles
vessel_activity_classifications
mmsi_spoofing_events
invalid_mmsi_vessels
alert_rules
alert_history
alert_logs
risk_scores
```

### Modèles Machine Learning
```
models/
├── trajectory_predictor.pkl
├── risk_classifier.pkl
├── anomaly_detector.pkl
├── transshipment_scorer.pkl
├── iuu_fishing_detector.pkl
└── behavioral_profiler.pkl
```

### APIs
```
/api/v1/alerts
├── GET /active
├── GET /history
├── POST /configure
├── PUT /{id}/acknowledge
├── DELETE /{id}/dismiss

/api/v1/anomalies
├── GET /list
├── GET /{vessel_id}
├── POST /detect

/api/v1/risk
├── GET /score/{vessel_id}
├── GET /ranking
├── POST /calculate

/api/v1/predictions
├── POST /trajectory
├── POST /eta
└── POST /behavior
```

### Dashboards
```
dashboards/
├── realtime_monitoring.html
├── alert_management.html
├── risk_analysis.html
├── vessel_profiling.html
├── zone_surveillance.html
└── ml_performance.html
```

### Documentation
```
docs/
├── alert_rules_guide.md
├── ml_models_documentation.md
├── api_reference.md
├── user_manual.pdf
└── technical_architecture.pdf
```

---

## ✅ Critères de Validation Phase 6

**Phase 6 considérée terminée si** :

1. ✅ **Détection anomalies opérationnelle**
   - Au moins 8 types anomalies détectés
   - Taux faux positifs < 20%

2. ✅ **Système alertes fonctionnel**
   - Multi-canaux implémenté
   - Temps réponse < 5 secondes
   - Dashboard temps réel opérationnel

3. ✅ **Modèles ML déployés**
   - Minimum 3 modèles en production
   - Accuracy > 80% sur test set
   - Pipeline retraining automatique

4. ✅ **Intégrations complètes**
   - API REST documentée
   - Webhooks configurables
   - Notifications multi-canaux

5. ✅ **Documentation livrée**
   - Guide utilisateur complet
   - Documentation technique
   - Runbooks opérationnels

6. ✅ **Tests validés**
   - Tests unitaires > 80% coverage
   - Tests intégration passés
   - Load testing réalisé

---

## 🚀 Prochaines Étapes

Après Phase 6 :
- **Phase 7** : Visualisations Avancées & Reporting
- **Phase 8** : Optimisation Performance & Scalabilité
- **Phase 9** : Intégration Données Externes (météo, bathymétrie)
- **Phase 10** : Mobile App & Alertes Terrain

---

**Fin SPECS_PHASE_06.md**

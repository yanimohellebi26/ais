# Spécifications Techniques - Phase 3 : Analyse par Type de Navire

> **Objectif** : Analyser et comparer les comportements selon les types de navires
> **Durée estimée** : 2 semaines
> **Priorité** : ⭐⭐ MOYENNE-HAUTE

---

## 📋 Vue d'ensemble

Cette phase exploite la classification des navires (vessel_type, vessel_group) pour identifier les patterns comportementaux spécifiques à chaque catégorie. L'objectif est de comprendre comment les différents types de navires utilisent l'espace maritime.

**Prérequis** :
- Phase 1 et 2 complétées
- Table `vessel_type` avec codes AIS standardisés
- Features calculées (SOG, distance, temps en mer)

**Types de navires AIS (codes principaux)** :
```
20-29 : Wing In Ground (WIG)
30     : Fishing
31-32 : Towing vessels
33     : Dredging/underwater ops
34     : Diving ops
35     : Military ops
36     : Sailing
37     : Pleasure craft
40-49 : High speed craft (HSC)
50     : Pilot vessel
51     : Search and Rescue (SAR)
52     : Tug
53     : Port tender
54     : Anti-pollution
55     : Law enforcement
56     : Spare
57-58 : Medical/spare
59     : Spare
60-69 : Passenger
70-79 : Cargo
80-89 : Tanker
90-99 : Other
```

---

## 3.1 Segmentation par Groupe

### 3.1.1 Statistiques par vessel_group

**Objectif** : Produire statistiques descriptives pour chaque catégorie

**Vue d'ensemble globale** :
```sql
CREATE MATERIALIZED VIEW vessel_type_statistics AS
SELECT
    vt.vessel_group,
    vt.type_code,
    COUNT(DISTINCT v.id) AS vessel_count,
    COUNT(DISTINCT v.mmsi) AS unique_mmsi_count,
    COUNT(pv.id) AS total_positions,
    AVG(v.length) AS avg_length_m,
    AVG(v.width) AS avg_width_m,
    AVG(v.draft) AS avg_draft_m,
    STDDEV(v.length) AS std_length_m,
    MIN(v.length) AS min_length_m,
    MAX(v.length) AS max_length_m
FROM vessel_type vt
LEFT JOIN vessel v ON vt.id = v.vessel_type_id
LEFT JOIN position_vessel pv ON v.id = pv.vessel_id
GROUP BY vt.vessel_group, vt.type_code
ORDER BY vessel_count DESC;

CREATE INDEX idx_vessel_type_stats ON vessel_type_statistics(vessel_group);
```

**Statistiques de navigation par type** :
```sql
CREATE MATERIALIZED VIEW vessel_type_navigation_stats AS
SELECT
    vt.vessel_group,
    COUNT(DISTINCT pv.vessel_id) AS active_vessels,
    AVG(pv.sog) AS avg_sog,
    STDDEV(pv.sog) AS std_sog,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pv.sog) AS median_sog,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY pv.sog) AS p95_sog,
    AVG(pv.distance_nm) AS avg_distance_per_leg_nm,
    SUM(pv.distance_nm) AS total_distance_nm,
    AVG(vas.total_hours_in_port) AS avg_hours_in_port,
    AVG(vas.total_distance_nm) AS avg_total_distance_per_vessel_nm
FROM vessel_type vt
JOIN vessel v ON vt.id = v.vessel_type_id
JOIN position_vessel pv ON v.id = pv.vessel_id
LEFT JOIN vessel_activity_summary vas ON v.id = vas.vessel_id
WHERE pv.is_valid = true
GROUP BY vt.vessel_group
ORDER BY avg_sog DESC;
```

**Livrables** :
- Vue : `vessel_type_statistics`
- Vue : `vessel_type_navigation_stats`
- CSV : `reports/vessel_type_statistics.csv`
- Script : `analysis/vessel_type_stats.py`

---

**Fin de SPECS_PHASE_03.md** (version abrégée pour respecter la limite)

> **Voulez-vous que je continue avec SPECS_PHASE_04.md ?**

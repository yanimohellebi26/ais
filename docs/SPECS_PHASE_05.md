# Spécifications Techniques - Phase 5 : Analyse Temporelle

> **Objectif** : Analyser les patterns temporels du trafic maritime (horaire, journalier, saisonnier)
> **Durée estimée** : 2 semaines
> **Priorité** : ⭐⭐ MOYENNE

---

## 📋 Vue d'ensemble

Cette phase se concentre sur l'analyse des dimensions temporelles des données AIS : patterns horaires, hebdomadaires, mensuels et saisonniers. L'objectif est d'identifier les cycles d'activité maritime et de détecter les anomalies temporelles.

**Prérequis** :
- Phase 1, 2, 3, 4 complétées
- Données avec timestamps valides
- Python avec pandas, matplotlib, seaborn, statsmodels

**Dimensions temporelles analysées** :
- Heure de la journée (0-23h)
- Jour de la semaine (lundi-dimanche)
- Jour du mois (1-31)
- Mois de l'année (1-12)
- Saisons (printemps, été, automne, hiver)
- Années (tendances long terme)

---

## 5.1 Patterns Temporels

### 5.1.1 Distribution horaire du trafic (0-24h)

**Objectif** : Identifier les heures de forte/faible activité

**Agrégation par heure** :
```sql
CREATE MATERIALIZED VIEW hourly_traffic_distribution AS
SELECT
    EXTRACT(HOUR FROM base_date_time) AS hour_of_day,
    COUNT(*) AS position_count,
    COUNT(DISTINCT vessel_id) AS unique_vessels,
    AVG(sog) AS avg_speed,
    COUNT(*) FILTER (WHERE is_moving) AS moving_count,
    COUNT(*) FILTER (WHERE distance_to_nearest_port_nm < 5) AS near_port_count
FROM position_vessel
WHERE is_valid = true
GROUP BY EXTRACT(HOUR FROM base_date_time)
ORDER BY hour_of_day;

-- Statistiques
SELECT
    hour_of_day,
    position_count,
    unique_vessels,
    ROUND(avg_speed::numeric, 2) AS avg_speed_knots,
    ROUND((moving_count * 100.0 / position_count)::numeric, 1) AS pct_moving
FROM hourly_traffic_distribution;
```

**Graphique 24h** :
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def plot_hourly_traffic_pattern():
    df = pd.read_sql("SELECT * FROM hourly_traffic_distribution", engine)
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Positions par heure
    axes[0].bar(df['hour_of_day'], df['position_count'], 
                color='steelblue', alpha=0.7)
    axes[0].set_xlabel('Hour of Day', fontsize=12)
    axes[0].set_ylabel('Position Count', fontsize=12)
    axes[0].set_title('AIS Position Distribution by Hour', fontsize=14)
    axes[0].grid(True, alpha=0.3, axis='y')
    axes[0].set_xticks(range(0, 24))
    
    # Navires uniques par heure
    axes[1].plot(df['hour_of_day'], df['unique_vessels'], 
                 marker='o', linewidth=2, color='coral')
    axes[1].fill_between(df['hour_of_day'], df['unique_vessels'], 
                          alpha=0.3, color='coral')
    axes[1].set_xlabel('Hour of Day', fontsize=12)
    axes[1].set_ylabel('Unique Vessels', fontsize=12)
    axes[1].set_title('Active Vessels by Hour', fontsize=14)
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xticks(range(0, 24))
    
    plt.tight_layout()
    plt.savefig('reports/hourly_traffic_pattern.png', dpi=300)
    print("Saved: reports/hourly_traffic_pattern.png")

plot_hourly_traffic_pattern()
```

**Radar chart 24h** :
```python
def plot_hourly_radar():
    df = pd.read_sql("SELECT * FROM hourly_traffic_distribution", engine)
    
    # Normaliser pour radar
    values = df['position_count'].values
    values_norm = (values - values.min()) / (values.max() - values.min())
    values_norm = np.append(values_norm, values_norm[0])  # Fermer le cercle
    
    angles = np.linspace(0, 2 * np.pi, 24, endpoint=False).tolist()
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    ax.plot(angles, values_norm, 'o-', linewidth=2, color='navy')
    ax.fill(angles, values_norm, alpha=0.25, color='steelblue')
    
    # Labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([f'{h}h' for h in range(24)], fontsize=9)
    ax.set_ylim(0, 1)
    ax.set_title('24-Hour Traffic Distribution (Radar)', fontsize=14, pad=20)
    ax.grid(True)
    
    plt.tight_layout()
    plt.savefig('reports/hourly_traffic_radar.png', dpi=300)

plot_hourly_radar()
```

**Livrables** :
- Vue : `hourly_traffic_distribution`
- Graphiques : bar chart et radar chart
- CSV : `reports/hourly_statistics.csv`

---

### 5.1.2 Distribution journalière (lundi-dimanche)

**Objectif** : Comparer activité en semaine vs week-end

**Agrégation par jour de la semaine** :
```sql
CREATE MATERIALIZED VIEW daily_traffic_distribution AS
SELECT
    EXTRACT(DOW FROM base_date_time) AS day_of_week,
    CASE EXTRACT(DOW FROM base_date_time)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END AS day_name,
    COUNT(*) AS position_count,
    COUNT(DISTINCT vessel_id) AS unique_vessels,
    COUNT(DISTINCT DATE(base_date_time)) AS day_count,
    AVG(sog) AS avg_speed,
    -- Moyennes par jour
    COUNT(*) / NULLIF(COUNT(DISTINCT DATE(base_date_time)), 0) AS avg_positions_per_day,
    COUNT(DISTINCT vessel_id) / NULLIF(COUNT(DISTINCT DATE(base_date_time)), 0) AS avg_vessels_per_day
FROM position_vessel
WHERE is_valid = true
GROUP BY EXTRACT(DOW FROM base_date_time)
ORDER BY day_of_week;

-- Week-end vs Semaine
SELECT
    CASE
        WHEN day_of_week IN (0, 6) THEN 'Weekend'
        ELSE 'Weekday'
    END AS period,
    SUM(position_count) AS total_positions,
    AVG(avg_positions_per_day) AS avg_daily_positions,
    AVG(unique_vessels) AS avg_unique_vessels
FROM daily_traffic_distribution
GROUP BY 
    CASE
        WHEN day_of_week IN (0, 6) THEN 'Weekend'
        ELSE 'Weekday'
    END;
```

**Graphique comparatif** :
```python
def plot_weekly_traffic_pattern():
    df = pd.read_sql("""
        SELECT * FROM daily_traffic_distribution 
        ORDER BY day_of_week
    """, engine)
    
    # Réordonner pour commencer lundi
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                 'Friday', 'Saturday', 'Sunday']
    df['day_name'] = pd.Categorical(df['day_name'], categories=day_order, ordered=True)
    df = df.sort_values('day_name')
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    
    # Positions par jour
    colors = ['#1f77b4']*5 + ['#ff7f0e']*2  # Bleu semaine, orange week-end
    axes[0].bar(df['day_name'], df['avg_positions_per_day'], color=colors, alpha=0.7)
    axes[0].set_ylabel('Average Positions per Day', fontsize=12)
    axes[0].set_title('Daily Traffic Distribution', fontsize=14)
    axes[0].grid(True, alpha=0.3, axis='y')
    axes[0].tick_params(axis='x', rotation=45)
    
    # Navires uniques par jour
    axes[1].bar(df['day_name'], df['avg_vessels_per_day'], color=colors, alpha=0.7)
    axes[1].set_ylabel('Average Unique Vessels per Day', fontsize=12)
    axes[1].set_title('Active Vessels by Day of Week', fontsize=14)
    axes[1].grid(True, alpha=0.3, axis='y')
    axes[1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('reports/weekly_traffic_pattern.png', dpi=300)

plot_weekly_traffic_pattern()
```

**Heatmap heure × jour** :
```python
def plot_hourly_daily_heatmap():
    query = """
    SELECT
        EXTRACT(HOUR FROM base_date_time) AS hour,
        EXTRACT(DOW FROM base_date_time) AS dow,
        COUNT(*) AS traffic
    FROM position_vessel
    WHERE is_valid = true
    GROUP BY hour, dow
    """
    df = pd.read_sql(query, engine)
    
    # Pivot
    pivot = df.pivot(index='hour', columns='dow', values='traffic')
    pivot.columns = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(pivot, cmap='YlOrRd', annot=False, fmt='d', 
                cbar_kws={'label': 'Position Count'}, ax=ax)
    ax.set_xlabel('Day of Week', fontsize=12)
    ax.set_ylabel('Hour of Day', fontsize=12)
    ax.set_title('Traffic Heatmap: Hour × Day of Week', fontsize=14)
    
    plt.tight_layout()
    plt.savefig('reports/hourly_daily_heatmap.png', dpi=300)

plot_hourly_daily_heatmap()
```

**Livrables** :
- Vue : `daily_traffic_distribution`
- Graphiques : bar charts et heatmap
- Analyse : différence week-end/semaine

---

### 5.1.3 Distribution mensuelle/saisonnière

**Objectif** : Identifier variations saisonnières

**Agrégation par mois** :
```sql
CREATE MATERIALIZED VIEW monthly_traffic_distribution AS
SELECT
    EXTRACT(MONTH FROM base_date_time) AS month,
    TO_CHAR(base_date_time, 'Month') AS month_name,
    CASE
        WHEN EXTRACT(MONTH FROM base_date_time) IN (12, 1, 2) THEN 'Winter'
        WHEN EXTRACT(MONTH FROM base_date_time) IN (3, 4, 5) THEN 'Spring'
        WHEN EXTRACT(MONTH FROM base_date_time) IN (6, 7, 8) THEN 'Summer'
        WHEN EXTRACT(MONTH FROM base_date_time) IN (9, 10, 11) THEN 'Fall'
    END AS season,
    COUNT(*) AS position_count,
    COUNT(DISTINCT vessel_id) AS unique_vessels,
    COUNT(DISTINCT DATE(base_date_time)) AS day_count,
    AVG(sog) AS avg_speed,
    COUNT(*) / NULLIF(COUNT(DISTINCT DATE(base_date_time)), 0) AS avg_positions_per_day
FROM position_vessel
WHERE is_valid = true
GROUP BY EXTRACT(MONTH FROM base_date_time), TO_CHAR(base_date_time, 'Month')
ORDER BY month;

-- Par saison
CREATE MATERIALIZED VIEW seasonal_traffic_distribution AS
SELECT
    season,
    SUM(position_count) AS total_positions,
    AVG(avg_positions_per_day) AS avg_daily_traffic,
    SUM(unique_vessels) / COUNT(*) AS avg_unique_vessels,
    AVG(avg_speed) AS avg_speed
FROM monthly_traffic_distribution
GROUP BY season
ORDER BY 
    CASE season
        WHEN 'Winter' THEN 1
        WHEN 'Spring' THEN 2
        WHEN 'Summer' THEN 3
        WHEN 'Fall' THEN 4
    END;
```

**Graphique mensuel** :
```python
def plot_monthly_traffic():
    df = pd.read_sql("SELECT * FROM monthly_traffic_distribution ORDER BY month", engine)
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Trafic mensuel
    axes[0].plot(df['month'], df['avg_positions_per_day'], 
                 marker='o', linewidth=2, markersize=8, color='navy')
    axes[0].fill_between(df['month'], df['avg_positions_per_day'], 
                          alpha=0.3, color='steelblue')
    axes[0].set_xlabel('Month', fontsize=12)
    axes[0].set_ylabel('Average Positions per Day', fontsize=12)
    axes[0].set_title('Monthly Traffic Distribution', fontsize=14)
    axes[0].set_xticks(range(1, 13))
    axes[0].set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    axes[0].grid(True, alpha=0.3)
    
    # Navires uniques
    axes[1].bar(df['month'], df['unique_vessels'], color='coral', alpha=0.7)
    axes[1].set_xlabel('Month', fontsize=12)
    axes[1].set_ylabel('Unique Vessels', fontsize=12)
    axes[1].set_title('Active Vessels by Month', fontsize=14)
    axes[1].set_xticks(range(1, 13))
    axes[1].set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    axes[1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('reports/monthly_traffic_pattern.png', dpi=300)

plot_monthly_traffic()
```

**Graphique saisonnier** :
```python
def plot_seasonal_comparison():
    df = pd.read_sql("SELECT * FROM seasonal_traffic_distribution", engine)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    seasons_order = ['Winter', 'Spring', 'Summer', 'Fall']
    df['season'] = pd.Categorical(df['season'], categories=seasons_order, ordered=True)
    df = df.sort_values('season')
    
    colors = ['#87CEEB', '#90EE90', '#FFD700', '#FF8C00']
    bars = ax.bar(df['season'], df['avg_daily_traffic'], color=colors, alpha=0.7)
    
    ax.set_ylabel('Average Daily Traffic', fontsize=12)
    ax.set_title('Seasonal Traffic Comparison', fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Annoter valeurs
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('reports/seasonal_traffic_comparison.png', dpi=300)

plot_seasonal_comparison()
```

**Livrables** :
- Vue : `monthly_traffic_distribution`
- Vue : `seasonal_traffic_distribution`
- Graphiques : patterns mensuels et saisonniers
- Rapport : mois de pointe et creux

---

### 5.1.4 Identification heures creuses et heures de pointe

**Objectif** : Définir périodes critiques

**Classification des périodes** :
```sql
CREATE MATERIALIZED VIEW traffic_peak_periods AS
WITH hourly_stats AS (
    SELECT
        hour_of_day,
        position_count,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY position_count) OVER () AS q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY position_count) OVER () AS q3,
        AVG(position_count) OVER () AS avg_traffic
    FROM hourly_traffic_distribution
)
SELECT
    hour_of_day,
    position_count,
    CASE
        WHEN position_count >= q3 THEN 'PEAK'
        WHEN position_count <= q1 THEN 'OFF_PEAK'
        ELSE 'NORMAL'
    END AS traffic_period,
    ROUND((position_count - avg_traffic) / avg_traffic * 100, 1) AS pct_deviation_from_avg
FROM hourly_stats
ORDER BY hour_of_day;

-- Résumé
SELECT
    traffic_period,
    COUNT(*) AS hour_count,
    STRING_AGG(hour_of_day::text, ', ' ORDER BY hour_of_day) AS hours,
    AVG(position_count) AS avg_traffic,
    MIN(position_count) AS min_traffic,
    MAX(position_count) AS max_traffic
FROM traffic_peak_periods
GROUP BY traffic_period
ORDER BY avg_traffic DESC;
```

**Définir heures de pointe par type de navire** :
```sql
CREATE MATERIALIZED VIEW peak_hours_by_vessel_type AS
SELECT
    vt.vessel_group,
    EXTRACT(HOUR FROM pv.base_date_time) AS hour_of_day,
    COUNT(*) AS position_count,
    RANK() OVER (PARTITION BY vt.vessel_group ORDER BY COUNT(*) DESC) AS traffic_rank
FROM position_vessel pv
JOIN vessel v ON pv.vessel_id = v.id
JOIN vessel_type vt ON v.vessel_type_id = vt.id
WHERE pv.is_valid = true
GROUP BY vt.vessel_group, EXTRACT(HOUR FROM pv.base_date_time)
ORDER BY vt.vessel_group, position_count DESC;

-- Top 3 heures par type
SELECT
    vessel_group,
    STRING_AGG(hour_of_day::text, ', ' ORDER BY traffic_rank) AS peak_hours
FROM peak_hours_by_vessel_type
WHERE traffic_rank <= 3
GROUP BY vessel_group;
```

**Visualisation heures de pointe** :
```python
def plot_peak_off_peak_periods():
    df = pd.read_sql("SELECT * FROM traffic_peak_periods", engine)
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    colors = df['traffic_period'].map({
        'PEAK': 'red',
        'NORMAL': 'gray',
        'OFF_PEAK': 'green'
    })
    
    bars = ax.bar(df['hour_of_day'], df['position_count'], color=colors, alpha=0.7)
    
    ax.set_xlabel('Hour of Day', fontsize=12)
    ax.set_ylabel('Position Count', fontsize=12)
    ax.set_title('Peak vs Off-Peak Traffic Periods', fontsize=14)
    ax.set_xticks(range(0, 24))
    ax.grid(True, alpha=0.3, axis='y')
    
    # Légende
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='red', alpha=0.7, label='Peak'),
        Patch(facecolor='gray', alpha=0.7, label='Normal'),
        Patch(facecolor='green', alpha=0.7, label='Off-Peak')
    ]
    ax.legend(handles=legend_elements, loc='upper left')
    
    plt.tight_layout()
    plt.savefig('reports/peak_off_peak_periods.png', dpi=300)

plot_peak_off_peak_periods()
```

**Livrables** :
- Vue : `traffic_peak_periods`
- Vue : `peak_hours_by_vessel_type`
- Graphique : visualisation périodes
- Tableau : heures de pointe par type

---

### 5.1.5 Détection patterns week-end vs semaine

**Objectif** : Quantifier différences comportementales

**Analyse comparative** :
```sql
CREATE MATERIALIZED VIEW weekend_vs_weekday_analysis AS
WITH classified_days AS (
    SELECT
        pv.*,
        CASE
            WHEN EXTRACT(DOW FROM pv.base_date_time) IN (0, 6) THEN 'Weekend'
            ELSE 'Weekday'
        END AS period_type
    FROM position_vessel pv
    WHERE pv.is_valid = true
)
SELECT
    period_type,
    COUNT(*) AS total_positions,
    COUNT(DISTINCT vessel_id) AS unique_vessels,
    COUNT(DISTINCT DATE(base_date_time)) AS day_count,
    AVG(sog) AS avg_speed,
    AVG(distance_nm) AS avg_distance_per_leg,
    COUNT(*) / NULLIF(COUNT(DISTINCT DATE(base_date_time)), 0) AS avg_positions_per_day,
    COUNT(DISTINCT vessel_id) / NULLIF(COUNT(DISTINCT DATE(base_date_time)), 0) AS avg_vessels_per_day
FROM classified_days
GROUP BY period_type;

-- Par type de navire
CREATE MATERIALIZED VIEW weekend_pattern_by_vessel_type AS
SELECT
    vt.vessel_group,
    CASE
        WHEN EXTRACT(DOW FROM pv.base_date_time) IN (0, 6) THEN 'Weekend'
        ELSE 'Weekday'
    END AS period_type,
    COUNT(*) AS position_count,
    COUNT(DISTINCT pv.vessel_id) AS unique_vessels,
    AVG(pv.sog) AS avg_speed
FROM position_vessel pv
JOIN vessel v ON pv.vessel_id = v.id
JOIN vessel_type vt ON v.vessel_type_id = vt.id
WHERE pv.is_valid = true
GROUP BY vt.vessel_group, 
    CASE
        WHEN EXTRACT(DOW FROM pv.base_date_time) IN (0, 6) THEN 'Weekend'
        ELSE 'Weekday'
    END
ORDER BY vt.vessel_group, period_type;
```

**Ratio week-end/semaine** :
```sql
CREATE MATERIALIZED VIEW weekend_weekday_ratio AS
WITH ratios AS (
    SELECT
        vessel_group,
        MAX(position_count) FILTER (WHERE period_type = 'Weekend') AS weekend_count,
        MAX(position_count) FILTER (WHERE period_type = 'Weekday') AS weekday_count
    FROM weekend_pattern_by_vessel_type
    GROUP BY vessel_group
)
SELECT
    vessel_group,
    weekend_count,
    weekday_count,
    ROUND((weekend_count::float / NULLIF(weekday_count, 0))::numeric, 2) AS weekend_weekday_ratio,
    CASE
        WHEN weekend_count > weekday_count THEN 'More Weekend Activity'
        WHEN weekend_count < weekday_count THEN 'More Weekday Activity'
        ELSE 'Similar'
    END AS activity_pattern
FROM ratios
ORDER BY weekend_weekday_ratio DESC;
```

**Graphique comparatif** :
```python
def plot_weekend_weekday_comparison():
    df = pd.read_sql("""
        SELECT * FROM weekend_pattern_by_vessel_type
        ORDER BY vessel_group, period_type
    """, engine)
    
    # Pivot pour grouped bar chart
    pivot = df.pivot(index='vessel_group', columns='period_type', values='position_count')
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    pivot.plot(kind='bar', ax=ax, color=['steelblue', 'coral'], alpha=0.7)
    ax.set_xlabel('Vessel Type', fontsize=12)
    ax.set_ylabel('Position Count', fontsize=12)
    ax.set_title('Weekend vs Weekday Activity by Vessel Type', fontsize=14)
    ax.legend(title='Period', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig('reports/weekend_weekday_comparison.png', dpi=300)

plot_weekend_weekday_comparison()
```

**Livrables** :
- Vue : `weekend_vs_weekday_analysis`
- Vue : `weekend_pattern_by_vessel_type`
- Vue : `weekend_weekday_ratio`
- Graphiques : comparaisons
- Rapport : types avec forte activité week-end

---

## 5.2 Séries Temporelles

### 5.2.1 Nombre de navires actifs par jour

**Objectif** : Suivre évolution quotidienne

**Time series daily** :
```sql
CREATE MATERIALIZED VIEW daily_active_vessels_timeseries AS
SELECT
    DATE(base_date_time) AS date,
    COUNT(DISTINCT vessel_id) AS active_vessels,
    COUNT(*) AS total_positions,
    AVG(sog) AS avg_speed,
    COUNT(*) FILTER (WHERE is_moving) AS moving_positions,
    COUNT(DISTINCT vessel_id) FILTER (
        WHERE distance_to_nearest_port_nm < 5
    ) AS vessels_near_port
FROM position_vessel
WHERE is_valid = true
GROUP BY DATE(base_date_time)
ORDER BY date;

-- Statistiques rolling (moyenne mobile 7 jours)
CREATE MATERIALIZED VIEW daily_vessels_with_rolling_avg AS
SELECT
    date,
    active_vessels,
    AVG(active_vessels) OVER (
        ORDER BY date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_avg_7d,
    AVG(active_vessels) OVER (
        ORDER BY date
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS rolling_avg_30d
FROM daily_active_vessels_timeseries
ORDER BY date;
```

**Graphique time series** :
```python
def plot_daily_vessels_timeseries():
    df = pd.read_sql("""
        SELECT * FROM daily_vessels_with_rolling_avg
        ORDER BY date
    """, engine)
    
    df['date'] = pd.to_datetime(df['date'])
    
    fig, ax = plt.subplots(figsize=(16, 6))
    
    # Données journalières
    ax.plot(df['date'], df['active_vessels'], 
            alpha=0.3, color='gray', label='Daily')
    
    # Moyenne mobile 7 jours
    ax.plot(df['date'], df['rolling_avg_7d'], 
            linewidth=2, color='steelblue', label='7-day Moving Avg')
    
    # Moyenne mobile 30 jours
    ax.plot(df['date'], df['rolling_avg_30d'], 
            linewidth=2, color='coral', label='30-day Moving Avg')
    
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Active Vessels', fontsize=12)
    ax.set_title('Daily Active Vessels Time Series', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Format dates
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('reports/daily_vessels_timeseries.png', dpi=300)

plot_daily_vessels_timeseries()
```

**Livrables** :
- Vue : `daily_active_vessels_timeseries`
- Vue : `daily_vessels_with_rolling_avg`
- Graphique : time series avec moyennes mobiles

---

### 5.2.2 Volume de positions enregistrées par jour

**Objectif** : Détecter variations de couverture AIS

**Time series positions** :
```sql
CREATE MATERIALIZED VIEW daily_position_volume AS
SELECT
    DATE(base_date_time) AS date,
    COUNT(*) AS position_count,
    COUNT(DISTINCT vessel_id) AS vessel_count,
    COUNT(*) / NULLIF(COUNT(DISTINCT vessel_id), 0) AS avg_positions_per_vessel,
    COUNT(*) FILTER (WHERE is_interpolated) AS interpolated_count,
    COUNT(*) FILTER (WHERE is_outlier) AS outlier_count
FROM position_vessel
WHERE is_valid = true
GROUP BY DATE(base_date_time)
ORDER BY date;
```

**Détection gaps de données** :
```sql
-- Identifier jours avec faible couverture
CREATE MATERIALIZED VIEW low_coverage_days AS
WITH stats AS (
    SELECT
        AVG(position_count) AS avg_daily_positions,
        STDDEV(position_count) AS std_daily_positions
    FROM daily_position_volume
)
SELECT
    dpv.date,
    dpv.position_count,
    dpv.vessel_count,
    s.avg_daily_positions,
    (dpv.position_count - s.avg_daily_positions) / s.std_daily_positions AS z_score
FROM daily_position_volume dpv, stats s
WHERE dpv.position_count < s.avg_daily_positions - 2 * s.std_daily_positions
ORDER BY dpv.date;
```

**Livrables** :
- Vue : `daily_position_volume`
- Vue : `low_coverage_days`
- Alerte : jours avec données anormales

---

### 5.2.3 Évolution du trafic dans le temps

**Objectif** : Tendances long terme (croissance/décroissance)

**Décomposition trend + saisonnalité** :
```python
from statsmodels.tsa.seasonal import seasonal_decompose
import pandas as pd

def decompose_traffic_timeseries():
    df = pd.read_sql("""
        SELECT date, active_vessels
        FROM daily_active_vessels_timeseries
        ORDER BY date
    """, engine)
    
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # Décomposition (additive)
    result = seasonal_decompose(
        df['active_vessels'],
        model='additive',
        period=7  # Saisonnalité hebdomadaire
    )
    
    # Plot
    fig, axes = plt.subplots(4, 1, figsize=(16, 12))
    
    df['active_vessels'].plot(ax=axes[0], title='Original')
    result.trend.plot(ax=axes[1], title='Trend')
    result.seasonal.plot(ax=axes[2], title='Seasonal')
    result.resid.plot(ax=axes[3], title='Residual')
    
    for ax in axes:
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('reports/traffic_decomposition.png', dpi=300)
    
    return result

decompose_traffic_timeseries()
```

**Régression linéaire pour tendance** :
```python
from scipy import stats

def calculate_traffic_trend():
    df = pd.read_sql("""
        SELECT
            date,
            active_vessels,
            ROW_NUMBER() OVER (ORDER BY date) AS day_number
        FROM daily_active_vessels_timeseries
        ORDER BY date
    """, engine)
    
    # Régression linéaire
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        df['day_number'],
        df['active_vessels']
    )
    
    print(f"Traffic Trend Analysis:")
    print(f"  Slope: {slope:.2f} vessels/day")
    print(f"  R²: {r_value**2:.4f}")
    print(f"  P-value: {p_value:.4e}")
    
    if p_value < 0.05:
        if slope > 0:
            print(f"  ✓ Significant GROWTH trend detected")
        else:
            print(f"  ✓ Significant DECLINE trend detected")
    else:
        print(f"  - No significant trend detected")
    
    # Plot avec régression
    fig, ax = plt.subplots(figsize=(14, 6))
    
    ax.scatter(df['day_number'], df['active_vessels'], 
               alpha=0.5, s=20, color='steelblue')
    
    # Ligne de régression
    y_pred = intercept + slope * df['day_number']
    ax.plot(df['day_number'], y_pred, 
            color='red', linewidth=2, 
            label=f'Trend: {slope:.2f} vessels/day (R²={r_value**2:.3f})')
    
    ax.set_xlabel('Days Since Start', fontsize=12)
    ax.set_ylabel('Active Vessels', fontsize=12)
    ax.set_title('Traffic Growth Trend Analysis', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('reports/traffic_trend_regression.png', dpi=300)

calculate_traffic_trend()
```

**Livrables** :
- Graphique : décomposition temporelle
- Graphique : régression linéaire
- Rapport : tendance détectée (croissance/déclin)

---

### 5.2.4 Détection de tendances (croissance/décroissance)

**Objectif** : Tests statistiques de tendances

**Mann-Kendall trend test** :
```python
from scipy.stats import kendalltau

def mann_kendall_test():
    df = pd.read_sql("""
        SELECT active_vessels
        FROM daily_active_vessels_timeseries
        ORDER BY date
    """, engine)
    
    # Mann-Kendall test
    n = len(df)
    x = df['active_vessels'].values
    
    # Calculer tau de Kendall
    tau, p_value = kendalltau(range(n), x)
    
    print(f"Mann-Kendall Trend Test:")
    print(f"  Kendall's tau: {tau:.4f}")
    print(f"  P-value: {p_value:.4e}")
    
    if p_value < 0.05:
        if tau > 0:
            print(f"  ✓ Significant INCREASING trend (p < 0.05)")
        else:
            print(f"  ✓ Significant DECREASING trend (p < 0.05)")
    else:
        print(f"  - No significant monotonic trend detected")
    
    return tau, p_value

mann_kendall_test()
```

**Livrables** :
- Test statistique : Mann-Kendall
- Rapport : significativité des tendances

---

### 5.2.5 Identification d'événements anormaux (pics, creux)

**Objectif** : Détecter anomalies temporelles

**Z-score anomaly detection** :
```sql
CREATE MATERIALIZED VIEW temporal_anomalies AS
WITH stats AS (
    SELECT
        AVG(active_vessels) AS mean_vessels,
        STDDEV(active_vessels) AS std_vessels
    FROM daily_active_vessels_timeseries
)
SELECT
    davt.date,
    davt.active_vessels,
    s.mean_vessels,
    s.std_vessels,
    (davt.active_vessels - s.mean_vessels) / s.std_vessels AS z_score,
    CASE
        WHEN ABS((davt.active_vessels - s.mean_vessels) / s.std_vessels) > 3 THEN 'EXTREME'
        WHEN ABS((davt.active_vessels - s.mean_vessels) / s.std_vessels) > 2 THEN 'MODERATE'
        ELSE 'NORMAL'
    END AS anomaly_level
FROM daily_active_vessels_timeseries davt, stats s
ORDER BY ABS((davt.active_vessels - s.mean_vessels) / s.std_vessels) DESC;

-- Anomalies seulement
SELECT *
FROM temporal_anomalies
WHERE anomaly_level IN ('MODERATE', 'EXTREME')
ORDER BY date;
```

**Isolation Forest** :
```python
from sklearn.ensemble import IsolationForest

def detect_anomalies_isolation_forest():
    df = pd.read_sql("""
        SELECT
            date,
            active_vessels,
            total_positions,
            avg_speed
        FROM daily_active_vessels_timeseries
        ORDER BY date
    """, engine)
    
    # Features pour anomaly detection
    features = df[['active_vessels', 'total_positions', 'avg_speed']].fillna(0)
    
    # Isolation Forest
    iso_forest = IsolationForest(contamination=0.05, random_state=42)
    df['anomaly'] = iso_forest.fit_predict(features)
    df['anomaly_score'] = iso_forest.score_samples(features)
    
    # -1 = anomalie, 1 = normal
    anomalies = df[df['anomaly'] == -1].copy()
    
    print(f"Detected {len(anomalies)} anomalies ({len(anomalies)/len(df)*100:.1f}%)")
    
    # Plot
    fig, ax = plt.subplots(figsize=(16, 6))
    
    normal = df[df['anomaly'] == 1]
    ax.scatter(normal['date'], normal['active_vessels'], 
               c='steelblue', alpha=0.6, s=20, label='Normal')
    ax.scatter(anomalies['date'], anomalies['active_vessels'], 
               c='red', s=100, marker='x', label='Anomaly', linewidths=2)
    
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Active Vessels', fontsize=12)
    ax.set_title('Temporal Anomaly Detection (Isolation Forest)', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('reports/temporal_anomalies.png', dpi=300)
    
    # Sauvegarder anomalies
    anomalies[['date', 'active_vessels', 'anomaly_score']].to_csv(
        'reports/temporal_anomalies.csv',
        index=False
    )
    
    return anomalies

detect_anomalies_isolation_forest()
```

**Livrables** :
- Vue : `temporal_anomalies`
- Graphique : anomalies détectées
- CSV : liste des dates anormales
- Rapport : causes possibles (météo, événements)

---

## 5.3 Durées et Fréquences

### 5.3.1 Durée moyenne des voyages par type

**Objectif** : Temps typique en mer par catégorie

**Calcul durées** :
```sql
CREATE MATERIALIZED VIEW voyage_duration_statistics AS
SELECT
    vt.vessel_group,
    COUNT(tr.vessel_id) AS voyage_count,
    AVG(tr.duration_hours) AS avg_duration_hours,
    STDDEV(tr.duration_hours) AS std_duration_hours,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY tr.duration_hours) AS median_duration_hours,
    MIN(tr.duration_hours) AS min_duration_hours,
    MAX(tr.duration_hours) AS max_duration_hours,
    -- Convertir en jours
    AVG(tr.duration_hours) / 24 AS avg_duration_days
FROM vessel_type vt
JOIN vessel v ON vt.id = v.vessel_type_id
JOIN vessel_trajectories tr ON v.id = tr.vessel_id
WHERE tr.duration_hours > 1  -- Au moins 1h
  AND tr.duration_hours < 720  -- Max 30 jours
GROUP BY vt.vessel_group
ORDER BY avg_duration_hours DESC;
```

**Graphique comparatif** :
```python
def plot_voyage_durations():
    df = pd.read_sql("SELECT * FROM voyage_duration_statistics", engine)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    ax.barh(df['vessel_group'], df['avg_duration_days'], 
            xerr=df['std_duration_hours']/24, 
            color='teal', alpha=0.7, capsize=5)
    
    ax.set_xlabel('Average Voyage Duration (days)', fontsize=12)
    ax.set_ylabel('Vessel Type', fontsize=12)
    ax.set_title('Average Voyage Duration by Vessel Type', fontsize=14)
    ax.grid(True, alpha=0.3, axis='x')
    ax.invert_yaxis()
    
    plt.tight_layout()
    plt.savefig('reports/voyage_durations_by_type.png', dpi=300)

plot_voyage_durations()
```

**Livrables** :
- Vue : `voyage_duration_statistics`
- Graphique : durées par type
- CSV : statistiques détaillées

---

### 5.3.2 Fréquence de passage par zone

**Objectif** : Utilisation des zones géographiques

**Déjà couvert en Phase 4.2.4 (route_passage_frequency)**

---

### 5.3.3 Identification navires les plus actifs

**Objectif** : Top navires par activité

**Classement activité** :
```sql
CREATE MATERIALIZED VIEW most_active_vessels AS
SELECT
    v.id AS vessel_id,
    v.mmsi,
    vt.vessel_group,
    v.name,
    COUNT(DISTINCT DATE(pv.base_date_time)) AS active_days,
    COUNT(*) AS total_positions,
    SUM(pv.distance_nm) AS total_distance_nm,
    AVG(pv.sog) AS avg_speed,
    MIN(pv.base_date_time) AS first_seen,
    MAX(pv.base_date_time) AS last_seen,
    COUNT(*) / NULLIF(COUNT(DISTINCT DATE(pv.base_date_time)), 0) AS avg_positions_per_day
FROM vessel v
JOIN vessel_type vt ON v.vessel_type_id = vt.id
JOIN position_vessel pv ON v.id = pv.vessel_id
WHERE pv.is_valid = true
GROUP BY v.id, v.mmsi, vt.vessel_group, v.name
ORDER BY total_positions DESC
LIMIT 100;

-- Top par type
SELECT
    vessel_group,
    COUNT(*) AS vessel_count,
    AVG(active_days) AS avg_active_days,
    AVG(total_distance_nm) AS avg_total_distance_nm
FROM most_active_vessels
GROUP BY vessel_group
ORDER BY avg_active_days DESC;
```

**Livrables** :
- Vue : `most_active_vessels`
- Rapport : top 100 navires les plus actifs
- Statistiques par type

---

### 5.3.4 Temps moyen entre deux voyages

**Objectif** : Fréquence d'utilisation des navires

**Calcul inter-voyage time** :
```sql
CREATE TABLE inter_voyage_intervals AS
WITH voyage_times AS (
    SELECT
        vessel_id,
        trajectory_end AS voyage_end,
        LEAD(trajectory_start) OVER (
            PARTITION BY vessel_id 
            ORDER BY trajectory_start
        ) AS next_voyage_start
    FROM vessel_trajectories
    ORDER BY vessel_id, trajectory_start
)
SELECT
    vessel_id,
    voyage_end,
    next_voyage_start,
    EXTRACT(EPOCH FROM (next_voyage_start - voyage_end)) / 3600 AS interval_hours,
    EXTRACT(EPOCH FROM (next_voyage_start - voyage_end)) / 86400 AS interval_days
FROM voyage_times
WHERE next_voyage_start IS NOT NULL
  AND next_voyage_start > voyage_end;

-- Statistiques par navire
CREATE MATERIALIZED VIEW vessel_inter_voyage_stats AS
SELECT
    vessel_id,
    COUNT(*) AS interval_count,
    AVG(interval_hours) AS avg_interval_hours,
    AVG(interval_days) AS avg_interval_days,
    MIN(interval_days) AS min_interval_days,
    MAX(interval_days) AS max_interval_days
FROM inter_voyage_intervals
WHERE interval_days < 365  -- Exclure très longues périodes
GROUP BY vessel_id;
```

**Livrables** :
- Table : `inter_voyage_intervals`
- Vue : `vessel_inter_voyage_stats`
- Histogramme : distribution des intervalles

---

### 5.3.5 Analyse régularité des lignes régulières

**Objectif** : Ponctualité des ferries/lignes

**Déjà couvert en Phase 3.2.4 (passenger_regular_lines)**

**Coefficient de variation** :
```sql
CREATE MATERIALIZED VIEW route_regularity_analysis AS
SELECT
    route_id,
    departure_port,
    arrival_port,
    trip_count,
    avg_duration_hours,
    std_duration_hours,
    -- Coefficient de variation (CV)
    std_duration_hours / NULLIF(avg_duration_hours, 0) AS cv_duration,
    CASE
        WHEN std_duration_hours / NULLIF(avg_duration_hours, 0) < 0.1 THEN 'Highly Regular'
        WHEN std_duration_hours / NULLIF(avg_duration_hours, 0) < 0.2 THEN 'Regular'
        WHEN std_duration_hours / NULLIF(avg_duration_hours, 0) < 0.3 THEN 'Moderately Regular'
        ELSE 'Irregular'
    END AS regularity_level
FROM passenger_regular_lines
ORDER BY cv_duration ASC;
```

**Livrables** :
- Vue : `route_regularity_analysis`
- Classement : lignes les plus régulières

---

## 📊 Livrables de la Phase 5

### Vues Matérialisées
```sql
hourly_traffic_distribution
daily_traffic_distribution
monthly_traffic_distribution
seasonal_traffic_distribution
traffic_peak_periods
peak_hours_by_vessel_type
weekend_vs_weekday_analysis
weekend_pattern_by_vessel_type
weekend_weekday_ratio
daily_active_vessels_timeseries
daily_vessels_with_rolling_avg
daily_position_volume
low_coverage_days
temporal_anomalies
voyage_duration_statistics
most_active_vessels
vessel_inter_voyage_stats
route_regularity_analysis
```

### Scripts Python
```
temporal_analysis/
├── plot_hourly_patterns.py
├── plot_weekly_patterns.py
├── plot_monthly_seasonal.py
├── analyze_timeseries.py
├── detect_temporal_anomalies.py
└── calculate_voyage_statistics.py
```

### Visualisations
```
reports/
├── hourly_traffic_pattern.png
├── hourly_traffic_radar.png
├── weekly_traffic_pattern.png
├── hourly_daily_heatmap.png
├── monthly_traffic_pattern.png
├── seasonal_traffic_comparison.png
├── peak_off_peak_periods.png
├── weekend_weekday_comparison.png
├── daily_vessels_timeseries.png
├── traffic_decomposition.png
├── traffic_trend_regression.png
├── temporal_anomalies.png
└── voyage_durations_by_type.png
```

### Rapports CSV
```
reports/
├── hourly_statistics.csv
├── weekly_statistics.csv
├── monthly_statistics.csv
├── seasonal_statistics.csv
├── temporal_anomalies.csv
├── most_active_vessels.csv
└── inter_voyage_intervals.csv
```

---

## ✅ Critères de Validation

**Phase 5 considérée terminée si** :

1. ✅ **Patterns horaires/hebdomadaires identifiés**
   - Heures de pointe déterminées
   - Différence week-end/semaine quantifiée

2. ✅ **Patterns saisonniers analysés**
   - Variations mensuelles documentées
   - Saisons comparées

3. ✅ **Séries temporelles traitées**
   - Time series créées
   - Tendances détectées (croissance/déclin)

4. ✅ **Anomalies temporelles détectées**
   - Dates anormales identifiées
   - Causes documentées

5. ✅ **Statistiques de durée calculées**
   - Durées de voyage par type
   - Intervalles entre voyages

6. ✅ **Visualisations complètes**
   - Minimum 12 graphiques temporels
   - Heatmaps et time series

---

## 🔄 Pipeline d'Exécution

```python
# run_phase5_temporal_analysis.py

def run_phase5():
    steps = [
        ("5.1.1", analyze_hourly_distribution),
        ("5.1.2", analyze_daily_distribution),
        ("5.1.3", analyze_monthly_seasonal),
        ("5.1.4", identify_peak_periods),
        ("5.1.5", compare_weekend_weekday),
        ("5.2.1", create_daily_timeseries),
        ("5.2.2", analyze_position_volume),
        ("5.2.3", analyze_traffic_evolution),
        ("5.2.4", detect_trends),
        ("5.2.5", detect_temporal_anomalies),
        ("5.3.1", calculate_voyage_durations),
        ("5.3.2", analyze_zone_frequency),
        ("5.3.3", identify_most_active_vessels),
        ("5.3.4", calculate_inter_voyage_time),
        ("5.3.5", analyze_route_regularity)
    ]
    
    for step_id, func in steps:
        print(f"Running step {step_id}: {func.__name__}")
        try:
            func()
            log_success(step_id)
        except Exception as e:
            log_error(step_id, str(e))
            raise
    
    print("Phase 5 completed!")
    generate_temporal_report()

if __name__ == "__main__":
    run_phase5()
```

---

**Fin de SPECS_PHASE_05.md**

> **Prochaine étape** : **SPECS_PHASE_06.md** (Détection de Comportements) ou passer aux phases ML ?

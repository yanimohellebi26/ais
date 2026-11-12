# Analyse du 1er Entraînement AIS + Plan d'action `train_eco_v2.py`

> Généré le 2026-03-03 | Basé sur `eco_output_final/`, PostgreSQL `ais`, notebooks EDA

---

## 1. Résultats du 1er entraînement

### Configuration
| Paramètre | Valeur |
|-----------|--------|
| Script | `train_eco.py` |
| Données | `ais_data.csv` — 22,250,708 lignes |
| GPU | 2x NVIDIA L40S 44 GB (DataParallel désactivé → 1 GPU) |
| Batch size | 16,384 |
| Hidden dim | 512 |
| Layers | 4 Transformer + 2 LSTM (bidir) |
| Heads | 8 |
| Dropout | 0.2 |
| Seq in / out | 20 / 10 steps (rééchantillonné à 1 min) |
| Features | 6 : `[dx, dy, sog_norm, sin_cog, cos_cog, dt]` |
| Loss | CustomLoss(pos_w=2.0, vel_w=1.0, dir_w=1.0) |
| Paramètres | 15,901,446 |
| Epochs | 24 (early stopping, patience=20) |

### Résultats
| Métrique | Valeur |
|----------|--------|
| **ADE (test)** | **4 419 m** |
| **FDE (test)** | **4 773 m** |
| Best val loss | 1.278 (epoch 4) |
| Train loss (epoch 24) | 2.82 (baisse continue) |
| Val loss | stagne ~1.50 depuis epoch 5 |
| LR final | 2.5e-4 (réduit 2 fois) |

### Courbe d'apprentissage (résumé)
```
Epoch  1 : TrainL=5.03  ValL=1.53  ADE=5052m  FDE=5494m
Epoch  4 : TrainL=3.74  ValL=1.28  ← BEST VAL LOSS
Epoch  6 : TrainL=3.61  ValL=1.45  ADE=4279m  ← Val remonte
Epoch 11 : TrainL=3.33  ValL=1.50  ADE=3866m
Epoch 16 : TrainL=3.02  ValL=1.49  ADE=3039m
Epoch 21 : TrainL=2.87  ValL=1.53  ADE=2794m
Epoch 24 : TrainL=2.82  ValL=1.54  → EARLY STOP
```
**Diagnostic : overfitting classique.** Le train loss descend mais la val loss stagne/remonte dès l'epoch 5.

---

## 2. Analyse des données PostgreSQL

### Vue d'ensemble
| Métrique | Valeur |
|----------|--------|
| Total positions | 22,250,708 |
| Navires uniques | 21,014 |
| Période | 2024-01-01 → 2024-01-06 (6 jours) |
| Étendue Lon | [-174.26, 147.34] |
| Étendue Lat | [0.07, 85.18] |

> ⚠️ Les données ne sont **pas** limitées au continent américain — elles couvrent l'hémisphère Nord entier (données NOAA MarineCadastre + trafic international).

### Schéma `position_vessel`
| Colonne | Type | Disponibilité | Utilité ML |
|---------|------|---------------|------------|
| `id` | bigint | 100% | — |
| `vessel_id` | integer | 100% | JOIN |
| `base_date_time` | timestamp | 100% | Feature temporelle |
| `sog` | float | ~100% | Feature core |
| `cog` | float | ~100% | Feature core |
| `heading` | smallint | **53.8%** | Feature utile (imputable) |
| `status_id` | integer | 77.6% | Feature contextuelle |
| `geom` | geography | 100% | Lat/Lon (PostGIS) |

### Schéma `vessel`
| Colonne | Disponibilité | Utilité ML |
|---------|---------------|------------|
| `vessel_type_id` | 100% | Type embedding |
| `length` | Partiel | Dimension navire |
| `width` | Partiel | Dimension navire |
| `draft` | Partiel | Dimension navire |
| `cargo_type_id` | Partiel | Type cargo |

### Distribution SOG — Problème critique
| Percentile | SOG (kn) |
|-----------|----------|
| 1% | 0.00 |
| 5% | 0.00 |
| **25%** | **0.00** |
| **50% (médiane)** | **0.30** |
| 75% | 6.40 |
| 95% | 13.60 |
| 99% | 21.30 |

> ⛔ **75% des positions ont SOG < 6.4 kn. 50% sont quasi-stationnaires (< 0.3 kn).** Le script filtre à SOG ≥ 0.1 kn → laisse passer énormément de bateaux à l'arrêt.

### Répartition par type de navire
| Type | Navires | Positions | % | Pertinence trajectoire |
|------|---------|-----------|---|----------------------|
| **Tug Tow** | 3,643 | 8,533,206 | **38.4%** | ❌ Erratique, courts déplacements |
| **Pleasure/Sailing** | 9,780 | 4,209,300 | **18.9%** | ❌ Loisirs, non-prédictible |
| **Cargo** | 1,661 | 2,862,547 | 12.9% | ✅ Trajectoires régulières |
| Other | 1,833 | 1,953,315 | 8.8% | ~ |
| Passenger | 1,218 | 1,712,222 | 7.7% | ✅ Routes fixes |
| Fishing | 1,583 | 1,427,574 | 6.4% | ~ Erratique |
| Tanker | 881 | 1,416,099 | 6.4% | ✅ Trajectoires longues |
| Military | 105 | 53,998 | 0.2% | — |

> ⚠️ **57% des données (Tug + Pleasure)** ont des trajectoires inadaptées à un modèle de prédiction de route maritime. Cela pollue massivement l'entraînement.

---

## 3. Problèmes identifiés

### P0 — Critiques (bloquants)

| # | Problème | Impact |
|---|----------|--------|
| 1 | **Scaler catastrophique** : σ=51,083m → signal noyé | ADE ×10 |
| 2 | **Feature `dt` constante** (60s après rééchantillonnage) | Bruit pur |
| 3 | **SOG filter trop laxiste** (≥ 0.1 kn) : 50% de bateaux stationnaires | Apprend du bruit |
| 4 | **Tug/Pleasure dominent** (57%) : trajectoires erratiques | Overfitting sur le mauvais signal |

### P1 — Architecture

| # | Problème | Impact |
|---|----------|--------|
| 5 | **Pas de positional encoding** dans le Transformer | Ne comprend pas l'ordre temporel |
| 6 | **Decoder simpliste** : `output[:, -10:, :]` | Pas de prédiction step-by-step cohérente |
| 7 | **MSE loss sensible aux outliers** | Gradients dominés par les erreurs extrêmes |

### P2 — Features manquantes

| # | Feature absente | Source | Impact |
|---|----------------|--------|--------|
| 8 | `delta_sog` (accélération) | Calculé | Manœuvres |
| 9 | `delta_cog` (taux de virage) | Calculé | Virages |
| 10 | `heading` | DB | Dérive/courant |
| 11 | `vessel_type` (embedding) | DB | Comportement par type |
| 12 | `status` (navigation/ancré/amarré) | DB | Contexte opérationnel |
| 13 | `heure_jour` sin/cos | BaseDateTime | Patterns horaires (trafic) |

---

## 4. État de l'art (SOTA 2024-2026)

### Modèles de référence

| Modèle | Architecture | ADE / Performance | Lien |
|--------|-------------|-------------------|------|
| **TrAISformer** | GPT-like, discrétise lat/lon/SOG/COG en bins, cross-entropy | < 10 NM à 9h | [arXiv:2109.03958](https://arxiv.org/abs/2109.03958) |
| **AIS-LLM** | LLM unifié (prédiction + anomalie + collision) | MSE 95.76 vs 268.98 (TrAISformer) | [arXiv:2508.07668](https://arxiv.org/html/2508.07668v1) |
| **PINN** | Physics-Informed NN, loss cinématique Euler/Heun | **ADE -32%** vs baselines | [arXiv:2506.12029](https://arxiv.org/abs/2506.12029) |
| **SEMINT** | LLM + intention de navigation sémantique | Long-term SOTA | [Taylor&Francis 2025](https://www.tandfonline.com/doi/full/10.1080/13658816.2025.2487990) |
| **AISFormer** | Transformer spatial-temporel | Long-term SOTA | [ScienceDirect 2025](https://www.sciencedirect.com/science/article/abs/pii/S0029801825017822) |
| **TPTrans** | Transformer + dépendances spatio-temporelles | Benchmark MDPI | [MDPI 2024](https://www.mdpi.com/2220-9964/13/11/400) |

### Encodage des positions — consensus SOTA

1. **Déplacements relatifs** : `dx[t] = pos[t] - pos[t-1]` → valeurs petites (~10-500m), homogènes ✅
2. **Projection UTM + origin-relative** : toutes les traj. démarrent à (0,0) en mètres ✅
3. **Discrétisation en bins** (TrAISformer) : classification au lieu de régression

### Loss functions SOTA
- **Huber/SmoothL1** — robuste aux outliers (standard)
- **Physics-informed loss** — pénalise `v ≠ dx/dt` et incohérences cinématiques → **-32% ADE**
- **Haversine loss** — distance géodésique directe
- **Cross-Entropy multi-résolution** — TrAISformer (discrétisation)

### Benchmarks ADE attendus
| Horizon prédiction | ADE cible |
|-------------------|-----------|
| 10 min (notre cas) | **< 200 m** |
| 1-2 h | < 1 NM (~1,850 m) |
| 4-6 h | < 5 NM (~9,200 m) |
| 9-10 h | < 10 NM (~18,500 m) |

> Notre ADE actuel de 4,419 m pour 10 min de prédiction est ~22× trop élevé.

---

## 5. Plan d'action `train_eco_v2.py`

### Phase 1 — Données propres (P0, impact ×10)

```python
# 1. Filtrage strict des données
df = df[df["SOG"] >= 2.0]                              # Bateaux en mouvement réel
df = df[df["vessel_group"].isin(["Cargo", "Tanker",    # Types à trajectoires régulières
                                  "Passenger", "Fishing",
                                  "Military", "Other"])]
# → retire Tug/Tow et Pleasure/Sailing

# 2. Intervalle de segmentation adaptatif
# Gap > 10 min OU changement de status → nouvelle trajectoire
# (au lieu du gap fixe 600s actuel)
```

### Phase 2 — Feature engineering (P1, impact ×2-3)

```python
# Nouvelles features (de 6 → 11)
feats = [
    dx_rel,        # delta lat en mètres (pos[t] - pos[t-1])  ← REMPLACE dx absolu
    dy_rel,        # delta lon en mètres (pos[t] - pos[t-1])  ← REMPLACE dy absolu
    sog_norm,      # SOG / 30.0 (inchangé)
    sin_cog,       # sin(COG)  (inchangé)
    cos_cog,       # cos(COG)  (inchangé)
    # SUPPRIMÉ : dt (constant = bruit)
    delta_sog,     # sog[t] - sog[t-1]  → accélération
    delta_cog_sin, # sin(cog[t] - cog[t-1])  → taux de virage
    delta_cog_cos, # cos(cog[t] - cog[t-1])
    sin_heading,   # sin(heading) si dispo, sinon sin(cog)
    cos_heading,   # cos(heading) si dispo, sinon cos(cog)
    sin_hour,      # sin(2π * heure / 24)  → cycle journalier
    cos_hour,      # cos(2π * heure / 24)
]
# → 12 features au total

# Vessel type : embedding learnable (pas one-hot)
# vessel_group → entier : Cargo=0, Tanker=1, Passenger=2, ...
```

### Phase 3 — Architecture améliorée (P2, impact ×2)

```python
class AISTransformerV2(nn.Module):
    def __init__(self, input_dim=12, hidden_dim=256, num_layers=4,
                 num_heads=8, dropout=0.15, seq_out=10,
                 n_vessel_types=8, vessel_embed_dim=16):
        super().__init__()
        self.seq_out = seq_out

        # Vessel type embedding
        self.vessel_embed = nn.Embedding(n_vessel_types, vessel_embed_dim)

        # Input projection
        self.input_proj = nn.Linear(input_dim + vessel_embed_dim, hidden_dim)

        # Positional encoding sinusoïdal
        self.pos_enc = SinusoidalPositionalEncoding(hidden_dim, max_len=200)

        # Encoder Transformer
        enc_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim, nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout, batch_first=True, activation='gelu'
        )
        self.encoder = nn.TransformerEncoder(enc_layer, num_layers=num_layers)

        # Decoder autorégressif
        dec_layer = nn.TransformerDecoderLayer(
            d_model=hidden_dim, nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout, batch_first=True, activation='gelu'
        )
        self.decoder = nn.TransformerDecoder(dec_layer, num_layers=2)

        # Learnable query tokens pour le decoder
        self.query_tokens = nn.Parameter(torch.randn(1, seq_out, hidden_dim))

        # Output projection : prédire dx, dy (+ optionnel sog, cog)
        self.output_proj = nn.Linear(hidden_dim, 2)  # prédire seulement dx, dy


class SinusoidalPositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=200):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        pos = torch.arange(max_len).unsqueeze(1).float()
        div = torch.exp(torch.arange(0, d_model, 2).float() * -(math.log(10000) / d_model))
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div)
        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x):
        return x + self.pe[:, :x.size(1)]
```

### Phase 4 — Loss function (P2, impact ×1.5)

```python
class PhysicsAwareLoss(nn.Module):
    """
    Combine Huber sur position + terme physics-informed.
    Pénalise les prédictions qui violent v = dx/dt.
    """
    def __init__(self, pos_w=1.0, physics_w=0.3, delta=1.0):
        super().__init__()
        self.pos_w = pos_w
        self.physics_w = physics_w
        self.huber = nn.HuberLoss(delta=delta)

    def forward(self, pred_dxy, target_dxy, pred_sog=None):
        # pred_dxy : (B, T, 2) déplacements prédits
        # target_dxy : (B, T, 2) déplacements réels
        pos_loss = self.huber(pred_dxy, target_dxy)

        # Terme physique : accélération doit être bornée
        if pred_dxy.shape[1] > 1:
            acc = pred_dxy[:, 1:, :] - pred_dxy[:, :-1, :]
            physics_loss = torch.mean(acc ** 2)  # pénalise les grands sauts
        else:
            physics_loss = torch.tensor(0.0, device=pred_dxy.device)

        return self.pos_w * pos_loss + self.physics_w * physics_loss
```

### Phase 5 — Training loop (P2, impact ×1.3)

```python
# Scheduler : Cosine Annealing au lieu de ReduceLROnPlateau
scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
    optimizer, T_0=20, T_mult=2, eta_min=1e-6
)

# Batch size réduit
BATCH_SIZE = 2048  # au lieu de 16384

# Gradient accumulation si besoin
ACCUM_STEPS = 4  # effective batch = 2048 * 4 = 8192

# Data augmentation
def augment_trajectory(x, y):
    # Rotation aléatoire dans le plan (dx, dy)
    angle = torch.rand(1) * 2 * math.pi
    cos_a, sin_a = torch.cos(angle), torch.sin(angle)
    R = torch.tensor([[cos_a, -sin_a], [sin_a, cos_a]])
    x[..., :2] = x[..., :2] @ R.T
    y[..., :2] = y[..., :2] @ R.T
    # Bruit gaussien
    x[..., :2] += torch.randn_like(x[..., :2]) * 0.01
    return x, y
```

### Phase 6 — Normalisation corrigée

```python
# Scaler sur les DELTAS (dx_rel, dy_rel) → σ << 51 km
# Chaque step est un déplacement de ~10-500m → σ ~ 100-300m
# Bien plus facile à apprendre pour le modèle
scaler_pos = StandardScaler()  # fitter sur dx_rel, dy_rel
scaler_sog = StandardScaler()  # fitter sur sog, delta_sog séparément
```

---

## 6. Récapitulatif des changements `v1 → v2`

| Aspect | v1 (actuel) | v2 (cible) |
|--------|-------------|------------|
| **Features** | 6 (`dx_abs, dy_abs, sog, sin_cog, cos_cog, dt`) | 12 (`dx_rel, dy_rel, sog, sin_cog, cos_cog, Δsog, Δcog×2, heading×2, heure×2`) |
| **Normalisation** | σ=51,083 m (positions absolues) | σ~200 m (déplacements relatifs) |
| **SOG filter** | ≥ 0.1 kn | **≥ 2.0 kn** |
| **Types filtrés** | VesselType [20,90] (tout) | Cargo, Tanker, Passenger, Fishing, Other |
| **Architecture decoder** | `output[:, -10:, :]` | Transformer Decoder autorégressif |
| **Positional Encoding** | Absent | Sinusoïdal |
| **Vessel type** | Non utilisé | Embedding learnable |
| **Loss** | MSE pondéré | Huber + Physics-informed |
| **Scheduler** | ReduceLROnPlateau | CosineAnnealingWarmRestarts |
| **Batch size** | 16,384 | 2,048 + gradient accumulation |
| **Data augmentation** | Aucune | Rotation + bruit gaussien |
| **Feature `dt`** | Présente (constante = bruit) | **Supprimée** |

---

## 7. Résultats attendus

| Étape | ADE attendu | Gain |
|-------|------------|------|
| v1 (actuel) | 4,419 m | — |
| + Données propres (SOG≥2, Cargo/Tanker/Passenger) | ~800 m | ×5.5 |
| + Déplacements relatifs + scaler corrigé | ~300 m | ×14 |
| + Nouvelles features (Δsog, Δcog, heading, heure) | ~200 m | ×22 |
| + Architecture v2 (PE + decoder + vessel embed) | ~150 m | ×29 |
| + Physics loss + Huber + augmentation | **~80-120 m** | **×37-55** |

> **Cible : ADE < 200 m** pour une prédiction à 10 min (horizon de 10 steps à 1 min/step)
> Cela correspond aux benchmarks SOTA pour des horizons courts.

---

## 8. Références

- [TrAISformer — arXiv:2109.03958](https://arxiv.org/abs/2109.03958)
- [AIS-LLM — arXiv:2508.07668](https://arxiv.org/html/2508.07668v1)
- [PINN for vessel trajectory — arXiv:2506.12029](https://arxiv.org/abs/2506.12029)
- [SEMINT (LLM + navigation intent) — Taylor&Francis 2025](https://www.tandfonline.com/doi/full/10.1080/13658816.2025.2487990)
- [AISFormer — ScienceDirect 2025](https://www.sciencedirect.com/science/article/abs/pii/S0029801825017822)
- [TPTrans — MDPI IJGI 2024](https://www.mdpi.com/2220-9964/13/11/400)
- [Physics-Informed Vessel Trajectory — ResearchSquare 2025](https://www.researchsquare.com/article/rs-8291452/v1)
- [AIS Data-Driven Maritime Review — arXiv:2505.07374](https://arxiv.org/html/2505.07374v1)

"""
AIS Trajectory Prediction Model Training with Multi-GPU Support
Optimized for ECO server (2x GPUs)
"""
import os
import math
import time
import argparse
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.nn.parallel import DataParallel
from torch.amp import autocast, GradScaler
from sqlalchemy import create_engine, text
from sklearn.model_selection import train_test_split

# Configuration
DB_CONFIG = {
    'host': '172.31.60.8',
    'port': 5432,
    'database': 'ais',
    'user': 'postgres',
    'password': 'ANjw/84H77C9h2'
}

# Hyperparamètres optimisés pour serveur ECO (1x NVIDIA L40S, 46GB VRAM)
SEQ_IN = 20
BATCH_SIZE = 1024  # Optimisé pour 1x L40S avec 46GB VRAM (meilleur que 2 GPUs)
EPOCHS = 50
LR = 1e-4
NUM_WORKERS = 16  # Optimisé pour serveur haute performance
PIN_MEMORY = True

# Configuration des splits
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Connexion DB
DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)


class AISTrajDataset(Dataset):
    """Dataset optimisé avec cache et préprocessing vectorisé"""
    
    def __init__(self, df, seq_len=SEQ_IN, feat_mean=None, feat_std=None):
        self.seq_len = seq_len
        self.X, self.Y = [], []
        
        print(f"   Création dataset à partir de {len(df):,} points...")
        
        # Grouper par trajectory_id (plus efficace que MMSI)
        for traj_id, g in df.groupby("trajectory_id"):
            g = g.sort_values("base_date_time")
            
            if len(g) < seq_len + 1:
                continue
            
            # Extraire features
            lat = g["LAT"].values
            lon = g["LON"].values
            sog = g["SOG"].values / 30.0  # Normalisation
            cog = np.deg2rad(g["COG"].values)
            
            # Conversion en coordonnées locales (métriques)
            lat0, lon0 = lat[0], lon[0]
            dx = (lat - lat0) * 111320.0
            dy = (lon - lon0) * 111320.0 * np.cos(np.deg2rad(lat0))

            # Empiler features: [dx, dy, sog, sin(cog), cos(cog)]
            feats = np.stack([dx, dy, sog, np.sin(cog), np.cos(cog)], axis=1).astype(np.float32)
            
            # Créer séquences avec fenêtre glissante
            for i in range(len(feats) - seq_len):
                self.X.append(feats[i:i+seq_len])
                self.Y.append(feats[i+1:i+seq_len+1])
        
        # Conversion en numpy array
        X = np.array(self.X)
        Y = np.array(self.Y)

        # Normalisation si stats fournies
        if feat_mean is not None and feat_std is not None:
            # ensure shapes
            mean = np.array(feat_mean).reshape(1, 1, -1)
            std = np.array(feat_std).reshape(1, 1, -1)
            X = (X - mean) / std
            Y = (Y - mean) / std

        # Conversion en tensors
        self.X = torch.from_numpy(X)
        self.Y = torch.from_numpy(Y)
        
        print(f"   → {len(self)} séquences créées")
    
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        return self.X[idx], self.Y[idx]


class LSTMTransformer(nn.Module):
    """Modèle hybride LSTM + Transformer optimisé"""
    
    def __init__(self, input_dim=5, hidden_dim=128, num_heads=8, num_layers=2, dropout=0.1):
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        
        # Embedding des features
        self.embed = nn.Linear(input_dim, hidden_dim)
        self.embed_dropout = nn.Dropout(dropout)
        
        # LSTM pour capturer les dépendances temporelles
        self.lstm = nn.LSTM(
            hidden_dim, 
            hidden_dim, 
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Transformer Encoder pour l'attention
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout,
            batch_first=True,
            norm_first=True  # Pre-LN pour meilleure stabilité
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Couche de sortie
        self.fc_out = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, input_dim)
        )
    
    def forward(self, x):
        # x: [batch, seq, features]
        batch_size, seq_len, _ = x.size()
        
        # Embedding
        x = self.embed(x)
        x = self.embed_dropout(x)
        
        # LSTM
        x, _ = self.lstm(x)
        
        # Transformer
        x = self.transformer(x)
        
        # Output
        x = self.fc_out(x)
        
        return x


def load_processed_from_db(split=None):
    """Charge les données prétraitées depuis PostgreSQL"""
    query = 'SELECT trajectory_id, mmsi, base_date_time, lat, lon, sog, cog, dataset_split FROM trajectory_processed'
    if split:
        query += f" WHERE dataset_split = '{split}'"
    query += ' ORDER BY trajectory_id, base_date_time'
    
    print(f"   Chargement {split or 'all'} depuis trajectory_processed...")
    df = pd.read_sql(query, engine)
    
    # Renommer pour compatibilité
    df.columns = ['trajectory_id', 'MMSI', 'base_date_time', 'LAT', 'LON', 'SOG', 'COG', 'dataset_split']
    
    print(f"   → {len(df):,} points, {df['trajectory_id'].nunique():,} trajectoires")
    return df


def compute_feature_stats(df, seq_len=SEQ_IN):
    """Compute mean and std of the 5 features across a dataframe (per-trajectory local coords).
    Returns (mean, std) as numpy arrays of shape (5,)
    """
    feats_list = []
    for traj_id, g in df.groupby("trajectory_id"):
        g = g.sort_values("base_date_time")
        if len(g) < 2:
            continue
        lat = g["LAT"].values
        lon = g["LON"].values
        sog = g["SOG"].values / 30.0
        cog = np.deg2rad(g["COG"].values)
        lat0, lon0 = lat[0], lon[0]
        dx = (lat - lat0) * 111320.0
        dy = (lon - lon0) * 111320.0 * np.cos(np.deg2rad(lat0))
        feats = np.stack([dx, dy, sog, np.sin(cog), np.cos(cog)], axis=1).astype(np.float32)
        feats_list.append(feats)

    if len(feats_list) == 0:
        raise RuntimeError("Aucune trajectoire valide pour calculer les statistiques")

    all_feats = np.concatenate(feats_list, axis=0)
    mean = all_feats.mean(axis=0)
    std = all_feats.std(axis=0)
    # avoid zero std
    std[std == 0] = 1.0
    return mean, std


def get_metrics(pred, true):
    """Calcule toutes les métriques d'évaluation"""
    # MSE et RMSE
    mse = ((pred - true) ** 2).mean().item()
    rmse = np.sqrt(mse)
    # MAE
    mae = torch.abs(pred - true).mean().item()

    # Extraire lat/lon (indices 0 et 1 correspondent à dx, dy)
    # On doit reconstruire les lat/lon absolues pour ADE/FDE
    # Pour simplification, on calcule l'erreur en mètres directement
    # ADE (Average Displacement Error) - moyenne sur toute la séquence
    dx_err = pred[:, :, 0] - true[:, :, 0]
    dy_err = pred[:, :, 1] - true[:, :, 1]
    dist = torch.sqrt(dx_err**2 + dy_err**2)
    ade = dist.mean().item()

    # Median ADE
    medade = dist.median().item()

    # FDE (Final Displacement Error) - erreur au dernier point
    fde = dist[:, -1].mean().item()

    # % of predictions under thresholds
    pct_under_10m = (dist < 10.0).float().mean().item() * 100.0
    pct_under_50m = (dist < 50.0).float().mean().item() * 100.0

    return {
        'mse': mse,
        'rmse': rmse,
        'mae': mae,
        'ade': ade,
        'medade': medade,
        'fde': fde,
        'pct_under_10m': pct_under_10m,
        'pct_under_50m': pct_under_50m
    }


def train_epoch(model, loader, optimizer, criterion, scaler, device):
    """Entraînement sur une epoch avec mixed precision"""
    model.train()
    total_loss = 0
    num_batches = len(loader)
    
    for batch_idx, (x, y) in enumerate(loader):
        x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)  # Plus efficace que zero_grad()

        # Safety checks for NaN/inf in inputs
        if torch.isnan(x).any() or torch.isnan(y).any() or torch.isinf(x).any() or torch.isinf(y).any():
            print(f"      ⚠ Batch {batch_idx+1}/{num_batches} contient NaN/inf dans les données — batch ignoré")
            continue

        # Mixed precision training (explicit device type to avoid warnings)
        amp_device = 'cuda' if device.type == 'cuda' else 'cpu'
        with autocast(device_type=amp_device):
            pred = model(x)
            loss = criterion(pred, y)

        # Detect non-finite loss and skip step if necessary
        if not torch.isfinite(loss):
            # print some diagnostics
            with torch.no_grad():
                pmin, pmax = float(pred.min().cpu()), float(pred.max().cpu())
                ymin, ymax = float(y.min().cpu()), float(y.max().cpu())
            print(f"      ⚠ Batch {batch_idx+1}/{num_batches} -> loss non fini (NaN/inf). pred range=({pmin:.3e},{pmax:.3e}), y range=({ymin:.3e},{ymax:.3e}) — réduction de l'échelle du scaler")
            # Update scaler to adjust scaling and skip optimizer step
            try:
                scaler.update()
            except Exception:
                pass
            continue

        # Backward pass avec gradient scaling
        scaler.scale(loss).backward()

        # Gradient clipping pour stabilité
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

        scaler.step(optimizer)
        scaler.update()

        total_loss += loss.item() * x.size(0)

        # Affichage progression
        if (batch_idx + 1) % 50 == 0:
            print(f"      Batch {batch_idx+1}/{num_batches} | Loss: {loss.item():.6f}")
    
    return total_loss / len(loader.dataset)


def validate(model, loader, criterion, device):
    """Validation avec calcul des métriques"""
    model.eval()
    total_loss = 0
    all_preds = []
    all_trues = []
    
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            # Safety checks
            if torch.isnan(x).any() or torch.isnan(y).any() or torch.isinf(x).any() or torch.isinf(y).any():
                print("      ⚠ Batch de validation contenant NaN/inf — batch ignoré")
                continue

            amp_device = 'cuda' if device.type == 'cuda' else 'cpu'
            with autocast(device_type=amp_device):
                pred = model(x)
                loss = criterion(pred, y)

            if not torch.isfinite(loss):
                print("      ⚠ Loss non fini (NaN/inf) pendant validation — batch ignoré")
                continue

            total_loss += loss.item() * x.size(0)

            all_preds.append(pred.cpu())
            all_trues.append(y.cpu())
    
    # Calculer métriques
    all_preds = torch.cat(all_preds)
    all_trues = torch.cat(all_trues)
    
    avg_loss = total_loss / len(loader.dataset)
    metrics = get_metrics(all_preds, all_trues)
    metrics['loss'] = avg_loss
    
    return metrics


def train_with_validation(model, train_loader, val_loader, device, epochs, save_dir='./models'):
    """Pipeline d'entraînement complet avec early stopping"""
    
    # Optimiseur avec weight decay pour régularisation
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    
    # Learning rate scheduler
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=3, verbose=True
    )
    
    # Loss function
    criterion = nn.MSELoss()
    
    # Mixed precision scaler
    scaler = GradScaler('cuda')
    
    # Early stopping
    best_val_loss = float('inf')
    patience = 5
    patience_counter = 0
    
    # Créer dossier de sauvegarde
    save_dir = Path(save_dir)
    save_dir.mkdir(exist_ok=True)
    
    # Historique d'entraînement
    history = {
        'train_loss': [],
        'val_loss': [],
        'val_ade': [],
        'val_fde': []
    }
    
    print("\n" + "="*70)
    print("DÉBUT DE L'ENTRAÎNEMENT")
    print("="*70)
    
    start_time = time.time()
    
    for epoch in range(epochs):
        epoch_start = time.time()
        
        # Entraînement
        print(f"\n[Epoch {epoch+1}/{epochs}] Entraînement...")
        train_loss = train_epoch(model, train_loader, optimizer, criterion, scaler, device)
        
        # Validation
        print(f"[Epoch {epoch+1}/{epochs}] Validation...")
        val_metrics = validate(model, val_loader, criterion, device)
        
        # Mise à jour scheduler
        scheduler.step(val_metrics['loss'])
        
        # Enregistrer historique
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_metrics['loss'])
        history['val_ade'].append(val_metrics['ade'])
        history['val_fde'].append(val_metrics['fde'])
        
        # Affichage
        epoch_time = time.time() - epoch_start
        print(f"[Epoch {epoch+1}/{epochs}] ({epoch_time:.1f}s)")
        print(f"   Train Loss: {train_loss:.6f}")
        print(f"   Val Loss:   {val_metrics['loss']:.6f}")
        print(f"   Val MAE:    {val_metrics.get('mae', float('nan')):.6f}")
        print(f"   Val ADE:    {val_metrics['ade']:.2f} m")
        print(f"   Val Median ADE: {val_metrics.get('medade', float('nan')):.2f} m")
        print(f"   Val FDE:    {val_metrics['fde']:.2f} m")
        print(f"   % <10m:     {val_metrics.get('pct_under_10m', 0.0):.2f}% | % <50m: {val_metrics.get('pct_under_50m', 0.0):.2f}%")
        print(f"   LR:         {optimizer.param_groups[0]['lr']:.2e}")
        
        # Sauvegarde du meilleur modèle
        if val_metrics['loss'] < best_val_loss:
            best_val_loss = val_metrics['loss']
            patience_counter = 0
            
            best_model_path = save_dir / 'best_model.pth'
            torch.save({
                'epoch': epoch + 1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': val_metrics['loss'],
                'val_ade': val_metrics['ade'],
                'val_fde': val_metrics['fde'],
                'history': history
            }, best_model_path)
            
            print(f"   ✓ Meilleur modèle sauvegardé: {best_model_path}")
        else:
            patience_counter += 1
            print(f"   Patience: {patience_counter}/{patience}")
        
        # Early stopping
        if patience_counter >= patience:
            print(f"\n⚠ Early stopping à l'epoch {epoch+1}")
            break
        
        # Checkpoint régulier
        if (epoch + 1) % 10 == 0:
            checkpoint_path = save_dir / f'checkpoint_epoch_{epoch+1}.pth'
            torch.save({
                'epoch': epoch + 1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'history': history
            }, checkpoint_path)
    
    total_time = time.time() - start_time
    
    print("\n" + "="*70)
    print(f"ENTRAÎNEMENT TERMINÉ en {total_time/60:.1f} minutes")
    print("="*70)
    
    # Charger le meilleur modèle
    best_checkpoint = torch.load(save_dir / 'best_model.pth')
    model.load_state_dict(best_checkpoint['model_state_dict'])
    
    return model, history


def evaluate_test(model, test_loader, device):
    """Évaluation finale sur le test set"""
    print("\n" + "="*70)
    print("ÉVALUATION SUR TEST SET")
    print("="*70)
    
    criterion = nn.MSELoss()
    metrics = validate(model, test_loader, criterion, device)
    
    print(f"\nRésultats Test Set:")
    print(f"   MSE:  {metrics['mse']:.6f}")
    print(f"   RMSE: {metrics['rmse']:.4f}")
    print(f"   MAE:  {metrics.get('mae', float('nan')):.6f}")
    print(f"   ADE:  {metrics['ade']:.2f} m")
    print(f"   Median ADE: {metrics.get('medade', float('nan')):.2f} m")
    print(f"   FDE:  {metrics['fde']:.2f} m")
    print(f"   % <10m: {metrics.get('pct_under_10m', 0.0):.2f}% | % <50m: {metrics.get('pct_under_50m', 0.0):.2f}%")
    
    return metrics


def main():
    parser = argparse.ArgumentParser(description='Train AIS Trajectory Prediction Model')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, help='Batch size (default: 1024 for 1x L40S)')
    parser.add_argument('--epochs', type=int, default=EPOCHS, help='Number of epochs')
    parser.add_argument('--lr', type=float, default=LR, help='Learning rate')
    parser.add_argument('--num-workers', type=int, default=NUM_WORKERS, help='Number of data loading workers (default: 16)')
    parser.add_argument('--save-dir', type=str, default='./models', help='Model save directory')
    parser.add_argument('--gpu-id', type=int, default=0, help='GPU ID to use (default: 0, use -1 for all GPUs)')
    args = parser.parse_args()
    
    # Configuration GPU
    if not torch.cuda.is_available():
        print("⚠ CUDA non disponible! Utilisation du CPU.")
        device = torch.device('cpu')
    else:
        if args.gpu_id >= 0:
            # Utiliser un GPU spécifique
            device = torch.device(f'cuda:{args.gpu_id}')
            torch.cuda.set_device(args.gpu_id)
            print(f"\n{'='*70}")
            print(f"CONFIGURATION GPU")
            print(f"{'='*70}")
            print(f"GPU utilisé: GPU {args.gpu_id}")
            print(f"   Nom: {torch.cuda.get_device_name(args.gpu_id)}")
            props = torch.cuda.get_device_properties(args.gpu_id)
            print(f"   Mémoire: {props.total_memory / 1e9:.1f} GB")
            print(f"   Compute capability: {props.major}.{props.minor}")
            print(f"{'='*70}\n")
        else:
            # Utiliser tous les GPUs disponibles
            device = torch.device('cuda')
            gpu_count = torch.cuda.device_count()
            print(f"\n{'='*70}")
            print(f"CONFIGURATION GPU")
            print(f"{'='*70}")
            print(f"GPUs disponibles: {gpu_count}")
            for i in range(gpu_count):
                print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
                print(f"      Mémoire: {torch.cuda.get_device_properties(i).total_memory / 1e9:.1f} GB")
            print(f"{'='*70}\n")
    
    # Chargement des données
    print("\n" + "="*70)
    print("CHARGEMENT DES DONNÉES")
    print("="*70)
    
    df_train = load_processed_from_db('train')
    df_val = load_processed_from_db('val')
    df_test = load_processed_from_db('test')

    # Compute feature normalization stats from train set and pass to datasets
    print("\nCalcul des statistiques de normalisation à partir du train set...")
    feat_mean, feat_std = compute_feature_stats(df_train, seq_len=SEQ_IN)
    print(f"   Feature mean: {feat_mean}")
    print(f"   Feature std:  {feat_std}")
    
    print(f"\nCréation des datasets...")
    train_dataset = AISTrajDataset(df_train, seq_len=SEQ_IN, feat_mean=feat_mean, feat_std=feat_std)
    val_dataset = AISTrajDataset(df_val, seq_len=SEQ_IN, feat_mean=feat_mean, feat_std=feat_std)
    test_dataset = AISTrajDataset(df_test, seq_len=SEQ_IN, feat_mean=feat_mean, feat_std=feat_std)
    
    print(f"\nRésumé datasets:")
    print(f"   Train: {len(train_dataset):,} séquences")
    print(f"   Val:   {len(val_dataset):,} séquences")
    print(f"   Test:  {len(test_dataset):,} séquences")
    
    # DataLoaders optimisés
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=PIN_MEMORY,
        persistent_workers=True if args.num_workers > 0 else False
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=PIN_MEMORY,
        persistent_workers=True if args.num_workers > 0 else False
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=PIN_MEMORY
    )
    
    # Création du modèle
    print("\n" + "="*70)
    print("CRÉATION DU MODÈLE")
    print("="*70)
    
    model = LSTMTransformer(
        input_dim=5,
        hidden_dim=128,
        num_heads=8,
        num_layers=2,
        dropout=0.1
    )
    
    # Compter les paramètres
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"Architecture: LSTMTransformer")
    print(f"Paramètres totaux: {total_params:,}")
    print(f"Paramètres entraînables: {trainable_params:,}")
    
    # Multi-GPU si args.gpu_id == -1
    if torch.cuda.is_available() and args.gpu_id < 0 and torch.cuda.device_count() > 1:
        print(f"\n✓ Utilisation de {torch.cuda.device_count()} GPUs avec DataParallel")
        model = DataParallel(model)
    elif torch.cuda.is_available() and args.gpu_id >= 0:
        print(f"\n✓ Utilisation du GPU {args.gpu_id} uniquement (mode single-GPU optimisé)")
    
    model = model.to(device)
    
    # Entraînement
    model, history = train_with_validation(
        model, 
        train_loader, 
        val_loader, 
        device,
        epochs=args.epochs,
        save_dir=args.save_dir
    )
    
    # Évaluation finale
    test_metrics = evaluate_test(model, test_loader, device)
    
    # Sauvegarde modèle final
    final_model_path = Path(args.save_dir) / f'ais_model_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pth'
    
    # Si multi-GPU, sauvegarder le modèle sous-jacent
    model_to_save = model.module if isinstance(model, DataParallel) else model
    
    torch.save({
        'model_state_dict': model_to_save.state_dict(),
        'test_metrics': test_metrics,
        'history': history,
        'config': {
            'seq_len': SEQ_IN,
            'batch_size': args.batch_size,
            'epochs': args.epochs,
            'lr': args.lr
        }
    }, final_model_path)
    
    print(f"\n✓ Modèle final sauvegardé: {final_model_path}")
    print("\n" + "="*70)
    print("ENTRAÎNEMENT COMPLET TERMINÉ!")
    print("="*70)


if __name__ == '__main__':
    main()

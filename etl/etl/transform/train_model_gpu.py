"""
AIS Trajectory Prediction Model Training with Multi-GPU Support
Optimized for ECO server with L40S GPU
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

# Hyperparameters optimized for ECO server (1x NVIDIA L40S, 46GB VRAM)
SEQ_IN = 20
BATCH_SIZE = 1024  # Optimized for 1x L40S with 46GB VRAM
EPOCHS = 50
LR = 1e-4
NUM_WORKERS = 16  # Optimized for high-performance server
PIN_MEMORY = True

# Dataset splits configuration
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Database connection
DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)


class AISTrajDataset(Dataset):
    """Optimized dataset with caching and vectorized preprocessing"""
    
    def __init__(self, df, seq_len=SEQ_IN, feat_mean=None, feat_std=None):
        self.seq_len = seq_len
        self.X, self.Y = [], []
        
        print(f"   Creating dataset from {len(df):,} points...")
        
        # Group by trajectory_id (more efficient than MMSI)
        for traj_id, g in df.groupby("trajectory_id"):
            g = g.sort_values("base_date_time")
            
            if len(g) < seq_len + 1:
                continue
            
            # Extract features
            lat = g["LAT"].values
            lon = g["LON"].values
            sog = g["SOG"].values / 30.0  # Normalization
            cog = np.deg2rad(g["COG"].values)
            
            # Convert to local metric coordinates
            lat0, lon0 = lat[0], lon[0]
            dx = (lat - lat0) * 111320.0
            dy = (lon - lon0) * 111320.0 * np.cos(np.deg2rad(lat0))

            # Stack features: [dx, dy, sog, sin(cog), cos(cog)]
            feats = np.stack([dx, dy, sog, np.sin(cog), np.cos(cog)], axis=1).astype(np.float32)
            
            # Create sequences with sliding window
            for i in range(len(feats) - seq_len):
                self.X.append(feats[i:i+seq_len])
                self.Y.append(feats[i+1:i+seq_len+1])
        
        # Convert to numpy array
        X = np.array(self.X)
        Y = np.array(self.Y)

        # Normalize if stats provided
        if feat_mean is not None and feat_std is not None:
            mean = np.array(feat_mean).reshape(1, 1, -1)
            std = np.array(feat_std).reshape(1, 1, -1)
            X = (X - mean) / std
            Y = (Y - mean) / std

        # Convert to tensors
        self.X = torch.from_numpy(X)
        self.Y = torch.from_numpy(Y)
        
        print(f"   Created {len(self)} sequences")
    
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        return self.X[idx], self.Y[idx]


class LSTMTransformer(nn.Module):
    """Optimized hybrid LSTM + Transformer model"""
    
    def __init__(self, input_dim=5, hidden_dim=128, num_heads=8, num_layers=2, dropout=0.1):
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        
        # Feature embedding
        self.embed = nn.Linear(input_dim, hidden_dim)
        self.embed_dropout = nn.Dropout(dropout)
        
        # LSTM to capture temporal dependencies
        self.lstm = nn.LSTM(
            hidden_dim, 
            hidden_dim, 
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Transformer Encoder for attention
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout,
            batch_first=True,
            norm_first=True  # Pre-LN for better stability
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Output layer
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
    """Load preprocessed data from PostgreSQL"""
    query = 'SELECT trajectory_id, mmsi, base_date_time, lat, lon, sog, cog, dataset_split FROM trajectory_processed'
    if split:
        query += f" WHERE dataset_split = '{split}'"
    query += ' ORDER BY trajectory_id, base_date_time'
    
    print(f"   Loading {split or 'all'} from trajectory_processed...")
    df = pd.read_sql(query, engine)
    
    # Rename for compatibility
    df.columns = ['trajectory_id', 'MMSI', 'base_date_time', 'LAT', 'LON', 'SOG', 'COG', 'dataset_split']
    
    print(f"   Loaded {len(df):,} points, {df['trajectory_id'].nunique():,} trajectories")
    return df


def compute_feature_stats(df, seq_len=SEQ_IN):
    """Compute mean and std of the 5 features across a dataframe.
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
        raise RuntimeError("No valid trajectories to compute statistics")

    all_feats = np.concatenate(feats_list, axis=0)
    mean = all_feats.mean(axis=0)
    std = all_feats.std(axis=0)
    # avoid zero std
    std[std == 0] = 1.0
    return mean, std


def get_metrics(pred, true):
    """Calculate all evaluation metrics"""
    # MSE and RMSE
    mse = ((pred - true) ** 2).mean().item()
    rmse = np.sqrt(mse)
    # MAE
    mae = torch.abs(pred - true).mean().item()

    # Extract lat/lon (indices 0 and 1 correspond to dx, dy)
    # Calculate error in meters directly
    # ADE (Average Displacement Error) - average over entire sequence
    dx_err = pred[:, :, 0] - true[:, :, 0]
    dy_err = pred[:, :, 1] - true[:, :, 1]
    dist = torch.sqrt(dx_err**2 + dy_err**2)
    ade = dist.mean().item()

    # Median ADE
    medade = dist.median().item()

    # FDE (Final Displacement Error) - error at last point
    fde = dist[:, -1].mean().item()

    # Percentage of predictions under thresholds
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
    """Training for one epoch with mixed precision"""
    model.train()
    total_loss = 0
    num_batches = len(loader)
    
    for batch_idx, (x, y) in enumerate(loader):
        x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)  # More efficient than zero_grad()

        # Safety checks for NaN/inf in inputs
        if torch.isnan(x).any() or torch.isnan(y).any() or torch.isinf(x).any() or torch.isinf(y).any():
            print(f"      WARNING: Batch {batch_idx+1}/{num_batches} contains NaN/inf - skipping")
            continue

        # Mixed precision training
        amp_device = 'cuda' if device.type == 'cuda' else 'cpu'
        with autocast(device_type=amp_device):
            pred = model(x)
            loss = criterion(pred, y)

        # Detect non-finite loss and skip step if necessary
        if not torch.isfinite(loss):
            with torch.no_grad():
                pmin, pmax = float(pred.min().cpu()), float(pred.max().cpu())
                ymin, ymax = float(y.min().cpu()), float(y.max().cpu())
            print(f"      WARNING: Batch {batch_idx+1}/{num_batches} loss is non-finite (pred:[{pmin:.3e},{pmax:.3e}], y:[{ymin:.3e},{ymax:.3e}]) - adjusting scaler")
            try:
                scaler.update()
            except Exception:
                pass
            continue

        # Backward pass with gradient scaling
        scaler.scale(loss).backward()

        # Gradient clipping for stability
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

        scaler.step(optimizer)
        scaler.update()

        total_loss += loss.item() * x.size(0)

        # Progress display
        if (batch_idx + 1) % 50 == 0:
            print(f"      Batch {batch_idx+1}/{num_batches} | Loss: {loss.item():.6f}")
    
    return total_loss / len(loader.dataset)


def validate(model, loader, criterion, device):
    """Validation with metrics calculation"""
    model.eval()
    total_loss = 0
    all_preds = []
    all_trues = []
    
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            # Safety checks
            if torch.isnan(x).any() or torch.isnan(y).any() or torch.isinf(x).any() or torch.isinf(y).any():
                print("      WARNING: Validation batch contains NaN/inf - skipping")
                continue

            amp_device = 'cuda' if device.type == 'cuda' else 'cpu'
            with autocast(device_type=amp_device):
                pred = model(x)
                loss = criterion(pred, y)

            if not torch.isfinite(loss):
                print("      WARNING: Non-finite loss in validation - skipping batch")
                continue

            total_loss += loss.item() * x.size(0)

            all_preds.append(pred.cpu())
            all_trues.append(y.cpu())
    
    # Calculate metrics
    all_preds = torch.cat(all_preds)
    all_trues = torch.cat(all_trues)
    
    avg_loss = total_loss / len(loader.dataset)
    metrics = get_metrics(all_preds, all_trues)
    metrics['loss'] = avg_loss
    
    return metrics


def train_with_validation(model, train_loader, val_loader, device, epochs, save_dir='./models'):
    """Complete training pipeline with early stopping"""
    
    # Optimizer with weight decay for regularization
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
    
    # Create save folder
    save_dir = Path(save_dir)
    save_dir.mkdir(exist_ok=True)
    
    # Training history
    history = {
        'train_loss': [],
        'val_loss': [],
        'val_ade': [],
        'val_fde': []
    }
    
    print("\n" + "="*70)
    print("START TRAINING")
    print("="*70)
    
    start_time = time.time()
    
    for epoch in range(epochs):
        epoch_start = time.time()
        
        # Training
        print(f"\n[Epoch {epoch+1}/{epochs}] Training...")
        train_loss = train_epoch(model, train_loader, optimizer, criterion, scaler, device)
        
        # Validation
        print(f"[Epoch {epoch+1}/{epochs}] Validation...")
        val_metrics = validate(model, val_loader, criterion, device)
        
        # Update scheduler
        scheduler.step(val_metrics['loss'])
        
        # Record history
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_metrics['loss'])
        history['val_ade'].append(val_metrics['ade'])
        history['val_fde'].append(val_metrics['fde'])
        
        # Display
        epoch_time = time.time() - epoch_start
        print(f"[Epoch {epoch+1}/{epochs}] ({epoch_time:.1f}s)")
        print(f"   Train Loss: {train_loss:.6f}")
        print(f"   Val Loss:   {val_metrics['loss']:.6f}")
        print(f"   Val MAE:    {val_metrics.get('mae', float('nan')):.6f}")
        print(f"   Val ADE:    {val_metrics['ade']:.2f} m")
        print(f"   Val Med ADE: {val_metrics.get('medade', float('nan')):.2f} m")
        print(f"   Val FDE:    {val_metrics['fde']:.2f} m")
        print(f"   % <10m:     {val_metrics.get('pct_under_10m', 0.0):.2f}% | % <50m: {val_metrics.get('pct_under_50m', 0.0):.2f}%")
        print(f"   LR:         {optimizer.param_groups[0]['lr']:.2e}")
        
        # Save best model
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
            
            print(f"   Best model saved: {best_model_path}")
        else:
            patience_counter += 1
            print(f"   Patience: {patience_counter}/{patience}")
        
        # Early stopping
        if patience_counter >= patience:
            print(f"\nEarly stopping at epoch {epoch+1}")
            break
        
        # Regular checkpoint
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
    print(f"TRAINING COMPLETED in {total_time/60:.1f} minutes")
    print("="*70)
    
    # Load best model
    best_checkpoint = torch.load(save_dir / 'best_model.pth')
    model.load_state_dict(best_checkpoint['model_state_dict'])
    
    return model, history


def evaluate_test(model, test_loader, device):
    """Final evaluation on test set"""
    print("\n" + "="*70)
    print("TEST SET EVALUATION")
    print("="*70)
    
    criterion = nn.MSELoss()
    metrics = validate(model, test_loader, criterion, device)
    
    print(f"\nTest Set Results:")
    print(f"   MSE:  {metrics['mse']:.6f}")
    print(f"   RMSE: {metrics['rmse']:.4f}")
    print(f"   MAE:  {metrics.get('mae', float('nan')):.6f}")
    print(f"   ADE:  {metrics['ade']:.2f} m")
    print(f"   Med ADE: {metrics.get('medade', float('nan')):.2f} m")
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
    
    # GPU Configuration
    if not torch.cuda.is_available():
        print("WARNING: CUDA not available! Using CPU.")
        device = torch.device('cpu')
    else:
        if args.gpu_id >= 0:
            # Use specific GPU
            device = torch.device(f'cuda:{args.gpu_id}')
            torch.cuda.set_device(args.gpu_id)
            print(f"\n{'='*70}")
            print(f"GPU CONFIGURATION")
            print(f"{'='*70}")
            print(f"Using GPU {args.gpu_id}: {torch.cuda.get_device_name(args.gpu_id)}")
            props = torch.cuda.get_device_properties(args.gpu_id)
            print(f"Memory: {props.total_memory / 1e9:.1f} GB")
            print(f"{'='*70}\n")
        else:
            # Use all available GPUs
            device = torch.device('cuda')
            gpu_count = torch.cuda.device_count()
            print(f"\n{'='*70}")
            print(f"GPU CONFIGURATION")
            print(f"{'='*70}")
            print(f"Available GPUs: {gpu_count}")
            for i in range(gpu_count):
                print(f"   GPU {i}: {torch.cuda.get_device_name(i)} ({torch.cuda.get_device_properties(i).total_memory / 1e9:.1f} GB)")
            print(f"{'='*70}\n")
    
    # Load data
    print("\n" + "="*70)
    print("DATA LOADING")
    print("="*70)
    
    df_train = load_processed_from_db('train')
    df_val = load_processed_from_db('val')
    df_test = load_processed_from_db('test')

    # Compute feature normalization stats from train set
    print("\nComputing normalization statistics from train set...")
    feat_mean, feat_std = compute_feature_stats(df_train, seq_len=SEQ_IN)
    print(f"   Feature mean: {feat_mean}")
    print(f"   Feature std:  {feat_std}")
    
    print(f"\nCreating datasets...")
    train_dataset = AISTrajDataset(df_train, seq_len=SEQ_IN, feat_mean=feat_mean, feat_std=feat_std)
    val_dataset = AISTrajDataset(df_val, seq_len=SEQ_IN, feat_mean=feat_mean, feat_std=feat_std)
    test_dataset = AISTrajDataset(df_test, seq_len=SEQ_IN, feat_mean=feat_mean, feat_std=feat_std)
    
    print(f"\nDataset summary:")
    print(f"   Train: {len(train_dataset):,} sequences")
    print(f"   Val:   {len(val_dataset):,} sequences")
    print(f"   Test:  {len(test_dataset):,} sequences")
    
    # DataLoaders optimized
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
    
    # Create model
    print("\n" + "="*70)
    print("MODEL CREATION")
    print("="*70)
    
    model = LSTMTransformer(
        input_dim=5,
        hidden_dim=128,
        num_heads=8,
        num_layers=2,
        dropout=0.1
    )
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"Architecture: LSTMTransformer")
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    
    # Multi-GPU if args.gpu_id == -1
    if torch.cuda.is_available() and args.gpu_id < 0 and torch.cuda.device_count() > 1:
        print(f"\nUsing {torch.cuda.device_count()} GPUs with DataParallel")
        model = DataParallel(model)
    elif torch.cuda.is_available() and args.gpu_id >= 0:
        print(f"\nUsing GPU {args.gpu_id} only (optimized single-GPU mode)")
    
    model = model.to(device)
    
    # Training
    model, history = train_with_validation(
        model, 
        train_loader, 
        val_loader, 
        device,
        epochs=args.epochs,
        save_dir=args.save_dir
    )
    
    # Final evaluation
    test_metrics = evaluate_test(model, test_loader, device)
    
    # Save final model
    final_model_path = Path(args.save_dir) / f'ais_model_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pth'
    
    # If multi-GPU, save underlying model
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
    
    print(f"\nFinal model saved: {final_model_path}")
    print("\n" + "="*70)
    print("TRAINING COMPLETE!")
    print("="*70)


if __name__ == '__main__':
    main()

""""""

AIS Trajectory Prediction ModuleAIS Trajectory Prediction Module



Usage:Usage:

    from ais_predictor import AISPredictor    from ais_predictor import AISPredictor

    predictor = AISPredictor("models/best_model.pth")    predictor = AISPredictor("models/best_model.pth")

    result = predictor.predict(mmsi="338000000", horizon_minutes=30)    result = predictor.predict(mmsi="338000000", horizon_minutes=30)

""""""



import numpy as npimport numpy as np

import torchimport torch

import torch.nn as nnimport torch.nn as nn

from sqlalchemy import create_enginefrom sqlalchemy import create_engine

import pandas as pdimport pandas as pd





class LSTMTransformer(nn.Module):class LSTMTransformer(nn.Module):

    """Hybrid LSTM + Transformer model"""    """Hybrid LSTM + Transformer model"""



    def __init__(self, input_dim=5, hidden_dim=128, num_heads=8, num_layers=2, dropout=0.1):    def __init__(self, input_dim=5, hidden_dim=128, num_heads=8, num_layers=2, dropout=0.1):

        super().__init__()        super().__init__()

        self.embed = nn.Linear(input_dim, hidden_dim)        self.embed = nn.Linear(input_dim, hidden_dim)

        self.embed_dropout = nn.Dropout(dropout)        self.embed_dropout = nn.Dropout(dropout)

        self.lstm = nn.LSTM(hidden_dim, hidden_dim, batch_first=True,         self.lstm = nn.LSTM(hidden_dim, hidden_dim, batch_first=True, 

                           dropout=dropout if num_layers > 1 else 0)                           dropout=dropout if num_layers > 1 else 0)

        encoder_layer = nn.TransformerEncoderLayer(        encoder_layer = nn.TransformerEncoderLayer(

            d_model=hidden_dim, nhead=num_heads, dim_feedforward=hidden_dim*4,            d_model=hidden_dim, nhead=num_heads, dim_feedforward=hidden_dim*4,

            dropout=dropout, batch_first=True, norm_first=True            dropout=dropout, batch_first=True, norm_first=True

        )        )

        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.fc_out = nn.Sequential(        self.fc_out = nn.Sequential(

            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),

            nn.Dropout(dropout), nn.Linear(hidden_dim, input_dim)            nn.Dropout(dropout), nn.Linear(hidden_dim, input_dim)

        )        )



    def forward(self, x):    def forward(self, x):

        x = self.embed_dropout(self.embed(x))        x = self.embed_dropout(self.embed(x))

        x, _ = self.lstm(x)        x, _ = self.lstm(x)

        x = self.transformer(x)        x = self.transformer(x)

        return self.fc_out(x)        return self.fc_out(x)





class AISPredictor:class AISPredictor:

    """Vessel trajectory predictor"""    """Vessel trajectory predictor"""



    FEAT_MEAN = np.array([9.17902344e+03, 6.18149365e+03, 6.64660275e-01,     FEAT_MEAN = np.array([9.17902344e+03, 6.18149365e+03, 6.64660275e-01, 

                          9.88708213e-02, 1.06762074e-01], dtype=np.float32)                          9.88708213e-02, 1.06762074e-01], dtype=np.float32)

    FEAT_STD = np.array([7.0434641e+04, 9.3020062e+04, 1.7018053e-01,     FEAT_STD = np.array([7.0434641e+04, 9.3020062e+04, 1.7018053e-01, 

                         7.0388573e-01, 6.9498688e-01], dtype=np.float32)                         7.0388573e-01, 6.9498688e-01], dtype=np.float32)

    SEQ_IN = 20    SEQ_IN = 20



    def __init__(self, model_path: str, db_url: str = None):    def __init__(self, model_path: str, db_url: str = None):

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.model = LSTMTransformer()

        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)        self.model = LSTMTransformer()

        self.model.load_state_dict(checkpoint['model_state_dict'])        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)

        self.model.to(self.device)        self.model.load_state_dict(checkpoint['model_state_dict'])

        self.model.eval()        self.model.to(self.device)

        self.engine = create_engine(db_url) if db_url else None        self.model.eval()



    def predict(self, mmsi: str = None, data: pd.DataFrame = None,         self.engine = create_engine(db_url) if db_url else None

                horizon_minutes: int = 30) -> dict:

        """    def predict(self, mmsi: str = None, data: pd.DataFrame = None, 

        Predict vessel future trajectory.                horizon_minutes: int = 30) -> dict:

        """

        Args:        Predict vessel future trajectory.

            mmsi: Vessel identifier (if data not provided)

            data: DataFrame with columns [lat, lon, sog, cog, timestamp]        Args:

            horizon_minutes: Prediction horizon in minutes            mmsi: Vessel identifier (if data not provided)

            data: DataFrame with columns [lat, lon, sog, cog, timestamp]

        Returns:            horizon_minutes: Prediction horizon in minutes

            dict with current_position and predictions list

        """        Returns:

        if data is None and mmsi:            dict with current_position and predictions list

            query = f"""        """

                SELECT lat, lon, sog, cog, base_date_time             data: DataFrame avec colonnes [lat, lon, sog, cog, timestamp] (optionnel)

                FROM trajectory_processed             horizon_minutes: Minutes de prédiction

                WHERE mmsi='{mmsi}' 

                ORDER BY base_date_time DESC         Returns:

                LIMIT 100            dict avec: current_position, predictions (list of {time, lat, lon, sog, cog})

            """        """

            data = pd.read_sql(query, self.engine).iloc[::-1]        # Récupérer les données

            data.columns = ['lat', 'lon', 'sog', 'cog', 'timestamp']        if data is None and mmsi:

            query = f"SELECT lat, lon, sog, cog, base_date_time FROM trajectory_processed WHERE mmsi='{mmsi}' ORDER BY base_date_time DESC LIMIT 100"

        if len(data) < self.SEQ_IN:            data = pd.read_sql(query, self.engine).iloc[::-1]

            return {"error": f"Insufficient data ({len(data)} < {self.SEQ_IN})"}            data.columns = ['lat', 'lon', 'sog', 'cog', 'timestamp']



        input_data = data.iloc[-self.SEQ_IN:]        if len(data) < self.SEQ_IN:

        lat0, lon0 = input_data.iloc[0][['lat', 'lon']]            return {"error": f"Pas assez de données ({len(data)} < {self.SEQ_IN})"}



        features = []        # Préparer les features

        for _, row in input_data.iterrows():        input_data = data.iloc[-self.SEQ_IN:]

            dx = (row['lat'] - lat0) * 111320.0        lat0, lon0 = input_data.iloc[0][['lat', 'lon']]

            dy = (row['lon'] - lon0) * 111320.0 * np.cos(np.radians(lat0))

            features.append([        features = []

                dx, dy, row['sog']/30.0,        for _, row in input_data.iterrows():

                np.sin(np.radians(row['cog'])),            dx = (row['lat'] - lat0) * 111320.0

                np.cos(np.radians(row['cog']))            dy = (row['lon'] - lon0) * 111320.0 * np.cos(np.radians(lat0))

            ])            features.append([dx, dy, row['sog']/30.0, np.sin(np.radians(row['cog'])), np.cos(np.radians(row['cog']))])



        features = np.array(features, dtype=np.float32)        features = np.array(features, dtype=np.float32)

        features_norm = (features - self.FEAT_MEAN) / self.FEAT_STD        features_norm = (features - self.FEAT_MEAN) / self.FEAT_STD



        X = torch.tensor(features_norm, dtype=torch.float32).unsqueeze(0).to(self.device)        # Prédire

        X = torch.tensor(features_norm, dtype=torch.float32).unsqueeze(0).to(self.device)

        with torch.no_grad():

            pred_norm = self.model(X).cpu().numpy()[0]        with torch.no_grad():

            pred_norm = self.model(X).cpu().numpy()[0]

        pred = pred_norm * self.FEAT_STD + self.FEAT_MEAN

        pred = pred_norm * self.FEAT_STD + self.FEAT_MEAN

        pred_lats = lat0 + pred[:, 0] / 111320.0

        pred_lons = lon0 + pred[:, 1] / (111320.0 * np.cos(np.radians(lat0)))        # Convertir en coordonnées

        pred_sogs = pred[:, 2] * 30.0        pred_lats = lat0 + pred[:, 0] / 111320.0

        pred_cogs = np.degrees(np.arctan2(pred[:, 3], pred[:, 4]))        pred_lons = lon0 + pred[:, 1] / (111320.0 * np.cos(np.radians(lat0)))

        pred_sogs = pred[:, 2] * 30.0

        timestamps = pd.to_datetime(input_data['timestamp'])        pred_cogs = np.degrees(np.arctan2(pred[:, 3], pred[:, 4]))

        avg_interval = (timestamps.iloc[-1] - timestamps.iloc[0]).total_seconds() / (len(timestamps) - 1)

        last_time = timestamps.iloc[-1]        # Timestamps

        timestamps = pd.to_datetime(input_data['timestamp'])

        n_points = min(len(pred_lats), int(horizon_minutes * 60 / avg_interval))        avg_interval = (timestamps.iloc[-1] - timestamps.iloc[0]).total_seconds() / (len(timestamps) - 1)

        last_time = timestamps.iloc[-1]

        return {

            "mmsi": mmsi,        n_points = min(len(pred_lats), int(horizon_minutes * 60 / avg_interval))

            "current_position": {

                "lat": float(input_data.iloc[-1]['lat']),         return {

                "lon": float(input_data.iloc[-1]['lon'])            "mmsi": mmsi,

            },            "current_position": {"lat": float(input_data.iloc[-1]['lat']), "lon": float(input_data.iloc[-1]['lon'])},

            "current_time": str(last_time),            "current_time": str(last_time),

            "predictions": [            "predictions": [

                {                {

                    "time": str(last_time + pd.Timedelta(seconds=avg_interval * (i+1))),                    "time": str(last_time + pd.Timedelta(seconds=avg_interval * (i+1))),

                    "lat": float(pred_lats[i]),                    "lat": float(pred_lats[i]),

                    "lon": float(pred_lons[i]),                    "lon": float(pred_lons[i]),

                    "sog": float(pred_sogs[i]),                    "sog": float(pred_sogs[i]),

                    "cog": float(pred_cogs[i])                    "cog": float(pred_cogs[i])

                }                }

                for i in range(n_points)                for i in range(n_points)

            ]            ]

        }        }


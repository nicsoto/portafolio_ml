#!/usr/bin/env python
"""
Numerai Tournament Submission Script

Entrena un modelo usando tu framework MLModel y lo sube a Numerai
para participar en el torneo.

Uso:
    # Primera vez (entrena y sube modelo)
    uv run python scripts/numerai_submission.py --train --upload
    
    # Solo predicciones diarias
    uv run python scripts/numerai_submission.py --predict
    
Requiere:
    - NUMERAI_PUBLIC_ID y NUMERAI_SECRET_KEY en .env
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ml import MLModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Numerai API credentials
NUMERAI_PUBLIC_ID = os.getenv("NUMERAI_PUBLIC_ID")
NUMERAI_SECRET_KEY = os.getenv("NUMERAI_SECRET_KEY")


def download_numerai_data(data_dir: Path = Path("data/numerai")):
    """Descarga datos del torneo Numerai."""
    from numerapi import NumerAPI
    
    napi = NumerAPI()
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("📥 Descargando datos de Numerai...")
    
    # Download current round data
    current_round = napi.get_current_round()
    logger.info(f"📊 Ronda actual: {current_round}")
    
    # Download training data (solo si no existe o es muy viejo)
    train_path = data_dir / "numerai_training_data.parquet"
    if not train_path.exists():
        logger.info("📥 Descargando datos de entrenamiento (puede tardar)...")
        napi.download_dataset("v5.2/train.parquet", str(train_path))
    else:
        logger.info("✅ Datos de entrenamiento ya existen")
    
    # Download live data (siempre actualizar)
    live_path = data_dir / "numerai_live_data.parquet"
    logger.info("📥 Descargando datos live...")
    napi.download_dataset("v5.2/live.parquet", str(live_path))
    
    # Download features metadata
    features_path = data_dir / "features.json"
    if not features_path.exists():
        napi.download_dataset("v5.0/features.json", str(features_path))
    
    return train_path, live_path


def train_numerai_model(
    train_path: Path,
    model_type: str = "lightgbm",
    target_col: str = "target",
    sample_frac: float = 1.0,
) -> MLModel:
    """
    Entrena un modelo para Numerai usando tu framework.
    
    Args:
        train_path: Path al archivo de entrenamiento
        model_type: Tipo de modelo (lightgbm, xgboost, random_forest)
        target_col: Columna target
        sample_frac: Fracción de datos a usar (0.0-1.0)
    """
    logger.info(f"📚 Cargando datos de entrenamiento desde {train_path}...")
    
    # Usar feature sets curados de features.json (en lugar de las primeras N por orden)
    import json
    features_json_path = train_path.parent / "features.json"
    if features_json_path.exists():
        with open(features_json_path) as f:
            feature_metadata = json.load(f)
        # "medium" es el mejor balance calidad/RAM. "small" si hay poca RAM.
        feature_cols = feature_metadata["feature_sets"].get("medium",
                       feature_metadata["feature_sets"].get("small", []))
        logger.info(f"📋 Feature set 'medium' de features.json: {len(feature_cols)} features")
    else:
        # Fallback: primeras 50 features (pero ya no debería pasar)
        import pyarrow.parquet as pq
        all_columns = pq.ParquetFile(train_path).schema_arrow.names
        feature_cols = [c for c in all_columns if c.startswith("feature_")][:50]
        logger.warning("⚠️  features.json no encontrado, usando primeras 50 features")
    
    columns_to_read = feature_cols + [target_col, "era"]
    
    # Verificar que las columnas existan en el parquet
    import pyarrow.parquet as pq
    available_cols = set(pq.ParquetFile(train_path).schema_arrow.names)
    columns_to_read = [c for c in columns_to_read if c in available_cols]
    feature_cols = [c for c in feature_cols if c in available_cols]
    
    logger.info(f"📉 Leyendo {len(feature_cols)} features curados...")
    
    # Leer solo columnas necesarias
    df = pd.read_parquet(train_path, columns=columns_to_read)
    
    # Era sampling (temporal) en lugar de random sampling
    if sample_frac < 1.0:
        all_eras = sorted(df["era"].unique())
        era_step = max(1, int(1.0 / sample_frac))
        sampled_eras = all_eras[::era_step]
        df = df[df["era"].isin(sampled_eras)]
        logger.info(f"📉 Era sampling (cada {era_step} eras): {len(df):,} filas ({len(sampled_eras)} eras)")
    
    logger.info(f"📊 Dataset: {len(df):,} filas, {len(df.columns)} columnas")
    
    # Identificar columnas de features (empiezan con 'feature_')
    feature_cols = [c for c in df.columns if c.startswith("feature_")]
    logger.info(f"🔢 Features: {len(feature_cols)}")
    
    # Preparar datos
    X = df[feature_cols]
    y = df[target_col]
    
    # Eliminar NaN
    valid_idx = ~y.isna()
    X = X[valid_idx]
    y = y[valid_idx]
    
    logger.info(f"✅ Datos válidos: {len(X):,} filas")
    
    # Para Numerai usamos LGBMRegressor directamente (es regresión, no clasificación)
    logger.info(f"🚀 Entrenando modelo LightGBM (Regressor)...")
    
    from lightgbm import LGBMRegressor
    import joblib
    
    model = LGBMRegressor(
        n_estimators=2000,
        learning_rate=0.005,
        max_depth=6,
        num_leaves=2**6 - 1,
        colsample_bytree=0.1,
        subsample=0.8,
        subsample_freq=1,       # Necesario para que subsample funcione
        reg_alpha=0.1,          # L1 regularization
        reg_lambda=1.0,         # L2 regularization
        min_child_samples=5000, # Evitar overfitting en hojas pequeñas
        n_jobs=-1,
        verbose=-1,
    )
    
    model.fit(X, y)
    
    logger.info("✅ Modelo entrenado exitosamente")
    
    # Guardar con joblib directamente
    return model, feature_cols


def generate_predictions(
    model,
    live_path: Path,
    feature_cols: list = None,
) -> pd.DataFrame:
    """
    Genera predicciones para los datos live de Numerai.
    """
    logger.info(f"📥 Cargando datos live desde {live_path}...")
    df = pd.read_parquet(live_path)
    
    logger.info(f"📊 Datos live: {len(df):,} filas")
    
    # Usar features del modelo si se proporcionan
    if feature_cols:
        available_features = [c for c in feature_cols if c in df.columns]
        X = df[available_features]
        logger.info(f"🔢 Usando {len(available_features)} features del modelo entrenado")
    else:
        feature_cols = [c for c in df.columns if c.startswith("feature_")]
        X = df[feature_cols]
    
    # Generar predicciones (predict para regresión)
    logger.info("🔮 Generando predicciones...")
    raw_predictions = model.predict(X)
    
    # Rank normalize: convierte a distribución uniforme [0, 1]
    # Numerai prefiere predicciones con distribución uniforme
    from scipy.stats import rankdata
    ranked = rankdata(raw_predictions, method="average")
    predictions = (ranked - 0.5) / len(ranked)
    logger.info(f"📊 Predicciones normalizadas: [{predictions.min():.4f}, {predictions.max():.4f}]")
    
    # Crear DataFrame de submission
    # Numerai v5.2 usa "id", versiones anteriores pueden usar row_id o índice
    if "id" in df.columns:
        id_col = df["id"]
    elif "row_id" in df.columns:
        id_col = df["row_id"]
    else:
        id_col = df.index
    
    submission = pd.DataFrame({
        "id": id_col,
        "prediction": predictions
    })
    
    logger.info(f"✅ Predicciones generadas: {len(submission):,} filas")
    
    return submission


def upload_predictions(submission: pd.DataFrame, model_id: str = None):
    """
    Sube las predicciones a Numerai.
    """
    from numerapi import NumerAPI
    
    if not NUMERAI_PUBLIC_ID or not NUMERAI_SECRET_KEY:
        logger.error("❌ Falta NUMERAI_PUBLIC_ID o NUMERAI_SECRET_KEY en .env")
        return
    
    napi = NumerAPI(
        public_id=NUMERAI_PUBLIC_ID,
        secret_key=NUMERAI_SECRET_KEY
    )
    
    # Guardar submission temporalmente
    submission_path = Path("data/numerai/submission.csv")
    submission.to_csv(submission_path, index=False)
    
    logger.info("📤 Subiendo predicciones a Numerai...")
    
    # Obtener model_id si no se proporciona
    if not model_id:
        models = napi.get_models()
        if models:
            model_id = list(models.keys())[0]
            logger.info(f"📌 Usando modelo: {model_id}")
        else:
            logger.error("❌ No hay modelos registrados en tu cuenta Numerai")
            return
    
    # Subir
    submission_id = napi.upload_predictions(str(submission_path), model_id=model_id)
    logger.info(f"✅ Predicciones subidas! ID: {submission_id}")


def main():
    parser = argparse.ArgumentParser(description="Numerai Tournament Submission")
    parser.add_argument("--train", action="store_true", help="Entrenar modelo")
    parser.add_argument("--predict", action="store_true", help="Generar predicciones")
    parser.add_argument("--upload", action="store_true", help="Subir predicciones")
    parser.add_argument("--model-type", default="lightgbm", 
                       choices=["lightgbm", "xgboost", "random_forest"],
                       help="Tipo de modelo")
    parser.add_argument("--model-path", default="models/numerai_model.pkl",
                       help="Path para guardar/cargar modelo")
    
    parser.add_argument("--sample", type=float, default=0.3,
                       help="Fracción de datos a usar (0.0-1.0), default 0.3 para ahorrar RAM")
    
    args = parser.parse_args()
    
    data_dir = Path("data/numerai")
    model_path = Path(args.model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Descargar datos
    train_path, live_path = download_numerai_data(data_dir)
    
    feature_cols = None
    
    # Entrenar modelo
    if args.train:
        import joblib
        model, feature_cols = train_numerai_model(train_path, model_type=args.model_type, sample_frac=args.sample)
        joblib.dump({"model": model, "features": feature_cols}, model_path)
        logger.info(f"💾 Modelo guardado en {model_path}")
    else:
        # Cargar modelo existente
        import joblib
        if not model_path.exists():
            logger.error(f"❌ Modelo no encontrado: {model_path}")
            logger.info("💡 Usa --train para entrenar un modelo primero")
            return
        saved = joblib.load(model_path)
        model = saved["model"]
        feature_cols = saved["features"]
        logger.info(f"📂 Modelo cargado desde {model_path}")
    
    # Generar predicciones
    if args.predict or args.upload:
        submission = generate_predictions(model, live_path, feature_cols)
        
        # Guardar submission
        submission_path = data_dir / f"submission_{datetime.now().strftime('%Y%m%d')}.csv"
        submission.to_csv(submission_path, index=False)
        logger.info(f"💾 Submission guardada en {submission_path}")
        
        # Subir si se solicita
        if args.upload:
            upload_predictions(submission)
    
    logger.info("🎉 ¡Proceso completado!")


if __name__ == "__main__":
    main()

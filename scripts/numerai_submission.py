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
        napi.download_dataset("v5.0/train.parquet", str(train_path))
    else:
        logger.info("✅ Datos de entrenamiento ya existen")
    
    # Download live data (siempre actualizar)
    live_path = data_dir / "numerai_live_data.parquet"
    logger.info("📥 Descargando datos live...")
    napi.download_dataset("v5.0/live.parquet", str(live_path))
    
    # Download features metadata
    features_path = data_dir / "features.json"
    if not features_path.exists():
        napi.download_dataset("v5.0/features.json", str(features_path))
    
    return train_path, live_path


def train_numerai_model(
    train_path: Path,
    model_type: str = "lightgbm",
    target_col: str = "target",
) -> MLModel:
    """
    Entrena un modelo para Numerai usando tu framework.
    
    Args:
        train_path: Path al archivo de entrenamiento
        model_type: Tipo de modelo (lightgbm, xgboost, random_forest)
        target_col: Columna target
    """
    logger.info(f"📚 Cargando datos de entrenamiento desde {train_path}...")
    df = pd.read_parquet(train_path)
    
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
    
    # Crear y entrenar modelo usando tu framework
    logger.info(f"🚀 Entrenando modelo {model_type}...")
    
    model = MLModel(model_type=model_type)
    
    # Para Numerai usamos parámetros específicos
    if model_type == "lightgbm":
        model.model_params = {
            "n_estimators": 2000,
            "learning_rate": 0.01,
            "max_depth": 5,
            "colsample_bytree": 0.1,
            "n_jobs": -1,
            "verbose": -1,
        }
    
    model.train(X, y)
    
    logger.info("✅ Modelo entrenado exitosamente")
    
    return model


def generate_predictions(
    model: MLModel,
    live_path: Path,
) -> pd.DataFrame:
    """
    Genera predicciones para los datos live de Numerai.
    """
    logger.info(f"📥 Cargando datos live desde {live_path}...")
    df = pd.read_parquet(live_path)
    
    logger.info(f"📊 Datos live: {len(df):,} filas")
    
    # Identificar features
    feature_cols = [c for c in df.columns if c.startswith("feature_")]
    X = df[feature_cols]
    
    # Generar predicciones
    logger.info("🔮 Generando predicciones...")
    predictions = model.predict_proba(X)
    
    # Crear DataFrame de submission
    submission = pd.DataFrame({
        "id": df["id"],
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
    
    args = parser.parse_args()
    
    data_dir = Path("data/numerai")
    model_path = Path(args.model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Descargar datos
    train_path, live_path = download_numerai_data(data_dir)
    
    # Entrenar modelo
    if args.train:
        model = train_numerai_model(train_path, model_type=args.model_type)
        model.save(model_path)
        logger.info(f"💾 Modelo guardado en {model_path}")
    else:
        # Cargar modelo existente
        if not model_path.exists():
            logger.error(f"❌ Modelo no encontrado: {model_path}")
            logger.info("💡 Usa --train para entrenar un modelo primero")
            return
        model = MLModel.load(model_path)
        logger.info(f"📂 Modelo cargado desde {model_path}")
    
    # Generar predicciones
    if args.predict or args.upload:
        submission = generate_predictions(model, live_path)
        
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

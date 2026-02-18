#!/usr/bin/env python
"""
Numerai Round Submission
Descarga datos live, genera predicciones y sube a Numerai.

Soporta tanto el modelo v2 legacy como el ensemble v3.

Uso:
    # Con modelo v3 ensemble (recomendado)
    uv run python scripts/numerai_round.py --model models/numerai_v3_ensemble.pkl

    # Con modelo v2 legacy
    uv run python scripts/numerai_round.py --model models/modelo_v2.pkl --legacy

    # Default (intenta v3, si no existe usa v2)
    uv run python scripts/numerai_round.py
"""

import os
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from dotenv import load_dotenv
import numerapi
import cloudpickle

load_dotenv()

# Configuración
DATA_DIR = Path("data/numerai")
MODEL_V3_PATH = Path("models/numerai_v3_ensemble.pkl")
MODEL_V2_PATH = Path("models/modelo_v2.pkl")
MODEL_NAME = "trad_bot_v4"


def rank_normalize(predictions: np.ndarray) -> np.ndarray:
    """Normaliza predicciones a distribución uniforme [0, 1] usando ranking."""
    ranked = rankdata(predictions, method="average")
    return (ranked - 0.5) / len(ranked)


def neutralize_features(
    predictions: pd.Series,
    features: pd.DataFrame,
    proportion: float = 0.5,
) -> pd.Series:
    """Neutraliza predicciones respecto a features para reducir exposure."""
    features_centered = features - features.mean()
    exposures = np.linalg.lstsq(features_centered.values, predictions.values, rcond=None)[0]
    neutralized = predictions.values - proportion * (features_centered.values @ exposures)
    return pd.Series(neutralized, index=predictions.index)


def predict_v3(model_path: Path, live: pd.DataFrame) -> np.ndarray:
    """Genera predicciones con modelo v3 ensemble."""
    with open(model_path, "rb") as f:
        result = cloudpickle.load(f)

    models = result["models"]
    feature_cols = result["feature_cols"]
    available = [c for c in feature_cols if c in live.columns]
    print(f"✅ Ensemble v3 cargado ({len(models)} modelos, {len(available)} features)")

    X = live[available]
    all_preds = pd.DataFrame(index=live.index)

    for target_name, model in models.items():
        raw = model.predict(X)
        all_preds[target_name] = rank_normalize(raw)
        print(f"   ✅ Predicción '{target_name}' generada")

    ensemble = all_preds.mean(axis=1)

    # Feature neutralization
    if result.get("use_neutralization", False):
        neut_features = result.get("neutralization_features", feature_cols[:50])
        neut_features = [f for f in neut_features if f in live.columns]
        proportion = result.get("neutralization_proportion", 0.5)
        print(f"🔄 Neutralizando con {len(neut_features)} features...")
        neut_df = live[neut_features].fillna(0.5)
        ensemble = neutralize_features(
            pd.Series(ensemble.values, index=live.index), neut_df, proportion
        )

    return rank_normalize(ensemble.values)


def predict_v2(model_path: Path, live: pd.DataFrame) -> np.ndarray:
    """Genera predicciones con modelo v2 legacy (con rank normalization)."""
    with open(model_path, "rb") as f:
        wrapper = cloudpickle.load(f)

    available = [f for f in wrapper.features if f in live.columns]
    print(f"✅ Modelo v2 cargado ({len(available)} features)")

    raw_preds = wrapper.model.predict(live[available])
    # FIX: rank normalize (el v2 original no lo hacía)
    return rank_normalize(raw_preds)


def main():
    parser = argparse.ArgumentParser(description="Numerai Round Submission")
    parser.add_argument("--model", type=str, default=None, help="Path al modelo")
    parser.add_argument("--legacy", action="store_true", help="Forzar modo v2 legacy")
    parser.add_argument("--model-name", default=MODEL_NAME, help="Nombre del modelo en Numerai")
    parser.add_argument("--no-upload", action="store_true", help="No subir, solo generar CSV")
    args = parser.parse_args()

    print("🚀 Numerai Round Submission")
    print("=" * 50)

    # 1. Descargar live data
    print("\n📥 Descargando datos live...")
    napi = numerapi.NumerAPI()
    current_round = napi.get_current_round()
    print(f"📊 Ronda actual: {current_round}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    live_path = DATA_DIR / "live.parquet"
    napi.download_dataset("v5.2/live.parquet", str(live_path))
    print("✅ Datos descargados")

    live = pd.read_parquet(live_path)
    print(f"📊 Datos live: {len(live):,} filas")

    # 2. Determinar qué modelo usar
    if args.model:
        model_path = Path(args.model)
    elif MODEL_V3_PATH.exists() and not args.legacy:
        model_path = MODEL_V3_PATH
    elif MODEL_V2_PATH.exists():
        model_path = MODEL_V2_PATH
        args.legacy = True
    else:
        print("❌ No se encontró ningún modelo. Entrenalo primero con:")
        print("   uv run python scripts/numerai_train_v3.py --train")
        return

    print(f"\n📂 Cargando modelo: {model_path}")

    # 3. Generar predicciones
    print("\n🔮 Generando predicciones...")
    if args.legacy:
        predictions = predict_v2(model_path, live)
    else:
        predictions = predict_v3(model_path, live)

    submission = pd.DataFrame({
        "id": live.index if "id" not in live.columns else live["id"],
        "prediction": predictions,
    })

    print(f"✅ Predicciones: {len(submission):,} filas")
    print(f"   Rango: [{predictions.min():.4f}, {predictions.max():.4f}]")
    print(f"   Media: {predictions.mean():.4f} | Std: {predictions.std():.4f}")

    # 4. Guardar
    submission_path = DATA_DIR / f"submission_round_{current_round}.csv"
    submission.to_csv(submission_path, index=False)
    print(f"💾 Guardado: {submission_path}")

    # 5. Subir a Numerai
    if args.no_upload:
        print("\n⏭️  Upload desactivado (--no-upload)")
        return

    PUBLIC_ID = os.getenv("NUMERAI_PUBLIC_ID")
    SECRET_KEY = os.getenv("NUMERAI_SECRET_KEY")

    if not PUBLIC_ID or not SECRET_KEY:
        print("\n⚠️  Sin credenciales en .env — subilo manualmente")
        return

    print(f"\n📤 Subiendo a {args.model_name}...")
    napi_auth = numerapi.NumerAPI(public_id=PUBLIC_ID, secret_key=SECRET_KEY)

    models = napi_auth.get_models()
    model_uuid = models.get(args.model_name)

    if not model_uuid:
        print(f"❌ Modelo '{args.model_name}' no encontrado")
        print(f"   Modelos disponibles: {list(models.keys())}")
        return

    submission_id = napi_auth.upload_predictions(str(submission_path), model_id=model_uuid)
    print(f"\n🎉 ¡Subido exitosamente!")
    print(f"   Submission ID: {submission_id}")
    print(f"   Revisá en: https://numer.ai/models")


if __name__ == "__main__":
    main()

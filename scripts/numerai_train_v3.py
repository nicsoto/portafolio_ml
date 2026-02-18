#!/usr/bin/env python
"""
Numerai Model Training V3 — Script mejorado de entrenamiento y submission.

Mejoras respecto a V2:
  1. Feature sets curados desde features.json (no las primeras N al azar)
  2. Era sampling temporal (cada N eras, no random)
  3. Ensemble multi-target (entrena en varios targets, promedia)
  4. Rank normalization de predicciones (distribución uniforme [0,1])
  5. Feature neutralization para reducir exposure y crowding
  6. Fix subsample_freq (el v2 lo tenía en 0, ignorando subsample)
  7. Regularización L1/L2
  8. Validación con embargo antes de subir
  9. Métricas per-era (CORR, Sharpe) para evaluar antes del upload

Uso:
    # Entrenar modelo mejorado
    uv run python scripts/numerai_train_v3.py --train

    # Entrenar + generar predicciones + subir
    uv run python scripts/numerai_train_v3.py --train --predict --upload

    # Solo predecir con modelo ya entrenado
    uv run python scripts/numerai_train_v3.py --predict --upload

    # Entrenar con feature set específico
    uv run python scripts/numerai_train_v3.py --train --feature-set medium --era-step 4

Requiere:
    - data/numerai/numerai_training_data.parquet (descargar con numerai_submission.py)
    - data/numerai/features.json
    - NUMERAI_PUBLIC_ID y NUMERAI_SECRET_KEY en .env (para upload)
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd
import numpy as np
from scipy.stats import rankdata
from dotenv import load_dotenv

# Setup
sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Configuración ──────────────────────────────────────────────────────
DATA_DIR = Path("data/numerai")
MODELS_DIR = Path("models")
FEATURES_JSON = DATA_DIR / "features.json"
TRAIN_PATH = DATA_DIR / "numerai_training_data.parquet"
LIVE_PATH = DATA_DIR / "live.parquet"

# Targets para ensemble (diversificar reduce crowding)
ENSEMBLE_TARGETS = [
    "target",                # target principal
    "target_cyrusd_20",      # targets alternativos de 20 días
    "target_ralph_20",
    "target_waldo_20",
    "target_victor_20",
]

# Hiperparámetros mejorados
DEFAULT_LGB_PARAMS = {
    "n_estimators": 2000,
    "learning_rate": 0.005,
    "max_depth": 6,
    "num_leaves": 2**6 - 1,       # 63, coherente con max_depth=6
    "colsample_bytree": 0.1,
    "subsample": 0.8,
    "subsample_freq": 1,           # FIX: era 0 en v2, lo que ignoraba subsample
    "reg_alpha": 0.1,              # L1 regularization (nuevo)
    "reg_lambda": 1.0,             # L2 regularization (nuevo)
    "min_child_samples": 5000,     # Evitar overfitting en hojas pequeñas
    "n_jobs": -1,
    "verbosity": -1,
}


# ── Utilidades ─────────────────────────────────────────────────────────

def load_feature_sets() -> dict:
    """Carga los feature sets curados de Numerai."""
    if not FEATURES_JSON.exists():
        raise FileNotFoundError(
            f"No se encuentra {FEATURES_JSON}. "
            "Ejecutá primero: uv run python scripts/numerai_submission.py (para descargar datos)"
        )
    with open(FEATURES_JSON) as f:
        meta = json.load(f)
    return meta["feature_sets"]


def rank_normalize(predictions: np.ndarray) -> np.ndarray:
    """
    Normaliza predicciones a distribución uniforme [0, 1] usando ranking.

    Numerai prefiere predicciones con distribución uniforme.
    Esto también asegura que los valores estén en [0, 1].
    """
    ranked = rankdata(predictions, method="average")
    # Mapear a (0, 1) abierto para evitar exactamente 0 y 1
    return (ranked - 0.5) / len(ranked)


def neutralize_features(
    predictions: pd.Series,
    features: pd.DataFrame,
    proportion: float = 0.5,
) -> pd.Series:
    """
    Neutraliza las predicciones respecto a los features.

    Esto reduce el feature exposure, lo que reduce crowding con otros
    modelos (MCWNM baja) y mejora MMC.

    Funciona haciendo regresión lineal de predictions ~ features y
    quedándose con los residuos.

    Args:
        predictions: Predicciones del modelo.
        features: DataFrame de features a neutralizar.
        proportion: Qué tanto neutralizar (0=nada, 1=completamente).

    Returns:
        Predicciones neutralizadas.
    """
    # Normalizar features a media 0
    features_centered = features - features.mean()

    # Regresión: predictions = features @ beta + residuals
    # Usamos pseudo-inversa para estabilidad numérica
    exposures = np.linalg.lstsq(features_centered.values, predictions.values, rcond=None)[0]

    # Restar la parte explicada por los features (proporcionalmente)
    neutralized = predictions.values - proportion * (features_centered.values @ exposures)

    return pd.Series(neutralized, index=predictions.index)


def compute_per_era_corr(df: pd.DataFrame, pred_col: str = "prediction", target_col: str = "target") -> pd.Series:
    """
    Calcula correlación per-era (métrica principal de Numerai).

    Usa correlación de Spearman por era, que es lo más cercano
    a lo que Numerai calcula internamente.
    """
    def _era_corr(group):
        if group[pred_col].nunique() < 2 or group[target_col].nunique() < 2:
            return 0.0
        return group[[pred_col, target_col]].corr(method="spearman").iloc[0, 1]

    return df.groupby("era").apply(_era_corr, include_groups=False)


# ── Clase Callable para Numerai ────────────────────────────────────────

class NumeraiEnsembleModel:
    """
    Wrapper callable para subir a Numerai como modelo pickle.

    Numerai espera un objeto callable que acepte:
        (live_features: pd.DataFrame, live_benchmark_models: pd.DataFrame) -> pd.DataFrame

    Esta clase encapsula:
    - Múltiples modelos LightGBM (uno por target)
    - Rank normalization
    - Feature neutralization
    """

    def __init__(
        self,
        models: dict,
        feature_cols: list,
        targets: list,
        use_neutralization: bool = True,
        neutralization_proportion: float = 0.5,
        neutralization_features: list = None,
    ):
        self.models = models
        self.feature_cols = list(feature_cols)
        self.targets = list(targets)
        self.use_neutralization = use_neutralization
        self.neutralization_proportion = neutralization_proportion
        self.neutralization_features = list(neutralization_features or feature_cols[:50])

    def __call__(self, live_features: pd.DataFrame, live_benchmark_models: pd.DataFrame = None) -> pd.DataFrame:
        """
        Genera predicciones. Firma compatible con Numerai.

        Args:
            live_features: DataFrame con features del live round.
            live_benchmark_models: DataFrame con benchmark models (no usado).

        Returns:
            DataFrame con columna 'prediction' e índice = live_features.index.
        """
        from scipy.stats import rankdata

        available = [c for c in self.feature_cols if c in live_features.columns]
        X = live_features[available]

        # Predicción por modelo (uno por target)
        all_preds = pd.DataFrame(index=live_features.index)
        for target_name, model in self.models.items():
            raw = model.predict(X)
            ranked = rankdata(raw, method="average")
            all_preds[target_name] = (ranked - 0.5) / len(ranked)

        # Ensemble: promedio
        ensemble = all_preds.mean(axis=1)

        # Feature neutralization
        if self.use_neutralization:
            neut_feats = [f for f in self.neutralization_features if f in live_features.columns]
            if neut_feats:
                feat_df = live_features[neut_feats].fillna(0.5)
                feat_centered = feat_df - feat_df.mean()
                exposures = np.linalg.lstsq(
                    feat_centered.values, ensemble.values, rcond=None
                )[0]
                ensemble = ensemble.values - self.neutralization_proportion * (
                    feat_centered.values @ exposures
                )
                ensemble = pd.Series(ensemble, index=live_features.index)

        # Rank normalize final
        final = rankdata(ensemble.values, method="average")
        final = (final - 0.5) / len(final)

        return pd.DataFrame(final, index=live_features.index, columns=["prediction"])


# ── Entrenamiento ──────────────────────────────────────────────────────

def train_ensemble(
    feature_set_name: str = "medium",
    era_step: int = 4,
    targets: Optional[list] = None,
    lgb_params: Optional[dict] = None,
) -> dict:
    """
    Entrena un ensemble de modelos con múltiples targets.

    Args:
        feature_set_name: Nombre del feature set ('small', 'medium', 'all', etc.)
        era_step: Samplear cada N eras (4 = 25% de los datos)
        targets: Lista de targets para entrenar. None = ENSEMBLE_TARGETS
        lgb_params: Parámetros de LightGBM. None = DEFAULT_LGB_PARAMS

    Returns:
        dict con modelos entrenados, features, y métricas de validación.
    """
    from lightgbm import LGBMRegressor

    targets = targets or ENSEMBLE_TARGETS
    lgb_params = lgb_params or DEFAULT_LGB_PARAMS

    # 1. Cargar feature set
    logger.info("📋 Cargando feature sets...")
    feature_sets = load_feature_sets()

    if feature_set_name not in feature_sets:
        available = list(feature_sets.keys())
        raise ValueError(f"Feature set '{feature_set_name}' no existe. Disponibles: {available}")

    feature_cols = feature_sets[feature_set_name]
    logger.info(f"✅ Feature set '{feature_set_name}': {len(feature_cols)} features")

    # 2. Cargar datos de entrenamiento (solo columnas necesarias)
    columns_to_read = ["era", "data_type"] + feature_cols + targets
    # Filtrar targets que existan en el dataset
    import pyarrow.parquet as pq
    available_cols = set(pq.ParquetFile(TRAIN_PATH).schema_arrow.names)
    columns_to_read = [c for c in columns_to_read if c in available_cols]
    targets = [t for t in targets if t in available_cols]

    logger.info(f"📥 Cargando datos ({len(columns_to_read)} columnas)...")
    df = pd.read_parquet(TRAIN_PATH, columns=columns_to_read)
    logger.info(f"   Total: {len(df):,} filas")

    # 3. Separar train vs validation
    train_df = df[df["data_type"] == "train"].copy()
    val_df = df[df["data_type"] == "validation"].copy()

    if len(val_df) == 0:
        # Si no hay data_type, usar últimas N eras como validación
        all_eras = sorted(df["era"].unique())
        val_eras = all_eras[-100:]  # últimas 100 eras (~2 años)
        train_df = df[~df["era"].isin(val_eras)].copy()
        val_df = df[df["era"].isin(val_eras)].copy()

    logger.info(f"   Train: {len(train_df):,} filas | Val: {len(val_df):,} filas")

    # 4. Era sampling para training (reduce RAM y overfitting)
    train_eras = sorted(train_df["era"].unique())
    sampled_eras = train_eras[::era_step]
    train_df = train_df[train_df["era"].isin(sampled_eras)]
    logger.info(f"   Era sampling ({era_step}): {len(train_df):,} filas ({len(sampled_eras)} eras)")

    # Era sampling para validación también (para ahorrar RAM)
    val_eras_list = sorted(val_df["era"].unique())
    val_sampled = val_eras_list[::era_step]
    val_df = val_df[val_df["era"].isin(val_sampled)]
    logger.info(f"   Val sampling ({era_step}): {len(val_df):,} filas ({len(val_sampled)} eras)")

    # 5. Embargo: remover las primeras 4 eras de validación para evitar data leakage
    # (el target mira 20 días / 4 semanas adelante)
    last_train_era = int(sampled_eras[-1])
    embargo_eras = [str(last_train_era + i).zfill(4) for i in range(4)]
    val_df = val_df[~val_df["era"].isin(embargo_eras)]
    logger.info(f"   Post-embargo: {len(val_df):,} filas de validación")

    # Verificar que feature_cols existan en el dataframe
    feature_cols = [c for c in feature_cols if c in train_df.columns]
    logger.info(f"   Features disponibles: {len(feature_cols)}")

    # Liberar memoria
    del df

    # 6. Entrenar un modelo por target
    models = {}
    val_predictions = pd.DataFrame(index=val_df.index)

    for target_name in targets:
        logger.info(f"\n🚀 Entrenando modelo para '{target_name}'...")

        # Filtrar NaN en target
        train_valid = train_df[~train_df[target_name].isna()]
        val_valid_mask = ~val_df[target_name].isna()

        X_train = train_valid[feature_cols]
        y_train = train_valid[target_name]

        logger.info(f"   Datos: {len(X_train):,} filas")

        model = LGBMRegressor(**lgb_params)
        model.fit(X_train, y_train)

        models[target_name] = model
        logger.info(f"   ✅ Modelo entrenado para '{target_name}'")

        # Validación per-era
        X_val = val_df[feature_cols]
        raw_preds = model.predict(X_val)
        val_predictions[target_name] = rank_normalize(raw_preds)

    # 7. Ensemble: promedio de las predicciones normalizadas
    logger.info(f"\n📊 Creando ensemble de {len(models)} modelos...")
    ensemble_preds = val_predictions.mean(axis=1)
    val_df = val_df.copy()
    val_df["prediction"] = rank_normalize(ensemble_preds.values)

    # 8. Feature neutralization
    logger.info("🔄 Aplicando feature neutralization...")
    # Usar un subset de features para neutralizar (los más importantes)
    neut_features = feature_cols[:50]  # top features por orden
    neut_feat_df = val_df[neut_features].fillna(0.5)
    val_df["prediction_neutral"] = rank_normalize(
        neutralize_features(
            val_df["prediction"],
            neut_feat_df,
            proportion=0.5,
        ).values
    )

    # 9. Evaluar en validación
    logger.info("\n" + "=" * 60)
    logger.info("📈 MÉTRICAS DE VALIDACIÓN")
    logger.info("=" * 60)

    for pred_col, label in [("prediction", "Ensemble"), ("prediction_neutral", "Ensemble+Neutral")]:
        if "target" in val_df.columns:
            per_era = compute_per_era_corr(val_df, pred_col=pred_col, target_col="target")
            mean_corr = per_era.mean()
            std_corr = per_era.std(ddof=0)
            sharpe = mean_corr / std_corr if std_corr > 0 else 0
            max_dd = (per_era.cumsum().expanding().max() - per_era.cumsum()).max()

            logger.info(f"\n  {label}:")
            logger.info(f"    Mean CORR:    {mean_corr:.4f}")
            logger.info(f"    Std CORR:     {std_corr:.4f}")
            logger.info(f"    Sharpe:       {sharpe:.2f}")
            logger.info(f"    Max Drawdown: {max_dd:.4f}")

            # Feature exposure (correlación media entre predicciones y features)
            pred_series = val_df[pred_col]
            exposures = []
            for fc in feature_cols[:100]:  # muestra de features
                if fc in val_df.columns:
                    corr = pred_series.corr(val_df[fc])
                    if not np.isnan(corr):
                        exposures.append(abs(corr))
            if exposures:
                logger.info(f"    Feature Exp:  {np.mean(exposures):.4f} (max: {np.max(exposures):.4f})")

    # 10. Construir resultado
    result = {
        "models": models,
        "feature_cols": feature_cols,
        "targets": targets,
        "feature_set_name": feature_set_name,
        "lgb_params": lgb_params,
        "era_step": era_step,
        "trained_at": datetime.now().isoformat(),
        "use_neutralization": True,
        "neutralization_proportion": 0.5,
        "neutralization_features": neut_features,
    }

    # Crear objeto callable para Numerai
    result["callable"] = NumeraiEnsembleModel(
        models=models,
        feature_cols=feature_cols,
        targets=targets,
        use_neutralization=True,
        neutralization_proportion=0.5,
        neutralization_features=neut_features,
    )

    return result


def save_ensemble(result: dict, path: Path):
    """
    Guarda el ensemble en dos formatos:
    1. {path}          → dict completo (para uso local con numerai_round.py)
    2. {path_callable}  → objeto callable (para upload a Numerai)
    """
    import cloudpickle

    path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Guardar dict completo (uso local)
    with open(path, "wb") as f:
        cloudpickle.dump(result, f)
    size_mb = path.stat().st_size / 1024 / 1024
    logger.info(f"💾 Modelo local guardado: {path} ({size_mb:.1f} MB)")

    # 2. Guardar callable para upload a Numerai
    callable_path = path.with_name(path.stem + "_callable.pkl")
    callable_model = result["callable"]
    with open(callable_path, "wb") as f:
        cloudpickle.dump(callable_model, f)
    size_mb = callable_path.stat().st_size / 1024 / 1024
    logger.info(f"💾 Modelo callable guardado: {callable_path} ({size_mb:.1f} MB)")
    logger.info(f"   ⬆️  Este es el archivo que debés subir a Numerai")


def load_ensemble(path: Path) -> dict:
    """Carga un ensemble guardado."""
    import cloudpickle

    with open(path, "rb") as f:
        result = cloudpickle.load(f)
    logger.info(f"📂 Modelo cargado: {path}")
    logger.info(f"   Targets: {result.get('targets', ['unknown'])}")
    logger.info(f"   Features: {len(result.get('feature_cols', []))}")
    return result


# ── Predicción ─────────────────────────────────────────────────────────

def generate_predictions(
    result: dict,
    live_path: Path = LIVE_PATH,
    neutralize: bool = True,
) -> pd.DataFrame:
    """
    Genera predicciones para datos live usando el ensemble.

    Args:
        result: Dict con modelos entrenados (output de train_ensemble).
        live_path: Path al parquet de datos live.
        neutralize: Si aplicar feature neutralization.

    Returns:
        DataFrame con columnas 'id' y 'prediction'.
    """
    logger.info(f"📥 Cargando datos live desde {live_path}...")
    live = pd.read_parquet(live_path)
    logger.info(f"   {len(live):,} filas")

    models = result["models"]
    feature_cols = result["feature_cols"]
    available_features = [c for c in feature_cols if c in live.columns]
    logger.info(f"   Features disponibles: {len(available_features)}/{len(feature_cols)}")

    X_live = live[available_features]

    # Predicciones por modelo (cada target)
    all_preds = pd.DataFrame(index=live.index)
    for target_name, model in models.items():
        raw = model.predict(X_live)
        all_preds[target_name] = rank_normalize(raw)
        logger.info(f"   ✅ Predicción con '{target_name}' generada")

    # Ensemble: promedio
    ensemble = all_preds.mean(axis=1)

    # Feature neutralization
    if neutralize and result.get("use_neutralization", False):
        neut_features = result.get("neutralization_features", feature_cols[:50])
        neut_features = [f for f in neut_features if f in live.columns]
        proportion = result.get("neutralization_proportion", 0.5)

        logger.info(f"🔄 Neutralizando con {len(neut_features)} features (proportion={proportion})...")
        neut_feat_df = live[neut_features].fillna(0.5)
        ensemble = neutralize_features(
            pd.Series(ensemble.values, index=live.index),
            neut_feat_df,
            proportion=proportion,
        )

    # Rank normalize final
    final_preds = rank_normalize(ensemble.values)

    # Construir submission
    if "id" in live.columns:
        id_col = live["id"]
    else:
        id_col = live.index

    submission = pd.DataFrame({
        "id": id_col,
        "prediction": final_preds,
    })

    logger.info(f"✅ Predicciones generadas: {len(submission):,} filas")
    logger.info(f"   Rango: [{final_preds.min():.4f}, {final_preds.max():.4f}]")
    logger.info(f"   Media: {final_preds.mean():.4f} | Std: {final_preds.std():.4f}")

    return submission


def upload_submission(submission_path: Path, model_name: str = "trad_bot_v4"):
    """Sube predicciones a Numerai."""
    import numerapi

    public_id = os.getenv("NUMERAI_PUBLIC_ID")
    secret_key = os.getenv("NUMERAI_SECRET_KEY")

    if not public_id or not secret_key:
        logger.warning("⚠️  Sin credenciales en .env — subí manualmente desde numer.ai")
        return

    napi = numerapi.NumerAPI(public_id=public_id, secret_key=secret_key)
    models = napi.get_models()
    model_uuid = models.get(model_name)

    if not model_uuid:
        logger.error(f"❌ Modelo '{model_name}' no encontrado. Disponibles: {list(models.keys())}")
        return

    logger.info(f"📤 Subiendo a '{model_name}'...")
    submission_id = napi.upload_predictions(str(submission_path), model_id=model_uuid)
    logger.info(f"🎉 ¡Subido! Submission ID: {submission_id}")
    logger.info(f"   Revisá en: https://numer.ai/models")


def download_live_data():
    """Descarga los datos live más recientes."""
    import numerapi

    napi = numerapi.NumerAPI()
    current_round = napi.get_current_round()
    logger.info(f"📊 Ronda actual: {current_round}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    napi.download_dataset("v5.2/live.parquet", str(LIVE_PATH))
    logger.info("✅ Datos live descargados")
    return current_round


# ── Main ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Numerai V3 — Entrenamiento y submission mejorados",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Entrenar con defaults (medium features, era step 4, 5 targets)
  uv run python scripts/numerai_train_v3.py --train

  # Entrenar con feature set small (más rápido, menos RAM)
  uv run python scripts/numerai_train_v3.py --train --feature-set small --era-step 2

  # Entrenar + predecir + subir
  uv run python scripts/numerai_train_v3.py --train --predict --upload

  # Solo predecir con modelo ya entrenado
  uv run python scripts/numerai_train_v3.py --predict --upload

  # Sin neutralización (si querés más CORR pero más crowding)
  uv run python scripts/numerai_train_v3.py --predict --no-neutralize
        """,
    )
    parser.add_argument("--train", action="store_true", help="Entrenar nuevo modelo")
    parser.add_argument("--predict", action="store_true", help="Generar predicciones live")
    parser.add_argument("--upload", action="store_true", help="Subir predicciones a Numerai")
    parser.add_argument(
        "--feature-set", default="medium",
        help="Feature set a usar: small, medium, all, intelligence, etc. (default: medium)",
    )
    parser.add_argument(
        "--era-step", type=int, default=4,
        help="Samplear cada N eras (default: 4 = 25%% de datos)",
    )
    parser.add_argument(
        "--model-path", default="models/numerai_v3_ensemble.pkl",
        help="Path para guardar/cargar modelo",
    )
    parser.add_argument(
        "--model-name", default="trad_bot_v4",
        help="Nombre del modelo en Numerai (default: trad_bot_v4)",
    )
    parser.add_argument(
        "--no-neutralize", action="store_true",
        help="Desactivar feature neutralization",
    )
    args = parser.parse_args()

    model_path = Path(args.model_path)

    # ─── Train ───
    if args.train:
        logger.info("=" * 60)
        logger.info("🏋️  ENTRENAMIENTO V3 — Ensemble Multi-Target")
        logger.info("=" * 60)

        result = train_ensemble(
            feature_set_name=args.feature_set,
            era_step=args.era_step,
        )
        save_ensemble(result, model_path)

    # ─── Predict ───
    if args.predict or args.upload:
        if not args.train:
            if not model_path.exists():
                logger.error(f"❌ Modelo no encontrado: {model_path}")
                logger.info("💡 Usá --train primero para entrenar un modelo")
                return
            result = load_ensemble(model_path)

        # Descargar datos live
        current_round = download_live_data()

        # Generar predicciones
        submission = generate_predictions(
            result,
            neutralize=not args.no_neutralize,
        )

        # Guardar
        submission_path = DATA_DIR / f"submission_v3_round_{current_round}.csv"
        submission.to_csv(submission_path, index=False)
        logger.info(f"💾 Submission guardada: {submission_path}")

        # Upload
        if args.upload:
            upload_submission(submission_path, model_name=args.model_name)

    if not args.train and not args.predict and not args.upload:
        parser.print_help()

    logger.info("\n🎉 ¡Proceso completado!")


if __name__ == "__main__":
    main()

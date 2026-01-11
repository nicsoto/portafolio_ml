"""Modelo ML y estrategia predictiva para trading."""

from dataclasses import dataclass, field
from typing import Any, Optional
import pickle
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler

from ..strategy.base import Strategy, SignalResult
from .features import FeatureEngineer


@dataclass
class MLModelMetrics:
    """Métricas de evaluación del modelo."""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    cv_scores: list = field(default_factory=list)
    feature_importance: dict = field(default_factory=dict)


class MLModel:
    """
    Wrapper para modelos de ML de clasificación.
    
    Soporta:
    - RandomForest
    - GradientBoosting (sklearn)
    - XGBoost
    - LightGBM
    """

    SUPPORTED_MODELS = {
        "random_forest": RandomForestClassifier,
        "gradient_boosting": GradientBoostingClassifier,
        "xgboost": XGBClassifier,
        "lightgbm": LGBMClassifier,
    }

    def __init__(
        self,
        model_type: str = "random_forest",
        model_params: Optional[dict] = None,
        scale_features: bool = True,
    ):
        """
        Args:
            model_type: Tipo de modelo ('random_forest', 'xgboost', etc).
            model_params: Parámetros para el modelo.
            scale_features: Si escalar features antes de entrenar.
        """
        if model_type not in self.SUPPORTED_MODELS:
            raise ValueError(f"Model type must be one of {list(self.SUPPORTED_MODELS.keys())}")

        self.model_type = model_type
        self.model_params = model_params or self._default_params(model_type)
        self.scale_features = scale_features

        self._model = None
        self._scaler = StandardScaler() if scale_features else None
        self._feature_names: list[str] = []
        self._is_trained = False

    def _default_params(self, model_type: str) -> dict:
        """Parámetros por defecto para cada tipo de modelo."""
        if model_type == "random_forest":
            return {
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 10,
                "min_samples_leaf": 5,
                "random_state": 42,
                "n_jobs": -1,
                "class_weight": "balanced",
            }
        elif model_type == "gradient_boosting":
            return {
                "n_estimators": 100,
                "max_depth": 5,
                "learning_rate": 0.1,
                "random_state": 42,
            }
        elif model_type == "xgboost":
            return {
                "n_estimators": 100,
                "max_depth": 6,
                "learning_rate": 0.1,
                "random_state": 42,
                "n_jobs": -1,
                # XGBoost specific for imbalanced data (optional)
                # "scale_pos_weight": 1, 
            }
        elif model_type == "lightgbm":
            return {
                "n_estimators": 100,
                "max_depth": -1,
                "num_leaves": 31,
                "learning_rate": 0.1,
                "random_state": 42,
                "n_jobs": -1,
                "class_weight": "balanced",
            }
        return {}

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
        cv_folds: int = 5,
    ) -> MLModelMetrics:
        """
        Entrena el modelo y retorna métricas.
        
        Usa TimeSeriesSplit para validación cruzada (evita data leakage temporal).
        
        Args:
            X: Features DataFrame.
            y: Target Series.
            test_size: Proporción para test set.
            cv_folds: Número de folds para cross-validation temporal.
            
        Returns:
            MLModelMetrics con resultados de evaluación.
        """
        from sklearn.model_selection import TimeSeriesSplit
        from sklearn.pipeline import Pipeline
        
        self._feature_names = list(X.columns)

        # Split temporal (train antes, test después)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False  # NO shuffle para series temporales
        )

        # Scale si es necesario
        if self.scale_features and self._scaler is not None:
            X_train_scaled = self._scaler.fit_transform(X_train)
            X_test_scaled = self._scaler.transform(X_test)
        else:
            X_train_scaled = X_train.values
            X_test_scaled = X_test.values

        # Crear y entrenar modelo
        model_class = self.SUPPORTED_MODELS[self.model_type]
        self._model = model_class(**self.model_params)
        self._model.fit(X_train_scaled, y_train)
        self._is_trained = True

        # Predicciones
        y_pred = self._model.predict(X_test_scaled)

        # Métricas
        metrics = MLModelMetrics(
            accuracy=accuracy_score(y_test, y_pred),
            precision=precision_score(y_test, y_pred, zero_division=0),
            recall=recall_score(y_test, y_pred, zero_division=0),
            f1=f1_score(y_test, y_pred, zero_division=0),
        )

        # Cross-validation con TimeSeriesSplit y Pipeline (evita data leakage)
        if cv_folds > 1 and len(X_train) >= cv_folds * 10:
            tscv = TimeSeriesSplit(n_splits=cv_folds)
            
            # Crear pipeline para que scaler se fit en cada fold
            steps = []
            if self.scale_features:
                steps.append(("scaler", StandardScaler()))
            steps.append(("model", model_class(**self.model_params)))
            
            pipe = Pipeline(steps)
            cv_scores = cross_val_score(pipe, X_train, y_train, cv=tscv)
            metrics.cv_scores = cv_scores.tolist()

        # Feature importance
        if hasattr(self._model, "feature_importances_"):
            importances = self._model.feature_importances_
            metrics.feature_importance = dict(zip(self._feature_names, importances))

        return metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Genera predicciones.
        
        Args:
            X: Features DataFrame.
            
        Returns:
            Array de predicciones (0 o 1).
        """
        if not self._is_trained:
            raise RuntimeError("Model must be trained before predicting")

        # Asegurar mismo orden de features
        X = X[self._feature_names]

        if self.scale_features and self._scaler is not None:
            X_scaled = self._scaler.transform(X)
        else:
            X_scaled = X.values

        return self._model.predict(X_scaled)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Genera probabilidades de predicción.
        
        Args:
            X: Features DataFrame.
            
        Returns:
            Array de probabilidades para clase positiva.
        """
        if not self._is_trained:
            raise RuntimeError("Model must be trained before predicting")

        X = X[self._feature_names]

        if self.scale_features and self._scaler is not None:
            X_scaled = self._scaler.transform(X)
        else:
            X_scaled = X.values

        return self._model.predict_proba(X_scaled)[:, 1]

    def save(self, path: Path | str) -> None:
        """Guarda modelo entrenado."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        state = {
            "model": self._model,
            "scaler": self._scaler,
            "feature_names": self._feature_names,
            "model_type": self.model_type,
            "model_params": self.model_params,
        }
        with open(path, "wb") as f:
            pickle.dump(state, f)

    @classmethod
    def load(cls, path: Path | str) -> "MLModel":
        """Carga modelo guardado."""
        with open(path, "rb") as f:
            state = pickle.load(f)
        
        instance = cls(
            model_type=state["model_type"],
            model_params=state["model_params"],
        )
        instance._model = state["model"]
        instance._scaler = state["scaler"]
        instance._feature_names = state["feature_names"]
        instance._is_trained = True
        return instance


class MLStrategy(Strategy):
    """
    Estrategia basada en modelo ML.
    
    Genera señales de entry cuando el modelo predice subida con
    probabilidad mayor al threshold, y exit cuando predice bajada.
    """

    def __init__(
        self,
        model: MLModel,
        feature_engineer: FeatureEngineer,
        entry_threshold: float = 0.6,
        exit_threshold: float = 0.4,
    ):
        """
        Args:
            model: Modelo ML entrenado.
            feature_engineer: FeatureEngineer para crear features.
            entry_threshold: Probabilidad mínima para entry.
            exit_threshold: Probabilidad máxima para exit.
        """
        self.model = model
        self.feature_engineer = feature_engineer
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold

    @property
    def name(self) -> str:
        return f"ML_{self.model.model_type}_thresh_{self.entry_threshold}"

    @property
    def params(self) -> dict:
        return {
            "model_type": self.model.model_type,
            "entry_threshold": self.entry_threshold,
            "exit_threshold": self.exit_threshold,
        }

    def generate_signals(self, prices: pd.DataFrame) -> SignalResult:
        """
        Genera señales basadas en predicciones del modelo.
        
        Args:
            prices: DataFrame OHLCV.
            
        Returns:
            SignalResult con entries/exits y features.
        """
        self.validate_prices(prices)

        # Generar features
        features = self.feature_engineer.create_features(prices)
        
        # Eliminar NaN (modelo no puede predecir con NaN)
        valid_mask = ~features.isna().any(axis=1)
        features_clean = features[valid_mask]

        # Inicializar señales como False
        entries = pd.Series(False, index=prices.index)
        exits = pd.Series(False, index=prices.index)

        if len(features_clean) > 0:
            # Predecir probabilidades
            proba = self.model.predict_proba(features_clean)
            proba_series = pd.Series(proba, index=features_clean.index)

            # Entry: probabilidad > entry_threshold
            # Exit: probabilidad < exit_threshold
            entries.loc[features_clean.index] = proba_series > self.entry_threshold
            exits.loc[features_clean.index] = proba_series < self.exit_threshold

            # Agregar probabilidad a features
            features["ml_probability"] = np.nan
            features.loc[features_clean.index, "ml_probability"] = proba

        signals = pd.DataFrame({"entries": entries, "exits": exits}, index=prices.index)

        return SignalResult(signals=signals, features=features)

"""Optimización de hiperparámetros con Optuna."""

import optuna
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import asdict

from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.base import clone

from .model import MLModel


class ModelOptimizer:
    """
    Optimizador de hiperparámetros usando Optuna.
    Soporta RF, XGBoost, LightGBM.
    """

    def __init__(self, n_trials: int = 50, cv_folds: int = 5):
        """
        Args:
            n_trials: Número de intentos de optimización.
            cv_folds: Folds para TimeSeriesSplit cross-validation.
        """
        self.n_trials = n_trials
        self.cv_folds = cv_folds

    def optimize(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model_type: str = "random_forest",
        metric: str = "f1",
    ) -> Dict[str, Any]:
        """
        Ejecuta la optimización y retorna los mejores parámetros.
        
        Args:
            X: Features DataFrame.
            y: Target Series.
            model_type: Tipo de modelo a optimizar.
            metric: Métrica a maximizar ('accuracy', 'precision', 'recall', 'f1').
            
        Returns:
            Diccionario con los mejores parámetros encontrados.
        """
        # Definir función objetivo para Optuna
        def objective(trial):
            params = self._suggest_params(trial, model_type)
            
            # Instanciar modelo base
            model_class = MLModel.SUPPORTED_MODELS[model_type]
            model = model_class(**params)
            
            # Pipeline con scaler (importante para evitar leakage)
            # Para árboles a veces no es crítico escalar, pero es buena práctica
            # especialmente modelos sensibles a magnitud.
            pipeline = Pipeline([
                ("scaler", StandardScaler()),
                ("model", model)
            ])
            
            # CV temporal
            # OJO: Se usaba len(X) >= cv_folds * 10 en MLModel, aquí asumimos datasize suficiente
            tscv = TimeSeriesSplit(n_splits=self.cv_folds)
            
            # Scoring
            # sklearn metrics string names: 'accuracy', 'precision', 'recall', 'f1'
            # Para imbalanced data, 'f1_weighted' o 'f1_macro' puede ser mejor,
            # pero mantendremos simple 'f1' (clase positiva 1) si es binaria.
            scoring = metric if metric != "f1" else "f1"  # Simplificación
            
            try:
                scores = cross_val_score(
                    pipeline, X, y, cv=tscv, scoring=scoring, n_jobs=-1
                )
                return scores.mean()
            except Exception as e:
                # Si falla una combinación por alguna razón, retornamos valor bajo
                return 0.0

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=self.n_trials)

        return study.best_params

    def _suggest_params(self, trial: optuna.Trial, model_type: str) -> Dict[str, Any]:
        """Sugiere parámetros según el tipo de modelo."""
        if model_type == "random_forest":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                "max_depth": trial.suggest_int("max_depth", 3, 20),
                "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
                "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
                "random_state": 42,
                "n_jobs": -1,
                "class_weight": "balanced",
            }
            
        elif model_type == "gradient_boosting":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                "random_state": 42,
            }
            
        elif model_type == "xgboost":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                "max_depth": trial.suggest_int("max_depth", 3, 12),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
                "random_state": 42,
                "n_jobs": -1,
                # "scale_pos_weight" se podría tunear si se calcula ratio neg/pos
            }
            
        elif model_type == "lightgbm":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                "max_depth": trial.suggest_int("max_depth", -1, 15),
                "num_leaves": trial.suggest_int("num_leaves", 20, 100),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
                "random_state": 42,
                "n_jobs": -1,
                "class_weight": "balanced",
                # "verbosity": -1,
            }
            
        return {}

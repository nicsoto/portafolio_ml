"""Tests para el módulo de ML."""

import pandas as pd
import numpy as np
import pytest

from src.ml.features import FeatureEngineer
from src.ml.model import MLModel, MLStrategy, MLModelMetrics


def create_test_prices(n_bars: int = 200) -> pd.DataFrame:
    """Crea DataFrame de precios para testing con tendencia y ruido."""
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=n_bars, freq="D")
    
    # Crear precios con tendencia + ruido
    trend = np.linspace(100, 150, n_bars)
    noise = np.random.randn(n_bars) * 2
    close = trend + noise
    
    return pd.DataFrame({
        "open": close - np.random.rand(n_bars),
        "high": close + np.random.rand(n_bars) * 2,
        "low": close - np.random.rand(n_bars) * 2,
        "close": close,
        "volume": np.random.randint(10000, 100000, n_bars),
    }, index=dates)


class TestFeatureEngineer:
    """Tests para FeatureEngineer."""

    def test_create_features_returns_dataframe(self):
        """create_features retorna DataFrame."""
        fe = FeatureEngineer()
        prices = create_test_prices()
        
        features = fe.create_features(prices)
        
        assert isinstance(features, pd.DataFrame)
        assert len(features) == len(prices)

    def test_features_have_expected_columns(self):
        """Features incluyen columnas esperadas."""
        fe = FeatureEngineer()
        prices = create_test_prices()
        
        features = fe.create_features(prices)
        
        # Verificar algunas features clave
        assert "return_1d" in features.columns
        assert "rsi" in features.columns
        assert "atr" in features.columns
        assert "ma_cross" in features.columns
        assert "momentum_5d" in features.columns

    def test_create_target_returns_series(self):
        """create_target retorna Series binaria."""
        fe = FeatureEngineer()
        prices = create_test_prices()
        
        target = fe.create_target(prices, horizon=1)
        
        assert isinstance(target, pd.Series)
        assert set(target.dropna().unique()).issubset({0, 1})

    def test_prepare_dataset_removes_nan(self):
        """prepare_dataset elimina NaN cuando dropna=True."""
        fe = FeatureEngineer()
        prices = create_test_prices()
        
        features, target = fe.prepare_dataset(prices, dropna=True)
        
        assert not features.isna().any().any()
        assert not target.isna().any()
        assert len(features) == len(target)


class TestMLModel:
    """Tests para MLModel."""

    def test_init_random_forest(self):
        """Inicializar con RandomForest."""
        model = MLModel(model_type="random_forest")
        assert model.model_type == "random_forest"

    def test_init_invalid_model_type(self):
        """Tipo de modelo inválido genera error."""
        with pytest.raises(ValueError, match="Model type must be one of"):
            MLModel(model_type="invalid_model")

    def test_train_returns_metrics(self):
        """train retorna MLModelMetrics."""
        fe = FeatureEngineer()
        prices = create_test_prices(200)
        X, y = fe.prepare_dataset(prices)
        
        model = MLModel(model_type="random_forest")
        metrics = model.train(X, y, test_size=0.2, cv_folds=3)
        
        assert isinstance(metrics, MLModelMetrics)
        assert 0 <= metrics.accuracy <= 1
        assert 0 <= metrics.precision <= 1

    def test_predict_after_train(self):
        """predict funciona después de entrenar."""
        fe = FeatureEngineer()
        prices = create_test_prices(200)
        X, y = fe.prepare_dataset(prices)
        
        model = MLModel(model_type="random_forest")
        model.train(X, y)
        
        predictions = model.predict(X)
        
        assert len(predictions) == len(X)
        assert set(predictions).issubset({0, 1})

    def test_predict_before_train_raises_error(self):
        """predict sin entrenar genera error."""
        model = MLModel()
        X = pd.DataFrame({"a": [1, 2, 3]})
        
        with pytest.raises(RuntimeError, match="must be trained"):
            model.predict(X)


class TestMLStrategy:
    """Tests para MLStrategy."""

    def test_generate_signals_returns_signal_result(self):
        """generate_signals retorna SignalResult."""
        # Entrenar modelo primero
        fe = FeatureEngineer()
        prices = create_test_prices(200)
        X, y = fe.prepare_dataset(prices)
        
        model = MLModel(model_type="random_forest")
        model.train(X, y)
        
        strategy = MLStrategy(model=model, feature_engineer=fe)
        result = strategy.generate_signals(prices)
        
        assert "entries" in result.signals.columns
        assert "exits" in result.signals.columns
        assert len(result.signals) == len(prices)

    def test_name_property(self):
        """name refleja configuración."""
        fe = FeatureEngineer()
        model = MLModel(model_type="gradient_boosting")
        # Entrenar para que no falle
        prices = create_test_prices(200)
        X, y = fe.prepare_dataset(prices)
        model.train(X, y)
        
        strategy = MLStrategy(model=model, feature_engineer=fe, entry_threshold=0.7)
        
        assert "gradient_boosting" in strategy.name
        assert "0.7" in strategy.name

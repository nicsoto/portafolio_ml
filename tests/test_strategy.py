"""Tests para el motor de estrategia."""

from datetime import datetime, timedelta

import pandas as pd
import pytest

from src.strategy.base import Strategy, SignalResult
from src.strategy.ma_cross import MACrossStrategy


def create_test_prices(n_bars: int = 100, trend: str = "up") -> pd.DataFrame:
    """Crea DataFrame de precios para testing."""
    dates = pd.date_range(start="2024-01-01", periods=n_bars, freq="D")

    if trend == "up":
        close = [100 + i * 0.5 for i in range(n_bars)]
    elif trend == "down":
        close = [100 - i * 0.5 for i in range(n_bars)]
    else:  # oscillating
        close = [100 + 10 * ((-1) ** i) for i in range(n_bars)]

    return pd.DataFrame({
        "open": [c - 1 for c in close],
        "high": [c + 2 for c in close],
        "low": [c - 2 for c in close],
        "close": close,
        "volume": [10000] * n_bars,
    }, index=dates)


class TestMACrossStrategy:
    """Tests para MACrossStrategy."""

    def test_init_valid_params(self):
        """Inicialización con parámetros válidos."""
        strategy = MACrossStrategy(fast_period=10, slow_period=50)
        assert strategy.fast_period == 10
        assert strategy.slow_period == 50

    def test_init_invalid_fast_greater_than_slow(self):
        """fast >= slow debe fallar."""
        with pytest.raises(ValueError, match="fast_period.*must be < slow_period"):
            MACrossStrategy(fast_period=50, slow_period=10)

    def test_init_invalid_fast_equals_slow(self):
        """fast == slow debe fallar."""
        with pytest.raises(ValueError, match="fast_period.*must be < slow_period"):
            MACrossStrategy(fast_period=20, slow_period=20)

    def test_generate_signals_returns_correct_type(self):
        """generate_signals retorna SignalResult."""
        strategy = MACrossStrategy(fast_period=5, slow_period=20)
        prices = create_test_prices(100)

        result = strategy.generate_signals(prices)

        assert isinstance(result, SignalResult)
        assert "entries" in result.signals.columns
        assert "exits" in result.signals.columns

    def test_signals_aligned_with_prices(self):
        """Señales tienen mismo índice que precios."""
        strategy = MACrossStrategy(fast_period=5, slow_period=20)
        prices = create_test_prices(100)

        result = strategy.generate_signals(prices)

        assert len(result.signals) == len(prices)
        pd.testing.assert_index_equal(result.signals.index, prices.index)

    def test_features_include_moving_averages(self):
        """Features incluyen MAs calculadas."""
        strategy = MACrossStrategy(fast_period=5, slow_period=20)
        prices = create_test_prices(100)

        result = strategy.generate_signals(prices)

        assert result.features is not None
        assert "ma_fast_5" in result.features.columns
        assert "ma_slow_20" in result.features.columns

    def test_name_property(self):
        """Nombre de estrategia es correcto."""
        strategy = MACrossStrategy(fast_period=10, slow_period=50, ma_type="sma")
        assert strategy.name == "MACross_SMA_10_50"

    def test_params_property(self):
        """Parámetros para reproducibilidad."""
        strategy = MACrossStrategy(fast_period=10, slow_period=50, ma_type="ema")
        params = strategy.params

        assert params["fast_period"] == 10
        assert params["slow_period"] == 50
        assert params["ma_type"] == "ema"

    def test_empty_prices_raises_error(self):
        """Precios vacíos generan error."""
        strategy = MACrossStrategy(fast_period=5, slow_period=20)
        empty_prices = pd.DataFrame()

        with pytest.raises(ValueError, match="prices.*empty"):
            strategy.generate_signals(empty_prices)


class TestSignalResult:
    """Tests para SignalResult."""

    def test_valid_signal_result(self):
        """SignalResult válido."""
        signals = pd.DataFrame({
            "entries": [True, False, False],
            "exits": [False, False, True],
        })
        result = SignalResult(signals=signals)
        assert len(result.signals) == 3

    def test_missing_columns_raises_error(self):
        """Columnas faltantes generan error."""
        signals = pd.DataFrame({"entries": [True, False]})  # Missing 'exits'

        with pytest.raises(ValueError, match="missing required columns"):
            SignalResult(signals=signals)

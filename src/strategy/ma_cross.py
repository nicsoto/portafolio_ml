"""Estrategia Moving Average Crossover."""

import pandas as pd

from .base import Strategy, SignalResult
from .indicators import sma


class MACrossStrategy(Strategy):
    """
    Estrategia de cruce de medias móviles.
    
    - Entry (long): MA rápida cruza arriba de MA lenta
    - Exit: MA rápida cruza abajo de MA lenta
    
    Soporta tanto SMA como EMA.
    """

    def __init__(
        self,
        fast_period: int = 10,
        slow_period: int = 50,
        ma_type: str = "sma",
    ):
        """
        Args:
            fast_period: Período de la MA rápida.
            slow_period: Período de la MA lenta.
            ma_type: Tipo de MA ('sma' o 'ema').
        """
        if fast_period >= slow_period:
            raise ValueError(
                f"fast_period ({fast_period}) must be < slow_period ({slow_period})"
            )
        if fast_period < 1:
            raise ValueError("fast_period must be >= 1")
        if ma_type not in ("sma", "ema"):
            raise ValueError(f"ma_type must be 'sma' or 'ema', got '{ma_type}'")

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.ma_type = ma_type

    @property
    def name(self) -> str:
        return f"MACross_{self.ma_type.upper()}_{self.fast_period}_{self.slow_period}"

    @property
    def params(self) -> dict:
        return {
            "fast_period": self.fast_period,
            "slow_period": self.slow_period,
            "ma_type": self.ma_type,
        }

    def generate_signals(self, prices: pd.DataFrame) -> SignalResult:
        """
        Genera señales de entrada/salida basadas en cruce de MAs.

        Args:
            prices: DataFrame OHLCV.

        Returns:
            SignalResult con entries/exits y features (MAs calculadas).
        """
        self.validate_prices(prices)

        close = prices["close"]

        # Calcular medias móviles
        if self.ma_type == "sma":
            from .indicators import sma as ma_func
        else:
            from .indicators import ema as ma_func

        fast_ma = ma_func(close, self.fast_period)
        slow_ma = ma_func(close, self.slow_period)

        # Detectar cruces
        # Entry: fast cruza arriba de slow (fast > slow y antes fast <= slow)
        fast_above_slow = fast_ma > slow_ma
        entries = fast_above_slow & (~fast_above_slow.shift(1).fillna(False))

        # Exit: fast cruza abajo de slow (fast < slow y antes fast >= slow)
        fast_below_slow = fast_ma < slow_ma
        exits = fast_below_slow & (~fast_below_slow.shift(1).fillna(False))

        # Crear DataFrame de señales
        signals = pd.DataFrame(
            {"entries": entries, "exits": exits},
            index=prices.index,
        )

        # Features para análisis/debugging
        features = pd.DataFrame(
            {
                f"ma_fast_{self.fast_period}": fast_ma,
                f"ma_slow_{self.slow_period}": slow_ma,
                "fast_above_slow": fast_above_slow,
            },
            index=prices.index,
        )

        return SignalResult(signals=signals, features=features)

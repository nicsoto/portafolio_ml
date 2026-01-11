"""Clase base abstracta para estrategias de trading."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd


@dataclass
class SignalResult:
    """
    Resultado de generación de señales.
    
    Attributes:
        signals: DataFrame con columnas 'entries' y 'exits' (bool).
        features: DataFrame con indicadores calculados (opcional).
    """
    signals: pd.DataFrame
    features: pd.DataFrame | None = None

    def __post_init__(self):
        """Valida que signals tenga las columnas requeridas."""
        required_cols = {"entries", "exits"}
        if not required_cols.issubset(self.signals.columns):
            missing = required_cols - set(self.signals.columns)
            raise ValueError(f"signals missing required columns: {missing}")


class Strategy(ABC):
    """
    Clase base abstracta para estrategias de trading.
    
    Output Contract:
        - signals: DataFrame con columnas 'entries' y 'exits' (bool)
        - índice alineado con el DataFrame de precios de entrada
        - features: indicadores calculados (opcional, para debugging/análisis)
    """

    @abstractmethod
    def generate_signals(self, prices: pd.DataFrame) -> SignalResult:
        """
        Genera señales de entrada/salida basadas en precios.

        Args:
            prices: DataFrame con columnas [open, high, low, close, volume]
                    e índice DatetimeIndex.

        Returns:
            SignalResult con signals (entries/exits) y features opcionales.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre de la estrategia para logs/reportes."""
        pass

    @property
    @abstractmethod
    def params(self) -> dict:
        """
        Parámetros de la estrategia para reproducibilidad.
        
        Returns:
            Dict con todos los parámetros configurables.
        """
        pass

    def validate_prices(self, prices: pd.DataFrame) -> None:
        """
        Valida que el DataFrame de precios tenga el formato correcto.

        Args:
            prices: DataFrame a validar.

        Raises:
            ValueError: Si faltan columnas requeridas o está vacío.
        """
        if prices.empty:
            raise ValueError("prices DataFrame is empty")

        required_cols = {"open", "high", "low", "close"}
        missing = required_cols - set(prices.columns)
        if missing:
            raise ValueError(f"prices missing required columns: {missing}")

        if not isinstance(prices.index, pd.DatetimeIndex):
            raise ValueError("prices index must be DatetimeIndex")

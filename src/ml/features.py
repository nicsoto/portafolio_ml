"""Feature engineering para modelos ML de trading."""

import pandas as pd
import numpy as np
from typing import List

from ..strategy.indicators import sma, ema, rsi, atr, macd, bollinger_bands


class FeatureEngineer:
    """
    Genera features técnicos para modelos de ML.
    
    Features incluidos:
    - Retornos (1, 5, 10, 20 períodos)
    - Medias móviles (ratios y cruces)
    - RSI
    - Volatilidad (ATR, std)
    - MACD
    - Bollinger Bands (posición)
    - Volume features
    """

    def __init__(
        self,
        sma_periods: List[int] = [5, 10, 20, 50],
        rsi_period: int = 14,
        atr_period: int = 14,
        lookback_periods: List[int] = [1, 5, 10, 20],
    ):
        """
        Args:
            sma_periods: Períodos para SMAs.
            rsi_period: Período para RSI.
            atr_period: Período para ATR.
            lookback_periods: Períodos para retornos históricos.
        """
        self.sma_periods = sma_periods
        self.rsi_period = rsi_period
        self.atr_period = atr_period
        self.lookback_periods = lookback_periods

    def create_features(self, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Genera DataFrame de features a partir de precios OHLCV.
        
        Args:
            prices: DataFrame con columnas [open, high, low, close, volume].
            
        Returns:
            DataFrame con features calculados, mismo índice que prices.
        """
        df = pd.DataFrame(index=prices.index)
        close = prices["close"]
        high = prices["high"]
        low = prices["low"]
        volume = prices["volume"] if "volume" in prices.columns else None

        # 1. Retornos históricos
        for period in self.lookback_periods:
            df[f"return_{period}d"] = close.pct_change(period)

        # 2. Medias móviles y ratios
        for period in self.sma_periods:
            ma = sma(close, period)
            df[f"sma_{period}"] = ma
            df[f"close_to_sma_{period}"] = close / ma - 1  # Distancia relativa

        # 3. Cruces de MAs (features binarios para cada par)
        if len(self.sma_periods) >= 2:
            fast_ma = sma(close, self.sma_periods[0])
            slow_ma = sma(close, self.sma_periods[-1])
            df["ma_cross"] = (fast_ma > slow_ma).astype(int)
            df["ma_diff"] = (fast_ma - slow_ma) / slow_ma

        # 4. RSI
        df["rsi"] = rsi(close, self.rsi_period)
        df["rsi_oversold"] = (df["rsi"] < 30).astype(int)
        df["rsi_overbought"] = (df["rsi"] > 70).astype(int)

        # 5. Volatilidad
        df["atr"] = atr(high, low, close, self.atr_period)
        df["atr_pct"] = df["atr"] / close  # ATR como % del precio
        
        for period in [5, 20]:
            df[f"volatility_{period}d"] = close.pct_change().rolling(period).std()

        # 6. MACD
        macd_df = macd(close)
        if macd_df is not None and not macd_df.empty:
            # Renombrar columnas de MACD
            macd_cols = macd_df.columns.tolist()
            if len(macd_cols) >= 3:
                df["macd"] = macd_df.iloc[:, 0]
                df["macd_signal"] = macd_df.iloc[:, 2]
                df["macd_hist"] = macd_df.iloc[:, 1]

        # 7. Bollinger Bands
        bb_df = bollinger_bands(close)
        if bb_df is not None and not bb_df.empty:
            bb_cols = bb_df.columns.tolist()
            # Encontrar columnas lower, mid, upper
            lower_col = [c for c in bb_cols if "BBL" in c]
            upper_col = [c for c in bb_cols if "BBU" in c]
            mid_col = [c for c in bb_cols if "BBM" in c]
            
            if lower_col and upper_col:
                bb_lower = bb_df[lower_col[0]]
                bb_upper = bb_df[upper_col[0]]
                bb_range = bb_upper - bb_lower
                df["bb_position"] = (close - bb_lower) / bb_range  # 0-1
                df["bb_width"] = bb_range / close

        # 8. Volume features (si disponible)
        if volume is not None:
            df["volume_sma_20"] = sma(volume, 20)
            df["volume_ratio"] = volume / df["volume_sma_20"]
            df["volume_change"] = volume.pct_change()

        # 9. Features de precio
        df["high_low_range"] = (high - low) / close
        df["close_position"] = (close - low) / (high - low)  # Dónde cerró en el rango

        # 10. Momentum
        for period in [5, 10, 20]:
            df[f"momentum_{period}d"] = close / close.shift(period) - 1

        return df

    def create_target(
        self,
        prices: pd.DataFrame,
        horizon: int = 1,
        threshold: float = 0.0,
    ) -> pd.Series:
        """
        Crea variable target para clasificación.
        
        Args:
            prices: DataFrame con precios.
            horizon: Períodos hacia adelante para predecir.
            threshold: Umbral de retorno para considerar "positivo".
            
        Returns:
            Series con 1 (subida) o 0 (bajada) para cada timestamp.
        """
        future_return = prices["close"].pct_change(horizon).shift(-horizon)
        target = (future_return > threshold).astype(int)
        return target

    def prepare_dataset(
        self,
        prices: pd.DataFrame,
        horizon: int = 1,
        threshold: float = 0.0,
        dropna: bool = True,
    ) -> tuple[pd.DataFrame, pd.Series]:
        """
        Prepara dataset completo (features + target).
        
        Args:
            prices: DataFrame con precios OHLCV.
            horizon: Períodos hacia adelante para target.
            threshold: Umbral para target.
            dropna: Si eliminar filas con NaN.
            
        Returns:
            Tuple de (features DataFrame, target Series).
        """
        features = self.create_features(prices)
        target = self.create_target(prices, horizon, threshold)

        if dropna:
            # Combinar para eliminar NaN de ambos
            combined = pd.concat([features, target.rename("target")], axis=1)
            combined = combined.dropna()
            features = combined.drop("target", axis=1)
            target = combined["target"]

        return features, target

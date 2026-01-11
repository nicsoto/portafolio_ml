"""Feature engineering para modelos ML de trading - SIN LOOKAHEAD BIAS."""

import pandas as pd
import numpy as np
from typing import List

from ..strategy.indicators import sma, ema, rsi, atr, macd, bollinger_bands


class FeatureEngineer:
    """
    Genera features técnicos para modelos de ML.
    
    CRÍTICO: Todos los features en tiempo t usan SOLO información hasta t-1.
    Esto se logra calculando features normalmente y luego haciendo .shift(1)
    al DataFrame completo al final.
    
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
        
        CRÍTICO: 
        1. Calculamos features con precios normales (sin shift)
        2. Al FINAL hacemos df.shift(1) para que feature[t] use datos hasta t-1
        
        Esto es correcto porque:
        - sma(close, 20) en día t usa close[t-19:t+1] (incluye t)
        - Luego .shift(1) mueve todo, entonces en día t del output 
          tendrás el SMA calculado hasta t-1 ✅
        
        Args:
            prices: DataFrame con columnas [open, high, low, close, volume].
            
        Returns:
            DataFrame con features calculados, mismo índice que prices.
        """
        df = pd.DataFrame(index=prices.index)
        
        # Usamos precios SIN shift - el shift se hace al final
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
            macd_cols = macd_df.columns.tolist()
            if len(macd_cols) >= 3:
                df["macd"] = macd_df.iloc[:, 0]
                df["macd_signal"] = macd_df.iloc[:, 2]
                df["macd_hist"] = macd_df.iloc[:, 1]

        # 7. Bollinger Bands
        bb_df = bollinger_bands(close)
        if bb_df is not None and not bb_df.empty:
            bb_cols = bb_df.columns.tolist()
            lower_col = [c for c in bb_cols if "BBL" in c]
            upper_col = [c for c in bb_cols if "BBU" in c]
            
            if lower_col and upper_col:
                bb_lower = bb_df[lower_col[0]]
                bb_upper = bb_df[upper_col[0]]
                bb_range = bb_upper - bb_lower
                df["bb_position"] = (close - bb_lower) / bb_range  # 0-1
                df["bb_width"] = bb_range / close

        # 8. Volume features
        if volume is not None:
            df["volume_sma_20"] = sma(volume, 20)
            df["volume_ratio"] = volume / df["volume_sma_20"]
            df["volume_change"] = volume.pct_change()

        # 9. Features de precio
        df["high_low_range"] = (high - low) / close
        df["close_position"] = (close - low) / (high - low)

        # 10. Momentum
        for period in [5, 10, 20]:
            df[f"momentum_{period}d"] = close / close.shift(period) - 1

        # 🔥 CRÍTICO: Shiftear TODO el DataFrame al final
        # Esto garantiza que feature[t] usa SOLO datos hasta t-1
        df = df.shift(1)

        return df

    def create_target(
        self,
        prices: pd.DataFrame,
        horizon: int = 1,
        threshold: float = 0.0,
    ) -> pd.Series:
        """
        Crea variable target para clasificación.
        
        Target en día t predice si el precio subirá en los próximos 'horizon' días.
        
        Fórmula:
            target[t] = 1 si (precio[t+horizon] / precio[t]) - 1 > threshold
            
        Equivalente a:
            target[t] = 1 si precio[t+horizon] > precio[t] * (1 + threshold)
        
        Ejemplo con horizon=1, threshold=0.0:
            target[t] = 1 si precio[t+1] > precio[t]
        
        Args:
            prices: DataFrame con precios.
            horizon: Períodos hacia adelante para predecir.
            threshold: Umbral de retorno mínimo para considerar "subida".
            
        Returns:
            Series con 1 (subirá) o 0 (bajará/lateral).
        """
        close = prices["close"]
        future_price = close.shift(-horizon)
        future_return = (future_price / close) - 1
        
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
        Prepara dataset completo SIN lookahead bias.
        
        IMPORTANTE: 
        - Features en día t usan datos hasta t-1 (por el shift al final)
        - Target en día t predice retorno de t a t+horizon
        - Modelo aprende: "dado lo que sabía ayer, ¿subirá hoy?"
        
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
            combined = pd.concat([features, target.rename("target")], axis=1)
            combined = combined.dropna()
            features = combined.drop("target", axis=1)
            target = combined["target"]

        return features, target

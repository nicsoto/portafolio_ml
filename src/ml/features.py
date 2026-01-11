"""Feature engineering para modelos ML de trading - SIN LOOKAHEAD BIAS."""

import pandas as pd
import numpy as np
from typing import List

from ..strategy.indicators import sma, ema, rsi, atr, macd, bollinger_bands


class FeatureEngineer:
    """
    Genera features técnicos para modelos de ML.
    
    CRÍTICO: Todos los features en tiempo t usan SOLO información hasta t-1.
    Esto evita lookahead bias al usar .shift(1) en los precios.
    
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
        
        CRÍTICO: Feature en día t usa SOLO datos hasta día t-1.
        Esto se logra con .shift(1) en todos los precios.
        
        Args:
            prices: DataFrame con columnas [open, high, low, close, volume].
            
        Returns:
            DataFrame con features calculados, mismo índice que prices.
        """
        df = pd.DataFrame(index=prices.index)
        
        # IMPORTANTE: Shift(1) en todos los precios para evitar lookahead bias
        # Usamos los datos de AYER para calcular features de HOY
        close_lagged = prices["close"].shift(1)
        high_lagged = prices["high"].shift(1)
        low_lagged = prices["low"].shift(1)
        volume_lagged = prices["volume"].shift(1) if "volume" in prices.columns else None

        # 1. Retornos históricos (calculados con precios lagged)
        for period in self.lookback_periods:
            df[f"return_{period}d"] = close_lagged.pct_change(period)

        # 2. Medias móviles y ratios (calculadas con precios lagged)
        for period in self.sma_periods:
            ma = sma(close_lagged, period)
            df[f"sma_{period}"] = ma
            df[f"close_to_sma_{period}"] = close_lagged / ma - 1  # Distancia relativa

        # 3. Cruces de MAs (features binarios para cada par)
        if len(self.sma_periods) >= 2:
            fast_ma = sma(close_lagged, self.sma_periods[0])
            slow_ma = sma(close_lagged, self.sma_periods[-1])
            df["ma_cross"] = (fast_ma > slow_ma).astype(int)
            df["ma_diff"] = (fast_ma - slow_ma) / slow_ma

        # 4. RSI (con precios lagged)
        df["rsi"] = rsi(close_lagged, self.rsi_period)
        df["rsi_oversold"] = (df["rsi"] < 30).astype(int)
        df["rsi_overbought"] = (df["rsi"] > 70).astype(int)

        # 5. Volatilidad (con precios lagged)
        df["atr"] = atr(high_lagged, low_lagged, close_lagged, self.atr_period)
        df["atr_pct"] = df["atr"] / close_lagged  # ATR como % del precio
        
        for period in [5, 20]:
            df[f"volatility_{period}d"] = close_lagged.pct_change().rolling(period).std()

        # 6. MACD (con precios lagged)
        macd_df = macd(close_lagged)
        if macd_df is not None and not macd_df.empty:
            # Renombrar columnas de MACD
            macd_cols = macd_df.columns.tolist()
            if len(macd_cols) >= 3:
                df["macd"] = macd_df.iloc[:, 0]
                df["macd_signal"] = macd_df.iloc[:, 2]
                df["macd_hist"] = macd_df.iloc[:, 1]

        # 7. Bollinger Bands (con precios lagged)
        bb_df = bollinger_bands(close_lagged)
        if bb_df is not None and not bb_df.empty:
            bb_cols = bb_df.columns.tolist()
            # Encontrar columnas lower, mid, upper
            lower_col = [c for c in bb_cols if "BBL" in c]
            upper_col = [c for c in bb_cols if "BBU" in c]
            
            if lower_col and upper_col:
                bb_lower = bb_df[lower_col[0]]
                bb_upper = bb_df[upper_col[0]]
                bb_range = bb_upper - bb_lower
                df["bb_position"] = (close_lagged - bb_lower) / bb_range  # 0-1
                df["bb_width"] = bb_range / close_lagged

        # 8. Volume features (con volumen lagged)
        if volume_lagged is not None:
            df["volume_sma_20"] = sma(volume_lagged, 20)
            df["volume_ratio"] = volume_lagged / df["volume_sma_20"]
            df["volume_change"] = volume_lagged.pct_change()

        # 9. Features de precio (con precios lagged)
        df["high_low_range"] = (high_lagged - low_lagged) / close_lagged
        df["close_position"] = (close_lagged - low_lagged) / (high_lagged - low_lagged)

        # 10. Momentum (con precios lagged)
        for period in [5, 10, 20]:
            df[f"momentum_{period}d"] = close_lagged / close_lagged.shift(period) - 1

        return df

    def create_target(
        self,
        prices: pd.DataFrame,
        horizon: int = 1,
        threshold: float = 0.0,
    ) -> pd.Series:
        """
        Crea variable target CORRECTA para clasificación.
        
        Target en día t predice si el precio subirá en los próximos 'horizon' días.
        
        Args:
            prices: DataFrame con precios.
            horizon: Períodos hacia adelante para predecir.
            threshold: Umbral de retorno mínimo para considerar "subida".
            
        Returns:
            Series con 1 (subirá) o 0 (bajará/lateral).
            
        Ejemplo:
            horizon=1, threshold=0.0
            Día t: target=1 si precio[t+1] > precio[t]
        """
        # Calcular retorno futuro desde HOY hacia ADELANTE
        close = prices["close"]
        future_price = close.shift(-horizon)
        future_return = (future_price / close) - 1
        
        # Clasificar: 1 si sube más que threshold, 0 si no
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
        - Features en día t usan datos hasta t-1
        - Target en día t predice retorno de t a t+horizon
        - Cuando entrenas, el modelo aprende: "dado lo que sabía ayer, ¿subirá mañana?"
        
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
            # Eliminar las primeras filas donde features tienen NaN
            # y las últimas donde target tiene NaN (por shift futuro)
            combined = pd.concat([features, target.rename("target")], axis=1)
            combined = combined.dropna()
            features = combined.drop("target", axis=1)
            target = combined["target"]

        return features, target

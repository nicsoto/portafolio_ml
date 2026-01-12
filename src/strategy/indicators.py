"""Wrappers para indicadores técnicos usando pandas-ta."""

import pandas as pd
import pandas_ta as ta


def sma(series: pd.Series, period: int) -> pd.Series:
    """
    Simple Moving Average.

    Args:
        series: Serie de precios (típicamente close).
        period: Número de períodos para el promedio.

    Returns:
        Serie con SMA calculado.
    """
    result = ta.sma(series, length=period)
    if result is None:
        # Fallback: usar pandas rolling si pandas-ta falla
        return series.rolling(window=period).mean()
    return result


def ema(series: pd.Series, period: int) -> pd.Series:
    """
    Exponential Moving Average.

    Args:
        series: Serie de precios.
        period: Número de períodos.

    Returns:
        Serie con EMA calculado.
    """
    result = ta.ema(series, length=period)
    if result is None:
        return series.ewm(span=period, adjust=False).mean()
    return result


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index.

    Args:
        series: Serie de precios.
        period: Número de períodos (default 14).

    Returns:
        Serie con RSI (0-100).
    """
    result = ta.rsi(series, length=period)
    if result is None:
        # Fallback manual RSI
        delta = series.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    return result


def atr(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> pd.Series:
    """
    Average True Range.

    Args:
        high: Serie de precios high.
        low: Serie de precios low.
        close: Serie de precios close.
        period: Número de períodos (default 14).

    Returns:
        Serie con ATR.
    """
    result = ta.atr(high=high, low=low, close=close, length=period)
    if result is None:
        # Fallback manual ATR
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    return result


def bollinger_bands(
    series: pd.Series, period: int = 20, std: float = 2.0
) -> pd.DataFrame:
    """
    Bollinger Bands.

    Args:
        series: Serie de precios.
        period: Número de períodos para SMA.
        std: Número de desviaciones estándar.

    Returns:
        DataFrame con columnas [lower, mid, upper, bandwidth, percent].
    """
    return ta.bbands(series, length=period, std=std)


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """
    Moving Average Convergence Divergence.

    Args:
        series: Serie de precios.
        fast: Período EMA rápido.
        slow: Período EMA lento.
        signal: Período para línea de señal.

    Returns:
        DataFrame con columnas [MACD, histogram, signal].
    """
    return ta.macd(series, fast=fast, slow=slow, signal=signal)

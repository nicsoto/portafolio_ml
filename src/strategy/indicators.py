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
    return ta.sma(series, length=period)


def ema(series: pd.Series, period: int) -> pd.Series:
    """
    Exponential Moving Average.

    Args:
        series: Serie de precios.
        period: Número de períodos.

    Returns:
        Serie con EMA calculado.
    """
    return ta.ema(series, length=period)


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index.

    Args:
        series: Serie de precios.
        period: Número de períodos (default 14).

    Returns:
        Serie con RSI (0-100).
    """
    return ta.rsi(series, length=period)


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
    return ta.atr(high=high, low=low, close=close, length=period)


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

"""Cálculo de métricas de trading (fuera de UI)."""

import numpy as np
import pandas as pd


def calculate_sharpe(
    returns: pd.Series,
    rf: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """
    Calcula Sharpe ratio anualizado.
    
    Args:
        returns: Serie de retornos (no porcentaje, i.e., 0.01 = 1%).
        rf: Risk-free rate anualizado (default 0).
        periods_per_year: Períodos por año para anualización.
            - 252 para daily
            - 252 * 6.5 para hourly (mercado abierto)
            - 252 * 6.5 * 4 para 15min
            
    Returns:
        Sharpe ratio anualizado.
    """
    if returns.empty or returns.std() == 0:
        return 0.0

    # Convertir rf a período
    rf_per_period = rf / periods_per_year

    excess_returns = returns - rf_per_period
    sharpe = excess_returns.mean() / excess_returns.std()

    # Anualizar
    return sharpe * np.sqrt(periods_per_year)


def calculate_max_drawdown(equity: pd.Series) -> float:
    """
    Calcula maximum drawdown como porcentaje.
    
    Args:
        equity: Serie con valores del portfolio.
        
    Returns:
        Max drawdown como porcentaje negativo (e.g., -15.5).
    """
    if equity.empty:
        return 0.0

    # Running maximum
    running_max = equity.expanding().max()

    # Drawdown en cada punto
    drawdown = (equity - running_max) / running_max * 100

    return drawdown.min()


def calculate_win_rate(trades: pd.DataFrame, pnl_column: str = "pnl") -> float:
    """
    Calcula porcentaje de trades ganadores.
    
    Args:
        trades: DataFrame con trades.
        pnl_column: Nombre de la columna con P&L.
        
    Returns:
        Win rate como porcentaje (0-100).
    """
    if trades.empty or pnl_column not in trades.columns:
        return 0.0

    wins = (trades[pnl_column] > 0).sum()
    total = len(trades)

    return (wins / total) * 100 if total > 0 else 0.0


def calculate_profit_factor(trades: pd.DataFrame, pnl_column: str = "pnl") -> float:
    """
    Calcula profit factor (ganancias brutas / pérdidas brutas).
    
    Args:
        trades: DataFrame con trades.
        pnl_column: Nombre de la columna con P&L.
        
    Returns:
        Profit factor. >1 significa sistema rentable.
    """
    if trades.empty or pnl_column not in trades.columns:
        return 0.0

    pnl = trades[pnl_column]
    gross_profits = pnl[pnl > 0].sum()
    gross_losses = abs(pnl[pnl < 0].sum())

    if gross_losses == 0:
        return float("inf") if gross_profits > 0 else 0.0

    return gross_profits / gross_losses


def calculate_cagr(
    equity: pd.Series,
    periods_per_year: int = 252,
) -> float:
    """
    Calcula Compound Annual Growth Rate.
    
    Args:
        equity: Serie con valores del portfolio.
        periods_per_year: Períodos por año.
        
    Returns:
        CAGR como porcentaje.
    """
    if equity.empty or len(equity) < 2:
        return 0.0

    total_return = equity.iloc[-1] / equity.iloc[0]
    n_periods = len(equity)
    n_years = n_periods / periods_per_year

    if n_years <= 0:
        return 0.0

    cagr = (total_return ** (1 / n_years) - 1) * 100
    return cagr


def get_periods_per_year(timeframe: str) -> int:
    """
    Retorna número de períodos por año según timeframe.
    
    Args:
        timeframe: Intervalo (1d, 1h, 15m, etc).
        
    Returns:
        Períodos aproximados por año de trading.
    """
    mapping = {
        "1m": 252 * 6.5 * 60,   # ~98,280
        "5m": 252 * 6.5 * 12,   # ~19,656
        "15m": 252 * 6.5 * 4,   # ~6,552
        "30m": 252 * 6.5 * 2,   # ~3,276
        "1h": 252 * 6.5,        # ~1,638
        "1d": 252,
        "1wk": 52,
        "1mo": 12,
    }
    return mapping.get(timeframe, 252)

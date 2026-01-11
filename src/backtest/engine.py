"""Motor de backtesting usando vectorbt."""

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd
import vectorbt as vbt

from .costs import TradingCosts


@dataclass
class BacktestResult:
    """
    Resultado de un backtest.
    
    Output Contract:
        - trades: DataFrame con entry/exit time, prices, pnl, fees
        - equity: Series con curva de capital
        - stats: dict con Sharpe, drawdown, win_rate, etc.
    """

    trades: pd.DataFrame
    equity: pd.Series
    stats: dict = field(default_factory=dict)
    portfolio: object = None  # vectorbt Portfolio object

    @property
    def total_return(self) -> float:
        """Retorno total como porcentaje."""
        if self.equity.empty:
            return 0.0
        return (self.equity.iloc[-1] / self.equity.iloc[0] - 1) * 100

    @property
    def num_trades(self) -> int:
        """Número total de trades."""
        return len(self.trades)


class BacktestEngine:
    """
    Motor de backtesting wrapper de vectorbt.
    
    Features:
        - Ejecución t→t+1 (evita lookahead bias)
        - Costos y slippage configurables
        - Métricas estandarizadas
    """

    def __init__(
        self,
        initial_capital: float = 10_000.0,
        costs: TradingCosts | None = None,
    ):
        """
        Args:
            initial_capital: Capital inicial para el backtest.
            costs: Modelo de costos (default: TradingCosts()).
        """
        if initial_capital <= 0:
            raise ValueError("initial_capital must be > 0")

        self.initial_capital = initial_capital
        self.costs = costs or TradingCosts()

    def run(
        self,
        prices: pd.DataFrame,
        signals: pd.DataFrame,
        execution_delay: int = 1,
        size_pct: float = 1.0,
        sl_pct: float | None = None,
        tp_pct: float | None = None,
    ) -> BacktestResult:
        """
        Ejecuta backtest con las señales dadas.

        Args:
            prices: DataFrame OHLCV.
            signals: DataFrame con columnas 'entries' y 'exits' (bool).
            execution_delay: Delay en barras para ejecución (1 = t→t+1).
            size_pct: Porcentaje del capital a usar por trade.
            sl_pct: Stop-loss como porcentaje (e.g., 0.02 = 2% abajo del entry).
            tp_pct: Take-profit como porcentaje (e.g., 0.05 = 5% arriba del entry).

        Returns:
            BacktestResult con trades, equity y stats.
        """
        if prices.empty:
            raise ValueError("prices DataFrame is empty")
        if signals.empty:
            raise ValueError("signals DataFrame is empty")

        # Alinear índices
        common_idx = prices.index.intersection(signals.index)
        prices = prices.loc[common_idx]
        signals = signals.loc[common_idx]

        # Aplicar delay de ejecución (señal en t → ejecución en t+delay)
        # Forzar dtype bool después del shift
        entries = signals["entries"].shift(execution_delay).fillna(False).astype(bool)
        exits = signals["exits"].shift(execution_delay).fillna(False).astype(bool)

        # Usar precio de apertura para ejecución realista
        exec_price = prices["open"] if "open" in prices.columns else prices["close"]

        # Configurar stop-loss y take-profit
        sl_stop = sl_pct if sl_pct is not None else None
        tp_stop = tp_pct if tp_pct is not None else None

        # Inferir frecuencia dinámicamente del índice
        freq = pd.infer_freq(prices.index)
        if freq is None and len(prices.index) >= 2:
            # Fallback: calcular delta entre primeras dos barras
            delta = prices.index[1] - prices.index[0]
            # Convertir a string para vectorbt
            if delta.days >= 1:
                freq = f"{delta.days}D"
            elif delta.seconds >= 3600:
                freq = f"{delta.seconds // 3600}H"
            else:
                freq = f"{delta.seconds // 60}T"
        freq = freq or "1D"

        # Crear portfolio con vectorbt
        portfolio = vbt.Portfolio.from_signals(
            close=prices["close"],
            open=exec_price,
            high=prices["high"] if "high" in prices.columns else None,
            low=prices["low"] if "low" in prices.columns else None,
            entries=entries,
            exits=exits,
            init_cash=self.initial_capital,
            size=size_pct,
            size_type="percent",
            fees=self.costs.commission_pct,
            slippage=self.costs.slippage_pct,
            sl_stop=sl_stop,
            tp_stop=tp_stop,
            freq=freq,
        )

        # Extraer trades
        trades_df = self._extract_trades(portfolio)

        # Extraer equity curve
        equity = portfolio.value()

        # Calcular stats
        stats = self._calculate_stats(portfolio, trades_df)

        # Agregar info de SL/TP a stats
        stats["sl_pct"] = sl_pct
        stats["tp_pct"] = tp_pct

        return BacktestResult(
            trades=trades_df,
            equity=equity,
            stats=stats,
            portfolio=portfolio,
        )

    def _extract_trades(self, portfolio) -> pd.DataFrame:
        """Extrae tabla de trades del portfolio."""
        try:
            trades = portfolio.trades.records_readable
            if trades.empty:
                return pd.DataFrame(columns=[
                    "entry_time", "exit_time", "entry_price", "exit_price",
                    "size", "pnl", "return_pct", "duration"
                ])

            # Renombrar columnas para consistencia
            trades = trades.rename(columns={
                "Entry Timestamp": "entry_time",
                "Exit Timestamp": "exit_time",
                "Avg Entry Price": "entry_price",
                "Avg Exit Price": "exit_price",
                "Size": "size",
                "PnL": "pnl",
                "Return": "return_pct",
                "Duration": "duration",
            })

            # Seleccionar columnas relevantes
            cols = ["entry_time", "exit_time", "entry_price", "exit_price",
                    "size", "pnl", "return_pct"]
            available = [c for c in cols if c in trades.columns]
            return trades[available]

        except Exception:
            return pd.DataFrame()

    def _calculate_stats(self, portfolio, trades_df: pd.DataFrame) -> dict:
        """Calcula métricas del backtest."""
        stats = {}

        try:
            pf_stats = portfolio.stats()

            stats["total_return_pct"] = pf_stats.get("Total Return [%]", 0)
            stats["sharpe_ratio"] = pf_stats.get("Sharpe Ratio", 0)
            stats["max_drawdown_pct"] = pf_stats.get("Max Drawdown [%]", 0)
            stats["win_rate_pct"] = pf_stats.get("Win Rate [%]", 0)
            stats["profit_factor"] = pf_stats.get("Profit Factor", 0)
            stats["num_trades"] = pf_stats.get("Total Trades", 0)
            stats["avg_trade_pct"] = pf_stats.get("Avg Trade [%]", 0)

            # Convertir NaN a 0
            stats = {k: (0 if pd.isna(v) else v) for k, v in stats.items()}

        except Exception:
            stats = {
                "total_return_pct": 0,
                "sharpe_ratio": 0,
                "max_drawdown_pct": 0,
                "win_rate_pct": 0,
                "profit_factor": 0,
                "num_trades": 0,
                "avg_trade_pct": 0,
            }

        return stats

"""Generador de reportes (independiente de UI)."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ..backtest.engine import BacktestResult


@dataclass
class Report:
    """Container para un reporte generado."""

    summary: dict
    trade_log: pd.DataFrame
    equity_data: pd.Series


class ReportGenerator:
    """Genera reportes a partir de resultados de backtest."""

    def generate(self, result: BacktestResult) -> Report:
        """
        Genera reporte completo.
        
        Args:
            result: Resultado de backtest.
            
        Returns:
            Report con summary, trade_log y equity_data.
        """
        return Report(
            summary=self.generate_summary(result),
            trade_log=result.trades.copy() if not result.trades.empty else pd.DataFrame(),
            equity_data=result.equity.copy() if not result.equity.empty else pd.Series(),
        )

    def generate_summary(self, result: BacktestResult) -> dict:
        """
        Genera resumen de métricas.
        
        Args:
            result: Resultado de backtest.
            
        Returns:
            Dict con métricas clave.
        """
        stats = result.stats

        return {
            "Total Return (%)": round(stats.get("total_return_pct", 0), 2),
            "Sharpe Ratio": round(stats.get("sharpe_ratio", 0), 2),
            "Max Drawdown (%)": round(stats.get("max_drawdown_pct", 0), 2),
            "Win Rate (%)": round(stats.get("win_rate_pct", 0), 2),
            "Profit Factor": round(stats.get("profit_factor", 0), 2),
            "Total Trades": int(stats.get("num_trades", 0)),
            "Avg Trade (%)": round(stats.get("avg_trade_pct", 0), 2),
        }

    def export_to_csv(self, result: BacktestResult, path: Path | str) -> None:
        """
        Exporta trades a CSV.
        
        Args:
            result: Resultado de backtest.
            path: Path del archivo CSV.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        result.trades.to_csv(path, index=False)

    def format_summary_text(self, result: BacktestResult) -> str:
        """
        Formatea resumen como texto.
        
        Args:
            result: Resultado de backtest.
            
        Returns:
            String formateado para impresión.
        """
        summary = self.generate_summary(result)

        lines = ["=" * 40, "BACKTEST SUMMARY", "=" * 40]
        for key, value in summary.items():
            lines.append(f"{key}: {value}")
        lines.append("=" * 40)

        return "\n".join(lines)

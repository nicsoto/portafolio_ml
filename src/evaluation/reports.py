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

    def create_equity_chart(self, result: BacktestResult, benchmark: pd.Series = None) -> "go.Figure":
        """
        Crea gráfico de equity profesional.
        
        Args:
            result: Resultado del backtest.
            benchmark: Serie de benchmark (opcional).
            
        Returns:
            Plotly Figure object.
        """
        import plotly.graph_objects as go
        
        equity = result.equity
        
        fig = go.Figure()
        
        # Equity Curve
        fig.add_trace(go.Scatter(
            x=equity.index,
            y=equity,
            mode='lines',
            name='Portfolio Equity',
            line=dict(color='#00E676', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 230, 118, 0.1)'
        ))
        
        # Benchmark (si existe)
        if benchmark is not None and not benchmark.empty:
            # Rebase benchmark to match initial equity
            initial_equity = equity.iloc[0]
            initial_bench = benchmark.iloc[0]
            bench_rebased = benchmark * (initial_equity / initial_bench)
            
            fig.add_trace(go.Scatter(
                x=bench_rebased.index,
                y=bench_rebased,
                mode='lines',
                name='Benchmark (SPY)',
                line=dict(color='#A0A0A0', width=1, dash='dash'),
                opacity=0.7
            ))
            
        # Layout profesional
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=30, b=10),
            height=400,
            xaxis=dict(
                showgrid=False,
                showspikes=True,
                spikethickness=1,
                spikedash="dot",
                spikecolor="#999999",
                spikemode="across",
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#333333',
                gridwidth=1,
                zeroline=False,
            ),
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig

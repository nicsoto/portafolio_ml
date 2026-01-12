"""Monte Carlo Simulation para análisis de robustez.

Genera múltiples escenarios futuros "barajando" los retornos históricos
para calcular distribuciones de probabilidad de riqueza final, VaR, y drawdown.

Ejemplo de uso:
    simulator = MonteCarloSimulator(n_simulations=1000)
    result = simulator.simulate(returns=backtest_result.equity.pct_change().dropna())
    print(result.var_95)  # Value at Risk al 95%
"""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
import pandas as pd


@dataclass
class MonteCarloResult:
    """Resultado de simulación Monte Carlo."""
    
    # Estadísticas de retorno final
    mean_final_return: float
    median_final_return: float
    std_final_return: float
    
    # Percentiles de retorno final
    percentile_5: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    
    # Value at Risk (VaR)
    var_95: float  # Pérdida máxima con 95% de confianza
    var_99: float  # Pérdida máxima con 99% de confianza
    cvar_95: float  # Conditional VaR (Expected Shortfall)
    
    # Drawdowns
    mean_max_drawdown: float
    worst_max_drawdown: float  # Percentil 99 de max drawdown
    
    # Probabilidades
    prob_positive: float  # P(retorno > 0)
    prob_double: float    # P(retorno > 100%)
    prob_loss_50: float   # P(retorno < -50%)
    
    # Datos para gráficos
    equity_paths: np.ndarray  # Shape: (n_simulations, n_periods)
    final_returns: np.ndarray  # Shape: (n_simulations,)
    
    @property
    def summary(self) -> dict:
        """Resumen para UI."""
        return {
            "Retorno Medio": f"{self.mean_final_return*100:.1f}%",
            "VaR 95%": f"{self.var_95*100:.1f}%",
            "CVaR 95%": f"{self.cvar_95*100:.1f}%",
            "Max DD Esperado": f"{self.mean_max_drawdown*100:.1f}%",
            "P(Ganancia)": f"{self.prob_positive*100:.0f}%",
            "Simulaciones": len(self.final_returns),
        }


class MonteCarloSimulator:
    """
    Simulador Monte Carlo para análisis de robustez de estrategias.
    
    Metodología:
    1. Toma los retornos históricos de la estrategia
    2. Los "baraja" (shuffle) aleatoriamente
    3. Reconstruye curvas de capital
    4. Repite N veces para generar distribución
    """
    
    def __init__(
        self,
        n_simulations: int = 1000,
        random_seed: int = 42,
    ):
        """
        Args:
            n_simulations: Número de simulaciones a ejecutar.
            random_seed: Semilla para reproducibilidad.
        """
        self.n_simulations = n_simulations
        self.random_seed = random_seed
    
    def simulate(
        self,
        returns: pd.Series | np.ndarray,
        initial_capital: float = 10000,
    ) -> MonteCarloResult:
        """
        Ejecuta simulación Monte Carlo.
        
        Args:
            returns: Serie de retornos diarios (decimales, no porcentaje).
            initial_capital: Capital inicial para reconstruir equity.
            
        Returns:
            MonteCarloResult con estadísticas y datos para gráficos.
        """
        np.random.seed(self.random_seed)
        
        if isinstance(returns, pd.Series):
            returns = returns.dropna().values
        
        n_periods = len(returns)
        
        if n_periods < 10:
            raise ValueError("Se necesitan al menos 10 retornos para Monte Carlo")
        
        # Generar paths simulados
        equity_paths = np.zeros((self.n_simulations, n_periods + 1))
        equity_paths[:, 0] = initial_capital
        
        for sim in range(self.n_simulations):
            # Shuffle de retornos
            shuffled_returns = np.random.permutation(returns)
            
            # Reconstruir equity
            for t in range(n_periods):
                equity_paths[sim, t + 1] = equity_paths[sim, t] * (1 + shuffled_returns[t])
        
        # Calcular retornos finales
        final_equities = equity_paths[:, -1]
        final_returns = (final_equities / initial_capital) - 1
        
        # Calcular drawdowns para cada path
        max_drawdowns = []
        for sim in range(self.n_simulations):
            path = equity_paths[sim]
            running_max = np.maximum.accumulate(path)
            drawdowns = (path - running_max) / running_max
            max_drawdowns.append(drawdowns.min())
        
        max_drawdowns = np.array(max_drawdowns)
        
        # Estadísticas
        mean_final = np.mean(final_returns)
        median_final = np.median(final_returns)
        std_final = np.std(final_returns)
        
        # Percentiles
        p5, p25, p75, p95 = np.percentile(final_returns, [5, 25, 75, 95])
        
        # VaR (pérdida máxima, expresada como número negativo)
        var_95 = np.percentile(final_returns, 5)  # 5th percentile = 95% VaR
        var_99 = np.percentile(final_returns, 1)  # 1st percentile = 99% VaR
        
        # CVaR (promedio de pérdidas peores que VaR)
        cvar_95 = final_returns[final_returns <= var_95].mean()
        
        # Drawdowns
        mean_max_dd = np.mean(max_drawdowns)
        worst_max_dd = np.percentile(max_drawdowns, 1)  # Peor 1%
        
        # Probabilidades
        prob_positive = (final_returns > 0).mean()
        prob_double = (final_returns > 1.0).mean()
        prob_loss_50 = (final_returns < -0.5).mean()
        
        return MonteCarloResult(
            mean_final_return=mean_final,
            median_final_return=median_final,
            std_final_return=std_final,
            percentile_5=p5,
            percentile_25=p25,
            percentile_75=p75,
            percentile_95=p95,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95 if not np.isnan(cvar_95) else var_95,
            mean_max_drawdown=mean_max_dd,
            worst_max_drawdown=worst_max_dd,
            prob_positive=prob_positive,
            prob_double=prob_double,
            prob_loss_50=prob_loss_50,
            equity_paths=equity_paths,
            final_returns=final_returns,
        )
    
    def create_fan_chart(
        self,
        result: MonteCarloResult,
        percentiles: List[int] = [5, 25, 50, 75, 95],
    ) -> "go.Figure":
        """
        Crea gráfico "fan chart" con bandas de confianza.
        
        Args:
            result: Resultado de simulación Monte Carlo.
            percentiles: Percentiles a mostrar como bandas.
            
        Returns:
            Plotly Figure object.
        """
        import plotly.graph_objects as go
        
        equity_paths = result.equity_paths
        n_periods = equity_paths.shape[1]
        x = list(range(n_periods))
        
        fig = go.Figure()
        
        # Colores para bandas (de exterior a interior)
        colors = [
            'rgba(0, 230, 118, 0.1)',  # 5-95%
            'rgba(0, 230, 118, 0.2)',  # 25-75%
        ]
        
        # Calcular percentiles por período
        percentile_values = {}
        for p in percentiles:
            percentile_values[p] = np.percentile(equity_paths, p, axis=0)
        
        # Banda 5-95%
        fig.add_trace(go.Scatter(
            x=x + x[::-1],
            y=list(percentile_values[95]) + list(percentile_values[5])[::-1],
            fill='toself',
            fillcolor=colors[0],
            line=dict(width=0),
            name='5-95%',
            showlegend=True,
        ))
        
        # Banda 25-75%
        fig.add_trace(go.Scatter(
            x=x + x[::-1],
            y=list(percentile_values[75]) + list(percentile_values[25])[::-1],
            fill='toself',
            fillcolor=colors[1],
            line=dict(width=0),
            name='25-75%',
            showlegend=True,
        ))
        
        # Mediana
        fig.add_trace(go.Scatter(
            x=x,
            y=percentile_values[50],
            mode='lines',
            name='Mediana',
            line=dict(color='#00E676', width=2),
        ))
        
        # Layout
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title="Monte Carlo Simulation - Fan Chart",
            xaxis_title="Período",
            yaxis_title="Equity ($)",
            hovermode="x unified",
            height=400,
        )
        
        return fig

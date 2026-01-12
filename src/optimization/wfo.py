"""Walk-Forward Optimization (WFO) - Validación robusta de estrategias.

WFO divide la historia en ventanas secuenciales train/test para detectar overfitting
y medir la estabilidad de parámetros óptimos a lo largo del tiempo.

Ejemplo de uso:
    wfo = WalkForwardOptimizer(n_splits=5, train_pct=0.7)
    result = wfo.optimize(
        prices=prices,
        strategy_class=MACrossStrategy,
        param_space={'fast_period': (5, 30), 'slow_period': (20, 100)},
        n_trials=50
    )
    print(result.oos_sharpe)  # Sharpe out-of-sample agregado
"""

from dataclasses import dataclass, field
from typing import Type, Dict, Any, List, Tuple
import pandas as pd
import numpy as np
import optuna
from optuna.samplers import TPESampler

from ..strategy.base import Strategy
from ..backtest import BacktestEngine, TradingCosts


@dataclass
class WFOFold:
    """Resultado de una ventana individual de WFO."""
    fold_idx: int
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    best_params: Dict[str, Any]
    train_sharpe: float
    test_sharpe: float
    train_return: float
    test_return: float


@dataclass
class WFOResult:
    """Resultado consolidado de Walk-Forward Optimization."""
    folds: List[WFOFold]
    oos_sharpe: float  # Sharpe promedio out-of-sample
    oos_return: float  # Retorno promedio out-of-sample
    param_stability: float  # 0-1, qué tan estables son los parámetros
    is_overfit: bool  # True si train >> test (señal de overfitting)
    param_matrix: pd.DataFrame  # Parámetros por fold para heatmap
    
    @property
    def summary(self) -> Dict[str, Any]:
        """Resumen para UI."""
        return {
            "OOS Sharpe": round(self.oos_sharpe, 3),
            "OOS Return (%)": round(self.oos_return * 100, 2),
            "Param Stability": round(self.param_stability, 2),
            "Overfitting Risk": "⚠️ ALTO" if self.is_overfit else "✅ BAJO",
            "Folds": len(self.folds),
        }


class WalkForwardOptimizer:
    """
    Walk-Forward Optimization con Optuna.
    
    Divide los datos en N ventanas secuenciales. Para cada ventana:
    1. Optimiza parámetros en train con Optuna
    2. Evalúa en test (out-of-sample)
    3. Registra estabilidad de parámetros
    
    Detecta overfitting comparando rendimiento train vs test.
    """
    
    def __init__(
        self,
        n_splits: int = 5,
        train_pct: float = 0.7,
        n_trials: int = 30,
        metric: str = "sharpe",
    ):
        """
        Args:
            n_splits: Número de ventanas walk-forward.
            train_pct: Proporción de cada ventana para training.
            n_trials: Trials de Optuna por ventana.
            metric: Métrica a optimizar ('sharpe', 'return', 'sortino').
        """
        self.n_splits = n_splits
        self.train_pct = train_pct
        self.n_trials = n_trials
        self.metric = metric
    
    def _create_folds(
        self, prices: pd.DataFrame
    ) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """Divide datos en ventanas train/test secuenciales."""
        n = len(prices)
        fold_size = n // self.n_splits
        
        folds = []
        for i in range(self.n_splits):
            start_idx = i * fold_size
            end_idx = (i + 1) * fold_size if i < self.n_splits - 1 else n
            
            fold_data = prices.iloc[start_idx:end_idx]
            train_size = int(len(fold_data) * self.train_pct)
            
            train_data = fold_data.iloc[:train_size]
            test_data = fold_data.iloc[train_size:]
            
            if len(train_data) > 50 and len(test_data) > 10:
                folds.append((train_data, test_data))
        
        return folds
    
    def _backtest_strategy(
        self,
        prices: pd.DataFrame,
        strategy_class: Type[Strategy],
        params: Dict[str, Any],
    ) -> Dict[str, float]:
        """Ejecuta backtest y retorna métricas."""
        try:
            strategy = strategy_class(**params)
            signals = strategy.generate_signals(prices)
            
            engine = BacktestEngine(
                initial_capital=10000,
                costs=TradingCosts(commission_pct=0.001, slippage_pct=0.0005)
            )
            result = engine.run(prices=prices, signals=signals.signals)
            
            return {
                "sharpe": result.stats.get("sharpe_ratio", 0),
                "return": result.stats.get("total_return_pct", 0) / 100,
                "sortino": result.stats.get("sortino_ratio", 0),
            }
        except Exception:
            return {"sharpe": -10, "return": -1, "sortino": -10}
    
    def _optimize_fold(
        self,
        train_data: pd.DataFrame,
        strategy_class: Type[Strategy],
        param_space: Dict[str, Tuple[int, int]],
    ) -> Dict[str, Any]:
        """Optimiza parámetros en una ventana con Optuna."""
        
        def objective(trial: optuna.Trial) -> float:
            params = {}
            for name, (low, high) in param_space.items():
                if isinstance(low, int):
                    params[name] = trial.suggest_int(name, low, high)
                else:
                    params[name] = trial.suggest_float(name, low, high)
            
            # Validar parámetros específicos de MA Cross
            if "fast_period" in params and "slow_period" in params:
                if params["fast_period"] >= params["slow_period"]:
                    return -10  # Penalizar configuración inválida
            
            metrics = self._backtest_strategy(train_data, strategy_class, params)
            return metrics.get(self.metric, -10)
        
        # Suprimir logs de Optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        
        study = optuna.create_study(
            direction="maximize",
            sampler=TPESampler(seed=42)
        )
        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=False)
        
        return study.best_params
    
    def optimize(
        self,
        prices: pd.DataFrame,
        strategy_class: Type[Strategy],
        param_space: Dict[str, Tuple[int, int]],
    ) -> WFOResult:
        """
        Ejecuta Walk-Forward Optimization completo.
        
        Args:
            prices: DataFrame OHLCV completo.
            strategy_class: Clase de estrategia a optimizar.
            param_space: Dict con rangos de parámetros, ej: {'fast_period': (5, 30)}.
            
        Returns:
            WFOResult con métricas agregadas y por fold.
        """
        folds_data = self._create_folds(prices)
        
        if len(folds_data) < 2:
            raise ValueError("Datos insuficientes para WFO. Se necesitan al menos 2 folds válidos.")
        
        folds_results: List[WFOFold] = []
        all_params: List[Dict[str, Any]] = []
        
        for i, (train_data, test_data) in enumerate(folds_data):
            # Optimizar en train
            best_params = self._optimize_fold(train_data, strategy_class, param_space)
            all_params.append(best_params)
            
            # Evaluar en train y test
            train_metrics = self._backtest_strategy(train_data, strategy_class, best_params)
            test_metrics = self._backtest_strategy(test_data, strategy_class, best_params)
            
            fold_result = WFOFold(
                fold_idx=i,
                train_start=train_data.index.min(),
                train_end=train_data.index.max(),
                test_start=test_data.index.min(),
                test_end=test_data.index.max(),
                best_params=best_params,
                train_sharpe=train_metrics["sharpe"],
                test_sharpe=test_metrics["sharpe"],
                train_return=train_metrics["return"],
                test_return=test_metrics["return"],
            )
            folds_results.append(fold_result)
        
        # Calcular métricas agregadas
        oos_sharpes = [f.test_sharpe for f in folds_results]
        oos_returns = [f.test_return for f in folds_results]
        train_sharpes = [f.train_sharpe for f in folds_results]
        
        oos_sharpe = np.mean(oos_sharpes)
        oos_return = np.mean(oos_returns)
        train_sharpe = np.mean(train_sharpes)
        
        # Detectar overfitting: si train >> test
        is_overfit = (train_sharpe - oos_sharpe) > 0.5 or (train_sharpe > 1 and oos_sharpe < 0.3)
        
        # Calcular estabilidad de parámetros
        param_stability = self._calculate_stability(all_params)
        
        # Crear matriz de parámetros para heatmap
        param_matrix = pd.DataFrame(all_params)
        param_matrix.index = [f"Fold {i+1}" for i in range(len(all_params))]
        
        return WFOResult(
            folds=folds_results,
            oos_sharpe=oos_sharpe,
            oos_return=oos_return,
            param_stability=param_stability,
            is_overfit=is_overfit,
            param_matrix=param_matrix,
        )
    
    def _calculate_stability(self, params_list: List[Dict[str, Any]]) -> float:
        """
        Calcula estabilidad de parámetros entre folds.
        
        Retorna 0-1 donde 1 = parámetros idénticos en todos los folds.
        Usa coeficiente de variación normalizado.
        """
        if len(params_list) < 2:
            return 1.0
        
        df = pd.DataFrame(params_list)
        
        # Calcular CV (coef. de variación) para cada parámetro
        cvs = []
        for col in df.columns:
            if df[col].std() == 0:
                cvs.append(0)  # Perfectamente estable
            else:
                cv = df[col].std() / (df[col].mean() + 1e-8)
                cvs.append(cv)
        
        # Promedio de CVs, invertido y normalizado a 0-1
        avg_cv = np.mean(cvs)
        stability = 1 / (1 + avg_cv)  # Transforma a 0-1
        
        return stability

# 📈 Portafolio ML - Sistema de Backtesting de Trading

Sistema modular de backtesting para estrategias de trading, con soporte para estrategias técnicas (Moving Averages) y Machine Learning. Diseñado con arquitectura limpia de 4 capas + 2 transversales.

## 🎯 Características

- **Descarga automática de datos** con caché local (yfinance + Parquet)
- **Estrategia MA Cross** con períodos configurables
- **Estrategia ML** con RandomForest o GradientBoosting
- **Backtesting realista** con vectorbt (ejecución t→t+1, costos, slippage)
- **Stop-Loss y Take-Profit** configurables
- **Dashboard Streamlit** con gráficos interactivos
- **Comparador con benchmark** (Buy & Hold)
- **Export de trades** a CSV/Excel
- **41 tests unitarios** con pytest

## 🚀 Quick Start

```bash
# Clonar el repositorio
git clone https://github.com/nicsoto/portafolio_ml.git
cd portafolio_ml

# Instalar dependencias (requiere uv)
uv sync --extra dev

# Correr la aplicación
uv run streamlit run app/streamlit_app.py

# Correr tests
uv run pytest tests/ -v
```

## 🏗️ Arquitectura

El sistema está diseñado con separación clara de responsabilidades:

```
┌─────────────────────────────────────────────────────────────┐
│                    CAPAS TRANSVERSALES                       │
├────────────────────────┬────────────────────────────────────┤
│   Config/Experimentos  │         Evaluación/Reportes        │
│   (reproducibilidad)   │         (métricas fuera de UI)     │
└────────────────────────┴────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     CAPAS PRINCIPALES                        │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│    Data     │  Strategy   │  Backtest   │     Frontend      │
│  (OHLCV)    │ (señales)   │ (ejecución) │   (Streamlit)     │
└─────────────┴─────────────┴─────────────┴───────────────────┘
```

### Flujo de Datos

```
yfinance → DataLoader → prices (DataFrame OHLCV)
                              ↓
                        Strategy.generate_signals()
                              ↓
                        signals (entries/exits)
                              ↓
                        BacktestEngine.run()
                              ↓
                        BacktestResult (trades, equity, stats)
                              ↓
                        Streamlit (solo renderiza)
```

## 📁 Estructura del Proyecto

```
portafolio_ml/
├── app/
│   └── streamlit_app.py      # UI principal (solo renderiza)
│
├── src/
│   ├── data/                  # Capa de Datos
│   │   ├── __init__.py
│   │   ├── loader.py          # DataLoader con caché
│   │   ├── cache.py           # Gestión de Parquet
│   │   └── schemas.py         # Validación Pydantic
│   │
│   ├── strategy/              # Motor de Estrategia
│   │   ├── __init__.py
│   │   ├── base.py            # Clase abstracta Strategy
│   │   ├── indicators.py      # Wrappers pandas-ta
│   │   └── ma_cross.py        # Estrategia MA Cross
│   │
│   ├── backtest/              # Motor de Backtesting
│   │   ├── __init__.py
│   │   ├── engine.py          # Wrapper vectorbt
│   │   ├── costs.py           # Modelo de costos
│   │   └── sizing.py          # Position sizing
│   │
│   ├── evaluation/            # Reportes y Métricas
│   │   ├── __init__.py
│   │   ├── metrics.py         # Sharpe, drawdown, etc.
│   │   └── reports.py         # Generador de reportes
│   │
│   ├── config/                # Configuración
│   │   ├── __init__.py
│   │   ├── settings.py        # Pydantic Settings
│   │   └── experiments.py     # Guardado de corridas
│   │
│   └── ml/                    # Machine Learning
│       ├── __init__.py
│       ├── features.py        # Feature engineering
│       └── model.py           # MLModel y MLStrategy
│
├── tests/                     # Tests unitarios
│   ├── test_data.py
│   ├── test_strategy.py
│   ├── test_backtest.py
│   └── test_ml.py
│
├── data/                      # Caché de datos (gitignored)
│   └── raw/                   # Archivos Parquet
│
├── pyproject.toml             # Dependencias
└── README.md                  # Este archivo
```

## 📦 Módulos en Detalle

### 1. Capa de Datos (`src/data/`)

#### `DataLoader`
Descarga datos OHLCV desde yfinance con caché local en Parquet.

```python
from src.data import DataLoader

loader = DataLoader(cache_dir="data/raw")
prices, metadata = loader.load(
    ticker="SPY",
    timeframe="1d",
    use_cache=True
)
```

**Output Contract:**
- `prices`: DataFrame con columnas `[open, high, low, close, volume]` e índice DatetimeIndex
- `metadata`: `DataMetadata` con ticker, timeframe, source, timezone, rango de fechas

#### `CacheManager`
Gestiona archivos Parquet con expiración configurable.

```python
from src.data import CacheManager

cache = CacheManager(cache_dir="data/raw", max_age_hours=24)
path = cache.get_cache_path("SPY", "1d")  # → data/raw/SPY_1d.parquet
is_valid = cache.is_cache_valid(path)      # → True/False según edad
```

---

### 2. Motor de Estrategia (`src/strategy/`)

#### `Strategy` (clase base abstracta)
Define el contrato que toda estrategia debe cumplir.

```python
from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, prices: pd.DataFrame) -> SignalResult:
        """Retorna entries/exits alineados con prices."""
        pass
    
    @property
    @abstractmethod
    def params(self) -> dict:
        """Parámetros para reproducibilidad."""
        pass
```

#### `MACrossStrategy`
Estrategia de cruce de medias móviles.

```python
from src.strategy import MACrossStrategy

strategy = MACrossStrategy(fast_period=10, slow_period=50, ma_type="sma")
result = strategy.generate_signals(prices)

print(result.signals)  # DataFrame con 'entries' y 'exits' (bool)
print(result.features) # DataFrame con MAs calculadas
```

**Lógica:**
- Entry: MA rápida cruza arriba de MA lenta
- Exit: MA rápida cruza abajo de MA lenta

---

### 3. Motor de Backtesting (`src/backtest/`)

#### `BacktestEngine`
Wrapper de vectorbt con costos y ejecución realista.

```python
from src.backtest import BacktestEngine, TradingCosts

costs = TradingCosts(commission_pct=0.001, slippage_pct=0.0005)
engine = BacktestEngine(initial_capital=10000, costs=costs)

result = engine.run(
    prices=prices,
    signals=signals,
    execution_delay=1,  # Señal en t → ejecución en t+1
    sl_pct=0.05,        # Stop-loss 5%
    tp_pct=0.10,        # Take-profit 10%
)
```

**Output Contract:**
- `result.trades`: DataFrame con entry/exit time, prices, pnl
- `result.equity`: Series con curva de capital
- `result.stats`: dict con Sharpe, max_drawdown, win_rate, etc.

#### `TradingCosts`
Modelo de costos por trade.

```python
costs = TradingCosts(commission_pct=0.001, slippage_pct=0.0005)
print(costs.total_cost_pct)  # 0.003 (entry + exit)

# Ajuste de precios
buy_price = costs.apply_to_price(100, is_buy=True)   # 100.15
sell_price = costs.apply_to_price(100, is_buy=False) # 99.85
```

#### Position Sizing

```python
from src.backtest import calculate_position_size

# Arriesgar 1% del capital con stop-loss
size = calculate_position_size(
    capital=10000,
    risk_pct=0.01,
    entry_price=100,
    stop_loss_price=95,
)
# → 20 acciones (si baja a 95, pierdes $100 = 1% de $10k)
```

---

### 4. Evaluación (`src/evaluation/`)

#### Métricas (independientes de UI)

```python
from src.evaluation import calculate_sharpe, calculate_max_drawdown

# Sharpe anualizado
sharpe = calculate_sharpe(returns, rf=0.0, periods_per_year=252)

# Max drawdown
mdd = calculate_max_drawdown(equity)  # → -15.5 (porcentaje)
```

#### ReportGenerator

```python
from src.evaluation import ReportGenerator

generator = ReportGenerator()
report = generator.generate(backtest_result)

print(report.summary)     # Dict con métricas
generator.export_to_csv(backtest_result, "trades.csv")
```

---

### 5. Configuración (`src/config/`)

#### Settings (Pydantic)

```python
from src.config import Settings

settings = Settings()  # Carga desde .env si existe
print(settings.initial_capital)  # 10000.0
print(settings.commission_pct)   # 0.001
```

#### ExperimentRun (reproducibilidad)

```python
from src.config import ExperimentRun

run = ExperimentRun(
    ticker="SPY",
    timeframe="1d",
    strategy_name="MACross",
    strategy_params={"fast": 10, "slow": 50},
    results={"sharpe": 1.5, "return": 25.3},
)
run.save("data/experiments")  # → JSON para reproducir
```

---

### 6. Machine Learning (`src/ml/`)

#### `FeatureEngineer`
Genera 30+ features técnicos desde OHLCV.

```python
from src.ml import FeatureEngineer

fe = FeatureEngineer()
features = fe.create_features(prices)

# Features incluidos:
# - return_1d, return_5d, return_10d, return_20d
# - sma_5, sma_10, sma_20, sma_50, close_to_sma_*
# - rsi, rsi_oversold, rsi_overbought
# - atr, atr_pct, volatility_5d, volatility_20d
# - macd, macd_signal, macd_hist
# - bb_position, bb_width
# - volume_ratio, volume_change
# - momentum_5d, momentum_10d, momentum_20d
```

#### `MLModel`
Wrapper para modelos de clasificación.

```python
from src.ml import MLModel

# Entrenar
model = MLModel(model_type="random_forest")
metrics = model.train(X, y, test_size=0.2, cv_folds=5)

print(metrics.accuracy)           # 0.65
print(metrics.feature_importance) # Dict con importancia por feature

# Predecir
predictions = model.predict(X_new)      # [0, 1, 1, 0, ...]
probabilities = model.predict_proba(X)  # [0.3, 0.7, 0.8, ...]

# Guardar/cargar
model.save("model.pkl")
loaded_model = MLModel.load("model.pkl")
```

#### `MLStrategy`
Estrategia basada en predicciones del modelo.

```python
from src.ml import MLStrategy

strategy = MLStrategy(
    model=trained_model,
    feature_engineer=fe,
    entry_threshold=0.6,  # Entry si P(subida) > 60%
    exit_threshold=0.4,   # Exit si P(subida) < 40%
)

result = strategy.generate_signals(prices)
```

---

## 🖥️ Frontend (Streamlit)

La UI en `app/streamlit_app.py` **solo renderiza**. Toda la lógica financiera vive en las capas.

### Features de la UI:
- Selector de ticker y timeframe
- Selector de estrategia (MA Cross vs ML)
- Parámetros configurables por estrategia
- Stop-loss y Take-profit opcionales
- Gráfico de velas con señales
- Curva de equity vs benchmark (Buy & Hold)
- Tabla de trades con métricas
- Export a CSV/Excel
- Guardado/carga de configuración

---

## 🧪 Tests

```bash
# Correr todos los tests
uv run pytest tests/ -v

# Correr con coverage
uv run pytest tests/ --cov=src --cov-report=html

# Tests por módulo
uv run pytest tests/test_data.py -v
uv run pytest tests/test_strategy.py -v
uv run pytest tests/test_backtest.py -v
uv run pytest tests/test_ml.py -v
```

### Cobertura de Tests:
- **test_data.py**: CacheManager, OHLCVBar, DataMetadata
- **test_strategy.py**: MACrossStrategy, SignalResult
- **test_backtest.py**: TradingCosts, position sizing
- **test_ml.py**: FeatureEngineer, MLModel, MLStrategy

---

## ⚙️ Dependencias

| Paquete | Uso |
|---------|-----|
| `pandas` | Manipulación de datos |
| `numpy` | Operaciones numéricas |
| `pandas-ta` | Indicadores técnicos |
| `vectorbt` | Motor de backtesting |
| `yfinance` | Descarga de datos |
| `scikit-learn` | Modelos ML |
| `pydantic` | Validación de datos |
| `streamlit` | Frontend |
| `plotly` | Gráficos interactivos |
| `pyarrow` | Parquet I/O |
| `openpyxl` | Export Excel |

---

## 📝 Licencia

MIT

---

## 🤝 Contribuir

1. Fork el repositorio
2. Crea un feature branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'feat: nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

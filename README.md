# 📈 Portafolio ML - Sistema de Trading con Backtesting e IA

Sistema modular de trading algorítmico con backtesting, Machine Learning y ejecución en vivo. Soporta Alpaca (acciones US) y MetaTrader 5 (Forex/CFDs).

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Tests](https://img.shields.io/badge/tests-16%20passed-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🎯 Características Principales

### Backtesting
- **Descarga automática de datos** con caché local (yfinance + Parquet)
- **Ejecución realista** con vectorbt (señal t → ejecución t+1 al open)
- **Costos de trading** (comisiones + slippage)
- **Stop-Loss y Take-Profit** configurables
- **Position sizing** basado en riesgo

### Estrategias
- **MA Cross**: Cruce de medias móviles (SMA/EMA)
- **Machine Learning**: RandomForest/GradientBoosting/XGBoost
- **30+ features técnicos**: RSI, MACD, Bollinger, ATR, etc.

### Análisis Avanzado
- **Walk-Forward Optimization** (WFO) con Optuna
- **Monte Carlo Simulation** con VaR/CVaR
- **PDF Alpha Report** estilo factsheet profesional

### Trading en Vivo
- **Alpaca Paper Trading**: Acciones US ($100k virtuales)
- **MetaTrader 5**: Forex/CFDs via FileCommander bridge
- **Bots automatizados** que corren 24/5

### UI
- **Dashboard Next.js** (nuevo) con diseño premium fintech
- **Dashboard Streamlit** con gráficos interactivos
- **API FastAPI** para integración con frontend
- **Métricas completas**: Sharpe, Sortino, Calmar, Profit Factor
- **Feature Importance** para modelos ML
- **Export** a CSV/Excel/PDF

---

## 🚀 Quick Start

### Requisitos
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (gestor de paquetes)

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/nicsoto/portafolio_ml.git
cd portafolio_ml

# Instalar dependencias
uv sync --extra dev

# Configurar Alpaca (opcional)
cp .env.example .env
# Editar .env con tus API keys
```

### Uso Básico

```bash
# Dashboard Next.js (moderno)
cd frontend && npm run dev
# Abrir http://localhost:3000

# API Backend (requerido para Next.js)
uv run uvicorn api:app --reload --port 8000

# Dashboard Streamlit (alternativo)
uv run streamlit run app/streamlit_app.py

# Correr tests
uv run pytest tests/ -v

# Bot Alpaca (acciones US)
uv run python scripts/live_bot.py --ticker SPY --interval 5

# Bot MT5 (Forex)
uv run python scripts/live_bot_mt5.py --symbol EURUSD --strategy ml

# Generar informe semanal
uv run python scripts/generate_report.py --period week
```

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    CAPAS TRANSVERSALES                       │
├────────────────────────┬────────────────────────────────────┤
│   Config/Experimentos  │         Evaluación/Reportes        │
│   (reproducibilidad)   │         (métricas + PDF)           │
└────────────────────────┴────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     CAPAS PRINCIPALES                        │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│    Data     │  Strategy   │  Backtest   │    Execution      │
│  (OHLCV)    │ (señales)   │ (simulación)│  (Alpaca/MT5)     │
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
          ┌───────────────────┴───────────────────┐
          ↓                                       ↓
   BacktestEngine.run()              AlpacaExecutor / MT5Executor
   (simulación histórica)              (ejecución en vivo)
          ↓                                       ↓
   BacktestResult                          OrderLog (SQLite)
   (trades, equity, stats)
```

---

## 📁 Estructura del Proyecto

```
portafolio_ml/
├── app/
│   ├── streamlit_app.py          # Dashboard principal
│   └── pages/
│       └── 1_Live_Trading.py     # Dashboard Alpaca en vivo
│
├── src/
│   ├── data/                     # Capa de Datos
│   │   ├── loader.py             # DataLoader con caché + validaciones
│   │   ├── cache.py              # Gestión de Parquet
│   │   └── schemas.py            # Validación Pydantic
│   │
│   ├── strategy/                 # Motor de Estrategia
│   │   ├── base.py               # Clase abstracta Strategy
│   │   ├── indicators.py         # Wrappers pandas-ta
│   │   └── ma_cross.py           # Estrategia MA Cross
│   │
│   ├── backtest/                 # Motor de Backtesting
│   │   ├── engine.py             # Wrapper vectorbt (18+ métricas)
│   │   ├── costs.py              # Modelo de costos
│   │   └── sizing.py             # Position sizing basado en riesgo
│   │
│   ├── ml/                       # Machine Learning
│   │   ├── features.py           # 30+ features técnicos (sin lookahead)
│   │   └── model.py              # MLModel + MLStrategy
│   │
│   ├── evaluation/               # Análisis Avanzado
│   │   ├── metrics.py            # Sharpe, Sortino, Calmar, etc.
│   │   ├── reports.py            # Generador de reportes
│   │   ├── monte_carlo.py        # Monte Carlo Simulation
│   │   ├── pdf_report.py         # Alpha Report (PDF)
│   │   └── wfo.py                # Walk-Forward Optimization
│   │
│   ├── optimization/             # Optimización
│   │   └── wfo.py                # WFO con Optuna
│   │
│   ├── execution/                # Trading en Vivo
│   │   ├── alpaca_engine.py      # Executor Alpaca + SQLite logging
│   │   └── mt5_executor.py       # Executor MT5 (via FileCommander)
│   │
│   └── config/                   # Configuración
│       ├── settings.py           # Pydantic Settings
│       └── experiments.py        # Guardado de corridas
│
├── scripts/
│   ├── live_bot.py               # Bot automatizado Alpaca
│   └── live_bot_mt5.py           # Bot automatizado MT5
│
├── mt5/
│   ├── FileCommander.mq5         # Expert Advisor para comunicación
│   └── FileCommander.ex5         # Compilado
│
├── tests/                        # 16+ tests unitarios
│   ├── test_data.py
│   ├── test_strategy.py
│   ├── test_backtest.py
│   └── test_ml.py
│
├── data/                         # Datos (gitignored)
│   ├── raw/                      # Caché Parquet
│   ├── orders.db                 # Log de órdenes Alpaca
│   └── mt5_orders.db             # Log de órdenes MT5
│
├── logs/                         # Logs de bots
│   ├── bot.log                   # Alpaca
│   └── bot_mt5.log               # MT5
│
├── .env                          # API keys (gitignored)
├── pyproject.toml                # Dependencias
└── README.md
```

---

## 📊 Módulos en Detalle

### 1. Capa de Datos (`src/data/`)

```python
from src.data import DataLoader

loader = DataLoader(cache_dir="data/raw")
prices, metadata = loader.load(
    ticker="SPY",
    timeframe="1d",  # 1m, 5m, 15m, 30m, 1h, 1d, 1wk
    use_cache=True
)
# Validaciones automáticas: duplicados, gaps, NaN, precios inválidos
```

### 2. Estrategias (`src/strategy/`)

```python
from src.strategy import MACrossStrategy

strategy = MACrossStrategy(fast_period=10, slow_period=50, ma_type="sma")
result = strategy.generate_signals(prices)
# result.signals: DataFrame con 'entries' y 'exits' (bool)
# result.features: DataFrame con indicadores calculados
```

### 3. Backtesting (`src/backtest/`)

```python
from src.backtest import BacktestEngine, TradingCosts

costs = TradingCosts(commission_pct=0.001, slippage_pct=0.0005)
engine = BacktestEngine(initial_capital=10000, costs=costs)

result = engine.run(
    prices=prices,
    signals=signals,
    execution_delay=1,  # Señal t → ejecución t+1 al open
    sl_pct=0.05,        # Stop-loss 5%
    tp_pct=0.10,        # Take-profit 10%
)
# result.trades: DataFrame con entry/exit, pnl, returns
# result.equity: Series con curva de capital
# result.stats: 18+ métricas (sharpe, sortino, calmar, etc.)
```

### 4. Machine Learning (`src/ml/`)

```python
from src.ml import FeatureEngineer, MLModel, MLStrategy

# Feature engineering (con shift(1) para evitar lookahead)
fe = FeatureEngineer()
features, target = fe.prepare_dataset(prices, horizon=1)

# Entrenar modelo
model = MLModel(model_type="random_forest")  # o gradient_boosting, xgboost
metrics = model.train(features, target, test_size=0.2)
print(f"Accuracy: {metrics.accuracy:.2%}")

# Crear estrategia
strategy = MLStrategy(
    model=model,
    feature_engineer=fe,
    entry_threshold=0.6,  # Entry si P(subida) > 60%
    exit_threshold=0.4,   # Exit si P(subida) < 40%
)
```

### 5. Análisis Avanzado (`src/evaluation/`)

```python
# Walk-Forward Optimization
from src.optimization import WalkForwardOptimizer
wfo = WalkForwardOptimizer(n_splits=5, train_pct=0.7, n_trials=30)
wfo_result = wfo.optimize(strategy_class, prices, param_space)

# Monte Carlo Simulation
from src.evaluation import MonteCarloSimulator
mc = MonteCarloSimulator(n_simulations=1000)
mc_result = mc.simulate(returns, initial_capital=10000)
print(f"VaR 95%: {mc_result.var_95:.2%}")

# PDF Report
from src.evaluation import AlphaReportGenerator
generator = AlphaReportGenerator()
pdf_bytes = generator.generate(backtest_result, strategy_name="ML Strategy")
```

### 6. Ejecución en Vivo (`src/execution/`)

```python
# Alpaca (acciones US)
from src.execution import AlpacaExecutor
executor = AlpacaExecutor()  # Lee API keys de .env
account = executor.get_account()  # {'equity': 100000, 'cash': 100000, ...}
order = executor.place_order("SPY", qty=10, side="buy")

# MetaTrader 5 (Forex)
from src.execution import MT5Executor
executor = MT5Executor()  # Requiere FileCommander corriendo en MT5
account = executor.get_account()  # {'balance': 100000, 'equity': 100000, ...}
order = executor.buy("EURUSD", volume=0.01)
```

---

## 🤖 Bots Automatizados

### Bot Alpaca (acciones US)

```bash
# Ejecutar manualmente
uv run python scripts/live_bot.py --ticker SPY --interval 5

# Dejar en background
nohup uv run python scripts/live_bot.py --ticker SPY --interval 60 &

# Ver logs
tail -f logs/bot.log
```

### Bot MT5 (Forex)

**Requisitos previos:**
1. MetaTrader 5 instalado (via Wine en Linux)
2. FileCommander.ex5 adjunto a un gráfico
3. "Allow algo trading" activado

```bash
# Ejecutar con estrategia MA Cross
uv run python scripts/live_bot_mt5.py --symbol EURUSD --strategy ma_cross

# Ejecutar con estrategia ML
uv run python scripts/live_bot_mt5.py --symbol EURUSD --strategy ml --volume 0.01

# Background
nohup uv run python scripts/live_bot_mt5.py --symbol EURUSD --strategy ml &
```

---

## ⚙️ Configuración

### Variables de Entorno (`.env`)

```bash
# Alpaca Paper Trading
ALPACA_API_KEY=tu_api_key
ALPACA_SECRET_KEY=tu_secret_key
ALPACA_PAPER=true
```

### Obtener API Keys de Alpaca

1. Ir a [alpaca.markets](https://alpaca.markets/)
2. Crear cuenta (gratis)
3. Ir a Paper Trading → API Keys
4. Copiar keys a `.env`

---

## 🧪 Tests

```bash
# Todos los tests
uv run pytest tests/ -v

# Con coverage
uv run pytest tests/ --cov=src --cov-report=html

# Tests específicos
uv run pytest tests/test_backtest.py -v  # Incluye tests de ejecución t+1
uv run pytest tests/test_ml.py -v        # Incluye test de lookahead bias
```

### Tests de Confiabilidad

| Test | Verifica |
|------|----------|
| `test_entry_executes_at_next_open` | Señal t → ejecución open t+1 |
| `test_exit_executes_at_next_open` | Salida t → ejecución open t+1 |
| `test_sharpe_daily_uses_252_periods` | Annualización correcta (252 días) |
| `test_sharpe_hourly_uses_more_periods` | Annualización horaria (1638 horas) |
| `test_feature_creation_no_lookahead` | Features usan solo datos pasados |

---

## 📦 Dependencias

| Paquete | Versión | Uso |
|---------|---------|-----|
| `pandas` | ≥2.0.0 | Manipulación de datos |
| `numpy` | ≥1.24.0 | Operaciones numéricas |
| `pandas-ta` | ≥0.3.14b | Indicadores técnicos |
| `vectorbt` | ≥0.26.0 | Motor de backtesting |
| `yfinance` | ≥0.2.0 | Descarga de datos |
| `scikit-learn` | ≥1.4.0 | Modelos ML |
| `xgboost` | ≥2.0.0 | XGBoost (opcional) |
| `lightgbm` | ≥4.0.0 | LightGBM (opcional) |
| `optuna` | ≥3.0.0 | Walk-Forward Optimization |
| `reportlab` | ≥4.4.7 | PDF reports |
| `alpaca-trade-api` | ≥3.2.0 | Trading Alpaca |
| `streamlit` | ≥1.30.0 | Dashboard |
| `plotly` | ≥5.18.0 | Gráficos interactivos |
| `pydantic` | ≥2.0.0 | Validación de datos |

---

## 📝 Notas Técnicas

### Anti-Lookahead Bias

- **Features**: `df.shift(1)` aplicado al final de `FeatureEngineer.create_features()`
- **Target**: Calculado con datos futuros pero solo para training
- **Ejecución**: Señal t → orden ejecutada al `open` de t+1
- **Live bots**: Usan vela cerrada (`iloc[-2]`) para señales

### Validación de Datos Intradía

El `DataLoader` valida automáticamente:
- Timestamps duplicados
- Gaps en datos (overnight/weekends)
- Rango de datos vs límites de yfinance
- Valores NaN
- Precios cero o negativos

---

## 🤝 Contribuir

1. Fork el repositorio
2. Crea un feature branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'feat: nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📄 Licencia

MIT

---

## 👤 Autor

**Nico Soto**
- GitHub: [@nicsoto](https://github.com/nicsoto)

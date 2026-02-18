# 📊 Informe Detallado del Proyecto: Portafolio ML Trading

> **Autor**: Nicolás Soto  
> **Última actualización**: Febrero 2026  
> **Estado**: En desarrollo activo  

---

## 1. Resumen Ejecutivo

Este proyecto es un **framework completo de trading algorítmico con Machine Learning**, desarrollado en Python. Integra múltiples componentes:

- **Backtesting** vectorizado con VectorBT
- **Modelos ML** (LightGBM, XGBoost, Random Forest)
- **Ejecución automatizada** con Alpaca (acciones US) y MetaTrader 5 (Forex/CFDs)
- **Participación en Numerai** (torneo de predicción de hedge fund)
- **Dashboard interactivo** con Streamlit y Next.js
- **Generación de reportes** PDF profesionales
- **Optimización** Walk-Forward y Monte Carlo

---

## 2. Arquitectura del Proyecto

### 2.1 Estructura de Archivos

```
portafolio_ml/
├── src/                          # Código fuente principal
│   ├── backtest/
│   │   ├── engine.py             # Motor de backtesting (VectorBT)
│   │   ├── costs.py              # Modelo de costos de trading
│   │   └── sizing.py             # Sizing de posiciones
│   ├── config/
│   │   ├── settings.py           # Configuración global
│   │   └── experiments.py        # Configuración de experimentos
│   ├── data/
│   │   ├── loader.py             # Carga de datos (yfinance)
│   │   ├── cache.py              # Cache de datos
│   │   └── schemas.py            # Esquemas de validación
│   ├── evaluation/
│   │   ├── metrics.py            # Métricas de performance
│   │   ├── monte_carlo.py        # Simulación Monte Carlo
│   │   ├── reports.py            # Generación de reportes
│   │   └── pdf_report.py         # Reportes en PDF
│   ├── execution/
│   │   ├── alpaca_engine.py      # Ejecución vía Alpaca API
│   │   └── mt5_executor.py       # Ejecución vía MetaTrader 5
│   ├── ml/
│   │   ├── model.py              # Modelos ML (clasificación)
│   │   ├── features.py           # Feature engineering
│   │   └── optimization.py       # Optuna hyperparameter tuning
│   ├── optimization/
│   │   └── wfo.py                # Walk-Forward Optimization
│   ├── strategy/
│   │   ├── base.py               # Clase base de estrategia
│   │   ├── ma_cross.py           # Estrategia Moving Average Cross
│   │   └── indicators.py         # Indicadores técnicos
│   └── ui/
│       └── styles.py             # Estilos del dashboard
├── scripts/
│   ├── live_bot.py               # Bot de trading Alpaca
│   ├── live_bot_mt5.py           # Bot de trading MT5
│   ├── numerai_submission.py     # Submissions a Numerai
│   ├── numerai_round.py          # Info de rondas Numerai
│   └── generate_report.py        # Generación de PDF reports
├── app/                          # Dashboard Streamlit
├── frontend/                     # Frontend Next.js
├── mt5/                          # Expert Advisors MetaTrader 5
│   ├── SocketServer.mq5          # Servidor de sockets
│   └── FileCommander.mq5         # Comandos por archivo
├── api.py                        # FastAPI backend
├── models/                       # Modelos entrenados (.pkl)
└── data/                         # Datos y cache
```

### 2.2 Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| **Lenguaje** | Python 3.13 |
| **ML** | LightGBM, XGBoost, scikit-learn |
| **Backtesting** | VectorBT |
| **Datos** | yfinance, Numerai API |
| **Ejecución** | Alpaca API, MetaTrader 5 |
| **Dashboard** | Streamlit, Next.js |
| **API** | FastAPI |
| **Optimización** | Optuna, Walk-Forward |
| **Gestión de paquetes** | uv (astral) |
| **Infraestructura** | AWS EC2 (Linux) |

---

## 3. Componentes Detallados

### 3.1 Motor de Backtesting

**Archivo**: `src/backtest/engine.py`

Motor vectorizado construido sobre VectorBT que ejecuta backtests con:

- **Ejecución t→t+1**: Evita lookahead bias asegurando que las señales generadas en el cierre de la barra `t` se ejecutan al precio de apertura de `t+1`.
- **Costos configurables**: Comisiones, spread, slippage modelados en `costs.py`.
- **Stop Loss / Take Profit**: Implementados como porcentaje del precio de entrada.
- **Position Sizing**: Fracción del capital por operación configurable.

**Métricas calculadas**:
- Sharpe Ratio
- Sortino Ratio
- Max Drawdown
- Win Rate
- Profit Factor
- Total Return
- Calmar Ratio
- Total Trades

### 3.2 Estrategias de Trading

#### Moving Average Cross (MA Cross)

**Archivo**: `src/strategy/ma_cross.py`

Estrategia clásica de cruce de medias móviles:
- **Entry**: Cuando la media rápida cruza arriba de la media lenta.
- **Exit**: Cuando la media rápida cruza abajo de la media lenta.
- **Parámetros default**: `fast_period=5`, `slow_period=20`

#### ML Strategy

**Archivo**: `src/ml/model.py`

Estrategia basada en predicciones de un modelo de clasificación:
- **Entry**: Cuando el modelo predice subida con probabilidad > `entry_threshold` (default 0.6).
- **Exit**: Cuando la probabilidad cae por debajo de `exit_threshold` (default 0.4).
- **Features**: 50+ indicadores técnicos generados automáticamente.

### 3.3 Feature Engineering

**Archivo**: `src/ml/features.py`

Genera más de 50 features técnicos incluyendo:
- **Returns**: 1d, 2d, 5d, 10d, 20d
- **Volatilidad**: Rolling std 5d, 10d, 20d
- **RSI**: 14 períodos
- **MACD**: Línea, señal, histograma
- **Bollinger Bands**: Upper, lower, width, %B
- **ATR**: 14 períodos
- **Volume**: Ratio vs media

### 3.4 Modelos ML

**Archivo**: `src/ml/model.py`

Clase `MLModel` wrapper que soporta múltiples algoritmos:

| Modelo | Clase | Tipo |
|--------|-------|------|
| Random Forest | `RandomForestClassifier` | Clasificación |
| Gradient Boosting | `GradientBoostingClassifier` | Clasificación |
| XGBoost | `XGBClassifier` | Clasificación |
| LightGBM | `LGBMClassifier` | Clasificación |

**Funcionalidades**:
- Validación cruzada temporal (`TimeSeriesSplit`)
- Escalado automático de features
- Feature importance
- Serialización (save/load)

### 3.5 Optimización

#### Walk-Forward Optimization (WFO)

**Archivo**: `src/optimization/wfo.py`

Divide los datos en ventanas móviles:
1. **In-sample**: Entrena el modelo / optimiza parámetros
2. **Out-of-sample**: Evalúa performance sin sesgo

Evita overfitting temporal al validar en datos no vistos.

#### Hyperparameter Tuning con Optuna

**Archivo**: `src/ml/optimization.py`

Búsqueda automática de hiperparámetros óptimos usando Optuna:
- Bayesian optimization
- Pruning de trials no prometedores
- Cross-validation como métrica de optimización

#### Monte Carlo Simulation

**Archivo**: `src/evaluation/monte_carlo.py`

Simula 1000+ escenarios futuros basados en la distribución de trades históricos:
- Percentiles de retorno (5th, 50th, 95th)
- Probabilidad de ruina
- Distribution de drawdowns

---

## 4. Alpaca Paper Trading

### 4.1 Configuración

**Motor de ejecución**: `src/execution/alpaca_engine.py`

Se conecta con Alpaca Paper Trading API para ejecutar órdenes reales (con dinero ficticio):

- **Tipo**: Paper Trading (simulado)
- **Capital inicial**: $100,000 USD
- **Broker**: Alpaca Markets
- **Activo**: SPY (S&P 500 ETF)

**Variables de entorno** (`.env`):
```
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...
ALPACA_PAPER=true
```

### 4.2 Bot de Trading

**Archivo**: `scripts/live_bot.py`

Bot automatizado que corre en loop continuo:

```
Inicio → ¿Mercado abierto? → Cargar datos → Generar señales → ¿Entry? → Comprar
                                                              → ¿Exit?  → Vender
                                                              → Nada → Esperar intervalo
```

**Parámetros de ejecución**:
```bash
uv run python scripts/live_bot.py --ticker SPY --strategy ma_cross --interval 60
```

- Revisa señales cada 60 minutos
- Usa 10% del capital por operación
- Log en `logs/bot.log`

### 4.3 Resultados Alpaca

**Período de operación**: Enero 2026

**Estado de cuenta** (revisado el 13 de enero 2026):

| Métrica | Valor |
|---------|-------|
| **Equity** | $99,998.17 |
| **Cash** | $99,998.17 |
| **Buying Power** | $199,996.34 |
| **P/L acumulado** | -$1.83 |

**Órdenes ejecutadas**:

| Fecha | Acción | Símbolo | Precio | Status |
|-------|--------|---------|--------|--------|
| 12 Ene 2026 | BUY | SPY | $694.61 | ✅ FILLED |
| 13 Ene 2026 | SELL | SPY | $692.79 | ✅ FILLED |

**Análisis**: El bot compró 1 acción de SPY a $694.61 y la vendió al día siguiente a $692.79, generando una pérdida de $1.82 (0.26%). El bot mantuvo la posición esperando señal de salida durante varias horas, y finalmente vendió cuando el precio bajó.

### 4.4 Bot MetaTrader 5

**Archivo**: `scripts/live_bot_mt5.py`

Bot adicional para operar Forex/CFDs a través de MetaTrader 5:
- Comunicación vía sockets o archivos (FileCommander)
- Expert Advisors en MQL5
- Soporte para EURUSD y otros pares

---

## 5. Numerai Tournament

### 5.1 ¿Qué es Numerai?

Numerai es un hedge fund que crowdsourcea modelos de predicción. Los participantes entrenan modelos con datos encriptados de Numerai y suben predicciones. Si las predicciones son buenas, ganan NMR (criptomoneda).

### 5.2 Integración con el Framework

**Archivo**: `scripts/numerai_submission.py`

Script que automatiza el flujo de Numerai:
1. Descarga datos del torneo (`v5.2` dataset)
2. Entrena un modelo LightGBM Regressor
3. Genera predicciones
4. Las sube vía API

**Variables de entorno**:
```
NUMERAI_PUBLIC_ID=...
NUMERAI_SECRET_KEY=...
```

### 5.3 Desafíos Encontrados y Soluciones

#### Problema 1: RAM insuficiente

**Problema**: El dataset de Numerai es de ~2.5 GB. Leerlo completo requiere >16 GB de RAM, lo que causaba SIGKILL tanto en la PC local como en Google Colab gratuito.

**Solución implementada**:
- Leer solo columnas necesarias con `pyarrow.parquet`
- Usar subsets de features (30-50 de 2376 disponibles)
- Samplear un porcentaje de los datos (10-30%)
- Era sampling (cada N eras) para mantener representatividad temporal

#### Problema 2: Clasificación vs Regresión

**Problema**: La clase `MLModel` del framework usa clasificadores (`LGBMClassifier`), pero Numerai requiere regresión (targets continuos).

**Error**: `ValueError: Unknown label type: continuous`

**Solución**: Usar `LGBMRegressor` directamente en vez del wrapper `MLModel`.

#### Problema 3: Formato del modelo para upload

**Problema**: Numerai espera un objeto **callable** que retorne un `pd.DataFrame`, no un modelo sklearn raw.

**Error secuencia**:
1. `TypeError: LGBMRegressor is not a callable object` → Necesita `__call__`
2. `SystemError: no locals when deleting` → Problemas de serialización con closures
3. `returned numpy.ndarray instead of pd.DataFrame` → Necesita retornar DataFrame
4. `values must be between 0 and 1` → Necesita normalizar predicciones

**Solución final**: Crear clase wrapper con `__call__`:

```python
class NumeraiModel:
    def __init__(self, model, features):
        self.model = model
        self.features = list(features)
    
    def __call__(self, live_features):
        available = [f for f in self.features if f in live_features.columns]
        preds = self.model.predict(live_features[available])
        return pd.DataFrame(
            preds, 
            index=live_features.index, 
            columns=["prediction"]
        )
```

#### Problema 4: Incompatibilidad de Python

**Problema**: El proyecto usa Python 3.13, pero Numerai solo soporta hasta Python 3.12.

**Solución**: Entrenar y serializar el modelo en Google Colab (Python 3.12) usando `cloudpickle`.

### 5.4 Evolución de Modelos

Se iteraron **4 versiones** de modelos para Numerai:

#### Modelo Original (Colab default)
- **Origen**: Notebook "Hello Numerai" estándar
- **Features**: Todas las disponibles
- **Target**: `target` (default)

| Métrica | Valor |
|---------|-------|
| Sharpe Ratio | 0.90 |
| CORR20v2 | 0.0126 |
| Max Drawdown | -7.9% |
| Feature Exposure | 0.28 |

#### Modelo V1 (Primer intento local)
- **Features**: Primeras 30 (aleatorias)
- **Datos**: 10% del dataset
- **Estimators**: 300
- **Target**: `target`

| Métrica | Valor |
|---------|-------|
| Sharpe Ratio | 0.28 |
| CORR20v2 | 0.0033 |
| Max Drawdown | -21.0% |
| Feature Exposure | 0.15 |

**Análisis**: Rendimiento pobre por usar muy pocas features elegidas al azar.

#### Modelo V2 (Optimizado) ⭐ **Mejor modelo**
- **Features**: Set "medium" curado por Numerai (~600)
- **Datos**: Era sampling cada 5 eras
- **Estimators**: 500, learning_rate=0.01
- **Target**: `target`
- **Regularización**: `colsample_bytree=0.1`, `subsample=0.8`

| Métrica | Valor |
|---------|-------|
| Sharpe Ratio | **1.16** |
| CORR20v2 | **0.0184** |
| Max Drawdown | **-7.0%** |
| Feature Exposure | 0.26 |

**Análisis**: Superó al modelo original en todas las métricas. Las mejoras clave fueron usar features curadas y era sampling.

#### Modelo V3 (Intento de reducir Feature Exposure)
- **Features**: Set "small" (~50)
- **Datos**: 10% sample
- **Estimators**: 800
- **Target**: `target`
- **Parámetros agresivos**: `colsample_bytree=0.05`, `subsample=0.5`

| Métrica | Valor |
|---------|-------|
| Sharpe Ratio | 0.81 |
| CORR20v2 | 0.0106 |
| Max Drawdown | -7.5% |
| Feature Exposure | **0.47** |

**Análisis**: Paradójicamente aumentó Feature Exposure. Usar menos features hizo que el modelo dependiera más de las pocas disponibles.

### 5.5 Comparativa Final de Modelos

| Métrica | Original | V1 | **V2** ⭐ | V3 |
|---------|----------|----|---------|----|
| Sharpe | 0.90 | 0.28 | **1.16** | 0.81 |
| CORR20v2 | 0.0126 | 0.0033 | **0.0184** | 0.0106 |
| Max DD | -7.9% | -21.0% | **-7.0%** | -7.5% |
| Feat. Exp. | 0.28 | **0.15** | 0.26 | 0.47 |

### 5.6 Performance en Vivo (Rondas Reales)

**Modelo TRAD_BOT_V4** (basado en modelo v2 con medium features):

**Período evaluado**: Rondas 1180 - 1192 (Enero 2026)

#### Rondas con mejor performance:

| Ronda | Close | CORR20 | MMC20 |
|-------|-------|--------|-------|
| 1191 | 22 Ene | **+0.0316** | **+0.0161** |
| 1192 | 23 Ene | **+0.0133** | **+0.0027** |
| 1190 | 21 Ene | +0.0075 | -0.0011 |

#### Rondas con peor performance:

| Ronda | Close | CORR20 | MMC20 |
|-------|-------|--------|-------|
| 1184 | 19 Ene | -0.0482 | -0.0401 |
| 1185 | 20 Ene | -0.0174 | -0.0244 |
| 1182 | 15 Ene | -0.0061 | -0.0217 |

#### Estadísticas agregadas:

| Métrica | Todas (13 rondas) | Últimas 3 |
|---------|-------------------|-----------|
| Promedio CORR20 | -0.0018 | **+0.0175** |
| Promedio MMC20 | -0.0103 | **+0.0059** |

#### Model Correlations (indicadores de crowding):

| Métrica | Valor | Interpretación |
|---------|-------|----------------|
| CWMM | 0.3500 | Moderado (alineación con meta) |
| MCWNM | **0.7411** | Alto (crowding con otros modelos) |
| APCWNM | 0.2685 | Moderado |

**Análisis**: Las primeras rondas tuvieron CORR negativo, pero las últimas 3 muestran mejora. El MCWNM alto (0.74) indica que el modelo es muy similar a otros en el torneo, lo que afecta negativamente el MMC.

### 5.7 Próximos Pasos Numerai

1. **Ensemble multi-target**: Combinar modelos entrenados con diferentes targets (`target`, `target_cyrus_v4_20`, `target_nomi_v4_20`) para reducir crowding
2. **Esperar resolución**: Las rondas 1180-1192 se resuelven en Feb 2026
3. **No stakear NMR** hasta tener 10+ rondas resueltas con CORR positivo consistente
4. **Reducir feature exposure** mediante neutralización o ensembles ortogonales

---

## 6. APIs y Endpoints

### 6.1 FastAPI Backend

**Archivo**: `api.py`

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/backtest` | POST | Ejecuta backtest con parámetros |
| `/strategies` | GET | Lista estrategias disponibles |
| `/tickers` | GET | Lista tickers soportados |

```bash
# Iniciar API
uv run uvicorn api:app --reload --port 8000
```

### 6.2 Dashboard Streamlit

**Directorio**: `app/`

Dashboard interactivo multipage:
- **Home**: Métricas generales
- **Live Trading**: Control del bot Alpaca
- **Backtesting**: Ejecución de backtests visuales
- **Monte Carlo**: Simulación de escenarios

```bash
uv run streamlit run app/Dashboard.py --server.port 8501
```

### 6.3 Frontend Next.js

**Directorio**: `frontend/`

Interfaz web moderna con:
- Panel de métricas
- Gráficos de equity interactivos
- Control de backtests

```bash
cd frontend && npm run dev
```

---

## 7. Infraestructura

### 7.1 Entorno Local
- **OS**: Fedora Linux
- **RAM**: ~8 GB
- **Python**: 3.13.11
- **Package Manager**: uv (astral)

### 7.2 AWS EC2
- Instancia para correr bots 24/7
- MetaTrader 5 vía Wine
- Bots Alpaca en background con `nohup`

### 7.3 Google Colab
- Usado para entrenar modelos de Numerai (Python 3.12)
- GPU gratuita disponible
- Limitaciones de RAM (~12 GB en versión gratuita)

---

## 8. Dependencias Principales

```toml
# pyproject.toml
dependencies = [
    "pandas",
    "numpy",
    "vectorbt",
    "yfinance",
    "lightgbm",
    "xgboost",
    "scikit-learn",
    "optuna",
    "streamlit",
    "plotly",
    "fastapi",
    "uvicorn",
    "python-dotenv",
    "alpaca-py",
    "alpaca-trade-api",
    "numerapi",
    "cloudpickle",
    "joblib",
    "reportlab",
    "pyarrow",
]
```

---

## 9. Comandos Útiles

### Backtesting
```bash
# Ejecutar backtest simple
uv run python -c "
from src.data import DataLoader
from src.strategy import MACrossStrategy
from src.backtest import BacktestEngine
loader = DataLoader()
prices, _ = loader.load('SPY')
strategy = MACrossStrategy()
signals = strategy.generate_signals(prices)
engine = BacktestEngine()
result = engine.run(prices, signals.signals)
print(result.stats)
"
```

### Trading Bots
```bash
# Bot Alpaca
uv run python scripts/live_bot.py --ticker SPY --strategy ma_cross --interval 60

# Bot MT5
uv run python scripts/live_bot_mt5.py --symbol EURUSD --interval 60
```

### Numerai
```bash
# Entrenar modelo local (30% datos, 50 features)
uv run python scripts/numerai_submission.py --train --sample 0.3

# Generar y subir predicciones
uv run python scripts/numerai_submission.py --predict --upload
```

### Dashboard
```bash
# Streamlit
uv run streamlit run app/Dashboard.py

# FastAPI
uv run uvicorn api:app --reload

# Next.js Frontend
cd frontend && npm run dev
```

### Reportes
```bash
# Generar reporte PDF
uv run python scripts/generate_report.py
```

---

## 10. Lecciones Aprendidas

### 10.1 Técnicas

1. **Lookahead Bias**: Fue una de las primeras correcciones críticas. Las señales se ejecutan en t+1, no en t, para evitar resultados inflados.

2. **RAM Management**: El dataset de Numerai (2.5 GB) enseñó la importancia de leer solo las columnas necesarias y usar sampling inteligente.

3. **Serialización ML**: Los modelos deben ser serializados en la misma versión de Python donde se ejecutarán. Python 3.13 → 3.12 no es compatible.

4. **Feature Exposure en Numerai**: Usar menos features no siempre reduce exposure. A veces tiene el efecto contrario si las pocas features restantes son muy correlacionadas.

5. **Era Sampling vs Random Sampling**: Seleccionar eras espaciadas temporalmente preserva mejor la estructura temporal que un sample random.

### 10.2 De Negocio

1. **Crowding en Numerai**: Un modelo que se parece mucho a otros (MCWNM alto) no aporta al meta-model y recibe MMC negativo.

2. **Diversificación de targets**: Entrenar con múltiples targets reduce correlación con el crowd.

3. **No stakear prematuramente**: Esperar resultados finales de al menos 10 rondas antes de poner NMR en riesgo.

---

## 11. Historial de Cambios Clave

| Fecha | Cambio |
|-------|--------|
| Dic 2025 | Creación del framework base (backtest, strategy, data) |
| Dic 2025 | Implementación de ML features y modelos |
| Dic 2025 | Corrección de lookahead bias en backtesting |
| Ene 2026 | Integración de Alpaca Paper Trading |
| Ene 2026 | Bot de trading automatizado con MA Cross |
| Ene 2026 | Integración de MetaTrader 5 vía sockets |
| Ene 2026 | Dashboard Streamlit y Frontend Next.js |
| Ene 2026 | Walk-Forward Optimization y Monte Carlo |
| Ene 2026 | Integración con Numerai Tournament |
| Ene 2026 | Iteración de modelos Numerai (v1 → v3) |
| Ene 2026 | Primera operación real en Alpaca (SPY) |
| Feb 2026 | Análisis de rondas resueltas en Numerai |
| Feb 2026 | Desarrollo de modelo ensemble multi-target |

---

## 12. Archivos de Modelos Generados

| Archivo | Tamaño | Descripción |
|---------|--------|-------------|
| `models/numerai_model.pkl` | 870 KB | Modelo v1 (dict con modelo + features) |
| `models/numerai_model_only.pkl` | 889 KB | Modelo v1 raw |
| `models/numerai_callable.pkl` | 891 KB | Modelo v1 como función callable |
| `models/numerai_class.pkl` | 892 KB | Modelo v1 como clase callable |
| `models/modelo_v2.pkl` | 1.7 MB | Modelo v2 (medium features, mejor performance) |

---

*Este informe fue generado como documentación técnica del proyecto portafolio_ml.*

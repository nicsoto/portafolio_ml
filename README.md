# Portafolio ML - Sistema de Backtesting

Sistema modular de backtesting de trading con arquitectura de 4 capas + 2 transversales.

## Quick Start

```bash
# Instalar dependencias
uv sync

# Correr la app
streamlit run app/streamlit_app.py

# Correr tests
pytest tests/ -v
```

## Arquitectura

- **Capa de Datos**: Descarga y caché de OHLCV
- **Motor de Estrategia**: Generación de señales
- **Motor de Backtesting**: Ejecución con vectorbt
- **Frontend**: Streamlit (solo renderiza)
- **Config**: Reproducibilidad de experimentos
- **Evaluación**: Métricas fuera de UI

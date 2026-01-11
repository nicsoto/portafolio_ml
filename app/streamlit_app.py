"""
Streamlit App - Trading Backtester

UI que SOLO renderiza, sin lógica financiera.
La lógica vive en las capas: data, strategy, backtest, evaluation.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.data import DataLoader
from src.strategy import MACrossStrategy
from src.backtest import BacktestEngine, TradingCosts
from src.evaluation import ReportGenerator
from src.config import Settings, ExperimentRun

# Page config
st.set_page_config(
    page_title="Trading Backtester",
    page_icon="📈",
    layout="wide",
)

# Load settings
settings = Settings()
settings.ensure_directories()


def main():
    st.title("📈 Trading Backtester")
    st.markdown("*Sistema modular de backtesting con arquitectura limpia*")

    # Sidebar - Parameters
    with st.sidebar:
        st.header("⚙️ Parámetros")

        # Data params
        st.subheader("📊 Datos")
        ticker = st.text_input("Ticker", value="SPY").upper()
        timeframe = st.selectbox(
            "Timeframe",
            options=["1d", "1h", "15m"],
            index=0,
        )

        # Strategy params
        st.subheader("🎯 Estrategia MA Cross")
        fast_period = st.slider("Período MA Rápida", min_value=5, max_value=50, value=10)
        slow_period = st.slider("Período MA Lenta", min_value=20, max_value=200, value=50)

        if fast_period >= slow_period:
            st.error("⚠️ MA rápida debe ser menor que MA lenta")
            return

        # Backtest params
        st.subheader("💰 Backtest")
        initial_capital = st.number_input(
            "Capital Inicial ($)",
            min_value=1000,
            max_value=1_000_000,
            value=int(settings.initial_capital),
            step=1000,
        )
        commission = st.number_input(
            "Comisión (%)",
            min_value=0.0,
            max_value=1.0,
            value=settings.commission_pct * 100,
            step=0.01,
            format="%.3f",
        ) / 100
        slippage = st.number_input(
            "Slippage (%)",
            min_value=0.0,
            max_value=1.0,
            value=settings.slippage_pct * 100,
            step=0.01,
            format="%.3f",
        ) / 100

        # Risk Management
        st.subheader("🛡️ Gestión de Riesgo")
        use_sl = st.checkbox("Usar Stop-Loss", value=False)
        sl_pct = None
        if use_sl:
            sl_pct = st.slider(
                "Stop-Loss (%)",
                min_value=1.0,
                max_value=20.0,
                value=5.0,
                step=0.5,
            ) / 100

        use_tp = st.checkbox("Usar Take-Profit", value=False)
        tp_pct = None
        if use_tp:
            tp_pct = st.slider(
                "Take-Profit (%)",
                min_value=1.0,
                max_value=50.0,
                value=10.0,
                step=0.5,
            ) / 100

        # Run button
        run_backtest = st.button("🚀 Ejecutar Backtest", type="primary", use_container_width=True)

    # Main area
    if run_backtest:
        with st.spinner("Cargando datos..."):
            result = execute_backtest(
                ticker=ticker,
                timeframe=timeframe,
                fast_period=fast_period,
                slow_period=slow_period,
                initial_capital=initial_capital,
                commission=commission,
                slippage=slippage,
                sl_pct=sl_pct,
                tp_pct=tp_pct,
            )

        if result is None:
            return

        prices, signals, backtest_result, metadata = result

        # Metrics row
        display_metrics(backtest_result)

        # Charts
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Precio y Señales")
            display_price_chart(prices, signals)

        with col2:
            st.subheader("📈 Curva de Equity")
            display_equity_chart(backtest_result)

        # Trades table
        st.markdown("---")
        st.subheader("📋 Historial de Trades")
        display_trades_table(backtest_result)

        # Metadata
        with st.expander("ℹ️ Metadata del Dataset"):
            st.json({
                "ticker": metadata.ticker,
                "timeframe": metadata.timeframe,
                "source": metadata.source,
                "timezone": metadata.timezone,
                "bars": metadata.bar_count,
                "start": str(metadata.start_date),
                "end": str(metadata.end_date),
            })

    else:
        # Welcome message
        st.info(
            "👈 Configura los parámetros en el sidebar y presiona **Ejecutar Backtest** "
            "para comenzar."
        )

        st.markdown("""
        ### 🏗️ Arquitectura del Sistema

        | Capa | Responsabilidad |
        |------|-----------------|
        | **Data** | Descarga y caché de OHLCV |
        | **Strategy** | Generación de señales |
        | **Backtest** | Ejecución con costos |
        | **Evaluation** | Métricas y reportes |
        | **Config** | Reproducibilidad |

        > 💡 **Regla de oro:** Esta UI solo renderiza, la lógica financiera vive en las capas.
        """)


def execute_backtest(
    ticker: str,
    timeframe: str,
    fast_period: int,
    slow_period: int,
    initial_capital: float,
    commission: float,
    slippage: float,
    sl_pct: float | None = None,
    tp_pct: float | None = None,
):
    """Ejecuta el pipeline completo de backtest."""
    try:
        # 1. Cargar datos
        loader = DataLoader(cache_dir=settings.data_cache_dir)
        prices, metadata = loader.load(ticker=ticker, timeframe=timeframe)

        if prices.empty:
            st.error(f"❌ No se encontraron datos para {ticker}")
            return None

        st.success(f"✅ Cargados {len(prices)} barras de {ticker}")

        # 2. Generar señales
        strategy = MACrossStrategy(fast_period=fast_period, slow_period=slow_period)
        signal_result = strategy.generate_signals(prices)

        num_entries = signal_result.signals["entries"].sum()
        risk_info = ""
        if sl_pct:
            risk_info += f" | SL: {sl_pct*100:.1f}%"
        if tp_pct:
            risk_info += f" | TP: {tp_pct*100:.1f}%"
        st.info(f"🎯 Estrategia {strategy.name}: {num_entries} señales{risk_info}")

        # 3. Ejecutar backtest
        costs = TradingCosts(commission_pct=commission, slippage_pct=slippage)
        engine = BacktestEngine(initial_capital=initial_capital, costs=costs)
        result = engine.run(
            prices=prices,
            signals=signal_result.signals,
            sl_pct=sl_pct,
            tp_pct=tp_pct,
        )

        return prices, signal_result, result, metadata

    except Exception as e:
        st.error(f"❌ Error: {e}")
        return None


def display_metrics(result):
    """Muestra métricas principales en cards."""
    stats = result.stats

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        value = stats.get("total_return_pct", 0)
        st.metric(
            "Total Return",
            f"{value:.2f}%",
            delta_color="normal" if value >= 0 else "inverse",
        )

    with col2:
        st.metric("Sharpe Ratio", f"{stats.get('sharpe_ratio', 0):.2f}")

    with col3:
        value = stats.get("max_drawdown_pct", 0)
        st.metric(
            "Max Drawdown",
            f"{value:.2f}%",
            delta_color="inverse",
        )

    with col4:
        st.metric("Win Rate", f"{stats.get('win_rate_pct', 0):.1f}%")

    with col5:
        st.metric("Trades", int(stats.get("num_trades", 0)))


def display_price_chart(prices, signal_result):
    """Muestra gráfico de precios con señales."""
    fig = make_subplots(rows=1, cols=1)

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=prices.index,
            open=prices["open"],
            high=prices["high"],
            low=prices["low"],
            close=prices["close"],
            name="OHLC",
        )
    )

    # Moving averages from features
    if signal_result.features is not None:
        for col in signal_result.features.columns:
            if col.startswith("ma_"):
                fig.add_trace(
                    go.Scatter(
                        x=prices.index,
                        y=signal_result.features[col],
                        mode="lines",
                        name=col.upper(),
                        line=dict(width=1),
                    )
                )

    # Entry signals
    entries = signal_result.signals["entries"]
    entry_prices = prices.loc[entries, "close"]
    fig.add_trace(
        go.Scatter(
            x=entry_prices.index,
            y=entry_prices,
            mode="markers",
            name="Entry",
            marker=dict(symbol="triangle-up", size=12, color="green"),
        )
    )

    # Exit signals
    exits = signal_result.signals["exits"]
    exit_prices = prices.loc[exits, "close"]
    fig.add_trace(
        go.Scatter(
            x=exit_prices.index,
            y=exit_prices,
            mode="markers",
            name="Exit",
            marker=dict(symbol="triangle-down", size=12, color="red"),
        )
    )

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=400,
        margin=dict(l=0, r=0, t=0, b=0),
    )

    st.plotly_chart(fig, use_container_width=True)


def display_equity_chart(result):
    """Muestra curva de equity."""
    if result.equity.empty:
        st.warning("No hay datos de equity para mostrar")
        return

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=result.equity.index,
            y=result.equity.values,
            mode="lines",
            name="Portfolio Value",
            fill="tozeroy",
            line=dict(color="rgb(0, 150, 255)"),
        )
    )

    # Add horizontal line at initial capital
    initial = result.equity.iloc[0]
    fig.add_hline(
        y=initial,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Initial: ${initial:,.0f}",
    )

    fig.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=0, b=0),
        yaxis_title="Portfolio Value ($)",
    )

    st.plotly_chart(fig, use_container_width=True)


def display_trades_table(result):
    """Muestra tabla de trades."""
    if result.trades.empty:
        st.warning("No hay trades para mostrar")
        return

    # Format for display
    trades = result.trades.copy()

    # Add formatting
    if "pnl" in trades.columns:
        trades["pnl"] = trades["pnl"].apply(lambda x: f"${x:,.2f}")
    if "return_pct" in trades.columns:
        trades["return_pct"] = trades["return_pct"].apply(lambda x: f"{x*100:.2f}%")

    st.dataframe(trades, use_container_width=True)

    # Export button
    if st.button("📥 Exportar CSV"):
        csv = result.trades.to_csv(index=False)
        st.download_button(
            label="Descargar trades.csv",
            data=csv,
            file_name="trades.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()

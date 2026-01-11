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
from src.ml import FeatureEngineer, MLModel, MLStrategy
from src.ui.styles import apply_styles

# Page config
st.set_page_config(
    page_title="Trading Backtester Pro",
    page_icon="📈",
    layout="wide",
)

# Load settings
settings = Settings()
settings.ensure_directories()


def main():
    apply_styles()
    
    # Header
    st.title("⚡ Trading Backtester Pro")
    st.markdown("""
    <div style='background-color: #1E1E1E; padding: 1rem; border-radius: 10px; border: 1px solid #333; margin-bottom: 2rem;'>
        Backtesting institucional y Machine Learning avanzado.
    </div>
    """, unsafe_allow_html=True)

    # Sidebar - Parameters
    with st.sidebar:
        st.header("⚙️ Configuración")
        st.markdown("---")

        # Data params
        st.subheader("📊 Datos")
        ticker = st.text_input("Ticker", value="SPY").upper()
        timeframe = st.selectbox(
            "Timeframe",
            options=["1d", "1h", "15m"],
            index=0,
        )

        # Strategy selection
        st.subheader("🎯 Estrategia")
        strategy_type = st.selectbox(
            "Tipo de Estrategia",
            options=["MA Cross", "Machine Learning"],
            index=0,
        )

        # MA Cross params
        if strategy_type == "MA Cross":
            fast_period = st.slider("Período MA Rápida", min_value=5, max_value=50, value=10)
            slow_period = st.slider("Período MA Lenta", min_value=20, max_value=200, value=50)
            if fast_period >= slow_period:
                st.error("⚠️ MA rápida debe ser menor que MA lenta")
                return
            ml_model_type = None
            ml_threshold = None
            optimize_params = False
        else:
            # ML params
            fast_period = None
            slow_period = None
            ml_model_type = st.selectbox(
                "Modelo ML",
                options=["random_forest", "gradient_boosting", "xgboost", "lightgbm"],
                index=0,
            )
            ml_threshold = st.slider(
                "Threshold de Entrada",
                min_value=0.5,
                max_value=0.9,
                value=0.6,
                step=0.05,
                help="Probabilidad mínima para generar señal de entrada"
            )
            
            # Optimization controls
            st.divider()
            optimize_params = st.checkbox(
                "✨ Optimizar Hiperparámetros (Optuna)",
                help="Busca automáticamente la mejor configuración (tarda más)"
            )
            if optimize_params:
                n_trials = st.slider("Intentos de optimización", 10, 100, 20)
            else:
                n_trials = 0

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

        # Save/Load configuration
        st.markdown("---")
        with st.expander("💾 Guardar/Cargar Config"):
            # Current config as dict
            current_config = {
                "ticker": ticker,
                "timeframe": timeframe,
                "fast_period": fast_period,
                "slow_period": slow_period,
                "initial_capital": initial_capital,
                "commission": commission,
                "slippage": slippage,
                "sl_pct": sl_pct,
                "tp_pct": tp_pct,
            }
            
            # Download current config
            import json
            config_json = json.dumps(current_config, indent=2)
            st.download_button(
                label="📥 Exportar Config",
                data=config_json,
                file_name=f"config_{ticker}_{timeframe}.json",
                mime="application/json",
                use_container_width=True,
            )
            
            # Upload config
            uploaded_file = st.file_uploader(
                "📤 Cargar Config",
                type=["json"],
                help="Sube un archivo JSON con configuración guardada"
            )
            if uploaded_file is not None:
                try:
                    loaded_config = json.load(uploaded_file)
                    st.success(f"✅ Config cargada: {loaded_config.get('ticker', 'N/A')}")
                    st.json(loaded_config)
                    st.info("👆 Aplica estos valores manualmente en los campos de arriba")
                except Exception as e:
                    st.error(f"Error cargando config: {e}")

        # Run button
        run_backtest = st.button("🚀 Ejecutar Backtest", type="primary", use_container_width=True)

    # Main area
    if run_backtest:
        with st.spinner("Cargando datos..."):
            result = execute_backtest(
                ticker=ticker,
                timeframe=timeframe,
                strategy_type=strategy_type,
                fast_period=fast_period,
                slow_period=slow_period,
                ml_model_type=ml_model_type,
                ml_threshold=ml_threshold,
                initial_capital=initial_capital,
                commission=commission,
                slippage=slippage,
                sl_pct=sl_pct,
                tp_pct=tp_pct,
                optimize_params=optimize_params,
                n_trials=n_trials,
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
            st.subheader("📈 Equity vs Buy & Hold")
            display_equity_chart(backtest_result, prices=prices, initial_capital=initial_capital)

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
    ticker: str, timeframe: str, strategy_type: str,
    fast_period: int | None, slow_period: int | None,
    ml_model_type: str | None, ml_threshold: float | None,
    initial_capital: float, commission: float, slippage: float,
    sl_pct: float | None = None, tp_pct: float | None = None,
    optimize_params: bool = False, n_trials: int = 20,
):
    """Ejecuta el pipeline completo de backtest."""
    try:
        # 1. Cargar datos
        loader = DataLoader()
        prices, metadata = loader.load(ticker, timeframe=timeframe)

        if prices.empty:
            st.error(f"❌ No se encontraron datos para {ticker}")
            return None

        st.success(f"✅ Cargados {len(prices)} barras de {ticker}")

        # 2. Generar señales según tipo de estrategia
        if strategy_type == "MA Cross":
            strategy = MACrossStrategy(fast_period=fast_period, slow_period=slow_period)
            signal_result = strategy.generate_signals(prices)
        else:
            # Estrategia ML
            from src.ml.optimization import ModelOptimizer
            import numpy as np # Import numpy for mean/std in CV scores
            
            fe = FeatureEngineer()
            
            # Preparar dataset
            # Nota: para entrenamiento usamos horizonte=1 (predicción siguiente vela)
            # Podría ser parámetro configurable
            features, target = fe.prepare_dataset(prices, horizon=1, dropna=True)
            
            # Separar train/test (simple split temporal 80/20)
            train_size = int(len(features) * 0.8)
            X_train = features.iloc[:train_size]
            y_train = target.iloc[:train_size]
            X_test = features.iloc[train_size:]
            y_test = target.iloc[train_size:]
            
            # Optimización de hiperparámetros si se solicita
            model_params = None
            if optimize_params:
                with st.spinner(f"✨ Optimizando {ml_model_type} con Optuna ({n_trials} intentos)..."):
                    optimizer = ModelOptimizer(n_trials=n_trials, cv_folds=5)
                    best_params = optimizer.optimize(X_train, y_train, model_type=ml_model_type)
                    st.success("✅ Optimización completada!")
                    with st.expander("Ver mejores parámetros"):
                        st.json(best_params)
                    model_params = best_params

            # Entrenar modelo
            with st.spinner(f"Entrenando modelo {ml_model_type}..."):
                model = MLModel(
                    model_type=ml_model_type,
                    model_params=model_params
                )
                metrics = model.train(X_train, y_train)
                
                # Mostrar métricas ML en sidebar o expander
                with st.expander("📊 Métricas del Modelo (Training/Test Split)", expanded=True):
                    cols = st.columns(4)
                    cols[0].metric("Accuracy", f"{metrics.accuracy:.2%}")
                    cols[1].metric("Precision", f"{metrics.precision:.2%}")
                    cols[2].metric("Recall", f"{metrics.recall:.2%}")
                    cols[3].metric("F1 Score", f"{metrics.f1:.2%}")
                    
                    if metrics.cv_scores:
                        st.caption(f"CV Score (TimeSplit): {np.mean(metrics.cv_scores):.3f} ± {np.std(metrics.cv_scores):.3f}")

                # Estrategia ML
                strategy = MLStrategy(
                    model=model,
                    feature_engineer=fe,
                    entry_threshold=ml_threshold
                )
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
        import traceback
        st.code(traceback.format_exc())
        return None


def display_results(result, prices, signals, metadata, ml_model_type, ml_threshold, timeframe, initial_capital):
    """Muestra métricas principales en cards y gráficos."""
    if result:
        # Layout con Tabs
        tab_overview, tab_analysis, tab_ml = st.tabs(["📈 Resumen", "🔍 Estructura", "🧠 Modelo ML"])
        
        with tab_overview:
            # Top Metrics Row
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            stats = result.stats
            
            def render_metric(col, label, value, delta=None):
                col.markdown(f"""
                <div class="css-1r6slb0" style="padding: 1rem; border-radius: 0.5rem; background-color: #262730; border: 1px solid #363945; margin-bottom: 1rem;">
                    <span style="font-size: 0.8rem; color: #a0a0a0; text-transform: uppercase;">{label}</span>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #ffffff;">{value}</div>
                </div>
                """, unsafe_allow_html=True)

            render_metric(col_m1, "Retorno Total", f"{stats['total_return_pct']:.1f}%")
            render_metric(col_m2, "Sharpe Ratio", f"{stats['sharpe_ratio']:.2f}")
            render_metric(col_m3, "Max Drawdown", f"{stats['max_drawdown_pct']:.1f}%")
            render_metric(col_m4, "Win Rate", f"{stats['win_rate_pct']:.1f}%")
            
            # Equity Chart (Professional)
            st.subheader("Curva de Equity")
            
            # Obtener benchmark data (SPY) para comparar
            loader = DataLoader() # Sin caché para benchmark rápido
            bench_prices, _ = loader.load("SPY", timeframe=timeframe)
            benchmark = bench_prices["close"] if not bench_prices.empty else None
            
            # Alinear benchmark temporalmente
            if benchmark is not None:
                benchmark = benchmark.reindex(result.equity.index).fillna(method='ffill')
            
            report_gen = ReportGenerator()
            fig_equity = report_gen.create_equity_chart(result, benchmark=benchmark)
            st.plotly_chart(fig_equity, use_container_width=True)
            
        with tab_analysis:
            st.subheader("Detalle de Operaciones")
            display_trades_table(result)
            
        with tab_ml:
            if ml_model_type:
                st.info(f"Modelo: {ml_model_type.upper()} | Threshold: {ml_threshold}")
            else:
                st.warning("Esta estrategia no usa Machine Learning.")


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


def display_equity_chart(result, prices=None, initial_capital=10000):
    """Muestra curva de equity con benchmark opcional."""
    if result.equity.empty:
        st.warning("No hay datos de equity para mostrar")
        return

    fig = go.Figure()

    # Portfolio equity
    fig.add_trace(
        go.Scatter(
            x=result.equity.index,
            y=result.equity.values,
            mode="lines",
            name="Estrategia",
            fill="tozeroy",
            line=dict(color="rgb(0, 150, 255)", width=2),
        )
    )

    # Benchmark: Buy & Hold
    if prices is not None and not prices.empty:
        # Calcular equity de buy & hold
        initial_price = prices["close"].iloc[0]
        shares = initial_capital / initial_price
        benchmark_equity = prices["close"] * shares
        
        fig.add_trace(
            go.Scatter(
                x=benchmark_equity.index,
                y=benchmark_equity.values,
                mode="lines",
                name="Buy & Hold",
                line=dict(color="rgb(255, 165, 0)", width=2, dash="dash"),
            )
        )

    # Add horizontal line at initial capital
    initial = result.equity.iloc[0]
    fig.add_hline(
        y=initial,
        line_dash="dot",
        line_color="gray",
        annotation_text=f"Initial: ${initial:,.0f}",
    )

    fig.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis_title="Portfolio Value ($)",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)


def display_trades_table(result):
    """Muestra tabla de trades con formato mejorado."""
    if result.trades.empty:
        st.warning("No hay trades para mostrar")
        return

    # Format for display
    trades = result.trades.copy()

    # Calcular métricas adicionales si hay trades
    if not trades.empty and "pnl" in trades.columns:
        winning_trades = trades[trades["pnl"] > 0]
        losing_trades = trades[trades["pnl"] < 0]
        
        # Mostrar resumen de trades
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Trades", len(trades))
        with col2:
            st.metric("Ganadores", len(winning_trades), delta=f"{len(winning_trades)/len(trades)*100:.0f}%" if len(trades) > 0 else "0%")
        with col3:
            avg_win = winning_trades["pnl"].mean() if len(winning_trades) > 0 else 0
            st.metric("Promedio Ganador", f"${avg_win:,.2f}")
        with col4:
            avg_loss = losing_trades["pnl"].mean() if len(losing_trades) > 0 else 0
            st.metric("Promedio Perdedor", f"${avg_loss:,.2f}")

    # Formatear columnas para display
    display_trades = trades.copy()
    if "pnl" in display_trades.columns:
        display_trades["pnl_formatted"] = display_trades["pnl"].apply(lambda x: f"${x:,.2f}")
    if "return_pct" in display_trades.columns:
        display_trades["return_formatted"] = display_trades["return_pct"].apply(lambda x: f"{x*100:.2f}%")
    if "entry_price" in display_trades.columns:
        display_trades["entry_price"] = display_trades["entry_price"].apply(lambda x: f"${x:,.2f}")
    if "exit_price" in display_trades.columns:
        display_trades["exit_price"] = display_trades["exit_price"].apply(lambda x: f"${x:,.2f}")

    # Seleccionar columnas para mostrar
    display_cols = []
    col_rename = {}
    if "entry_time" in display_trades.columns:
        display_cols.append("entry_time")
        col_rename["entry_time"] = "Entrada"
    if "exit_time" in display_trades.columns:
        display_cols.append("exit_time")
        col_rename["exit_time"] = "Salida"
    if "entry_price" in display_trades.columns:
        display_cols.append("entry_price")
        col_rename["entry_price"] = "Precio Entrada"
    if "exit_price" in display_trades.columns:
        display_cols.append("exit_price")
        col_rename["exit_price"] = "Precio Salida"
    if "type" in display_trades.columns:
        display_cols.append("type")
        col_rename["type"] = "Tipo"
    if "pnl_formatted" in display_trades.columns:
        display_cols.append("pnl_formatted")
        col_rename["pnl_formatted"] = "P&L"
    if "return_formatted" in display_trades.columns:
        display_cols.append("return_formatted")
        col_rename["return_formatted"] = "Retorno"

    # Mostrar tabla con estilo
    st.dataframe(
        display_trades[display_cols].rename(columns=col_rename),
        use_container_width=True,
        hide_index=True
    )

    # Export options
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        csv = trades.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name="trades.csv",
            mime="text/csv",
            use_container_width=True,
        )
    
    with col2:
        # Excel export
        try:
            import io
            buffer = io.BytesIO()
            # Copiar trades y remover timezone de columnas datetime
            trades_for_excel = trades.copy()
            for col in trades_for_excel.columns:
                if hasattr(trades_for_excel[col], 'dt') and hasattr(trades_for_excel[col].dt, 'tz'):
                    if trades_for_excel[col].dt.tz is not None:
                        trades_for_excel[col] = trades_for_excel[col].dt.tz_localize(None)
            trades_for_excel.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            st.download_button(
                label="📊 Descargar Excel",
                data=buffer,
                file_name="trades.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as e:
            st.warning("Para exportar a Excel, instala openpyxl: pip install openpyxl")


if __name__ == "__main__":
    main()

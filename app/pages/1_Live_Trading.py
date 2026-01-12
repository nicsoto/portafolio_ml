"""
Live Trading Dashboard - Alpaca Paper Trading

Página de Streamlit para monitorear y ejecutar trades en tiempo real.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="Live Trading",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #1E1E1E;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #333;
    }
    .positive { color: #00E676; }
    .negative { color: #FF5252; }
</style>
""", unsafe_allow_html=True)


def main():
    st.title("⚡ Live Trading Dashboard")
    st.markdown("*Alpaca Paper Trading - Real-time monitoring*")
    
    # Check connection
    try:
        from src.execution import AlpacaExecutor
        executor = AlpacaExecutor()
        connected = True
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        st.info("Verifica tu archivo `.env` con las credenciales de Alpaca")
        connected = False
        return
    
    # Account info header
    account = executor.get_account()
    market = executor.get_market_hours()
    
    col1, col2, col3, col4to = st.columns(4)
    
    with col1:
        st.metric("💰 Equity", f"${account['equity']:,.2f}")
    with col2:
        st.metric("💵 Cash", f"${account['cash']:,.2f}")
    with col3:
        st.metric("🔥 Buying Power", f"${account['buying_power']:,.2f}")
    with col4to:
        market_status = "🟢 Abierto" if market['is_open'] else "🔴 Cerrado"
        st.metric("📈 Mercado", market_status)
    
    st.divider()
    
    # Tabs
    tab_positions, tab_orders, tab_execute = st.tabs([
        "📊 Posiciones",
        "📋 Historial de Órdenes", 
        "⚡ Ejecutar Orden"
    ])
    
    with tab_positions:
        st.subheader("Posiciones Abiertas")
        
        positions = executor.get_positions()
        
        if positions:
            df = pd.DataFrame(positions)
            
            # Formatear columnas
            df['market_value'] = df['market_value'].apply(lambda x: f"${x:,.2f}")
            df['avg_entry_price'] = df['avg_entry_price'].apply(lambda x: f"${x:.2f}")
            df['current_price'] = df['current_price'].apply(lambda x: f"${x:.2f}")
            df['unrealized_pl'] = df['unrealized_pl'].apply(lambda x: f"${x:+,.2f}")
            df['unrealized_plpc'] = df['unrealized_plpc'].apply(lambda x: f"{x:+.2f}%")
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Botón para cerrar todas
            if st.button("🚫 Cerrar Todas las Posiciones", type="secondary"):
                with st.spinner("Cerrando posiciones..."):
                    logs = executor.close_all_positions()
                    for log in logs:
                        if log.error:
                            st.error(f"Error cerrando {log.symbol}: {log.error}")
                        else:
                            st.success(f"✅ Cerrada posición {log.symbol}")
                    st.rerun()
        else:
            st.info("No hay posiciones abiertas")
    
    with tab_orders:
        st.subheader("Historial de Órdenes")
        
        orders = executor.get_order_history(limit=20)
        
        if orders:
            df = pd.DataFrame(orders)
            
            # Seleccionar columnas relevantes
            display_cols = ['timestamp', 'symbol', 'side', 'qty', 'order_type', 
                          'status', 'filled_price', 'slippage', 'error']
            df = df[[c for c in display_cols if c in df.columns]]
            
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No hay órdenes en el historial")
    
    with tab_execute:
        st.subheader("Ejecutar Nueva Orden")
        
        if not market['is_open']:
            st.warning("⚠️ El mercado está cerrado. Las órdenes se ejecutarán al abrirse.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.text_input("Símbolo", value="SPY").upper()
            qty = st.number_input("Cantidad", min_value=1, value=1, step=1)
            
        with col2:
            side = st.selectbox("Lado", ["buy", "sell"])
            order_type = st.selectbox("Tipo", ["market", "limit"])
            
            limit_price = None
            if order_type == "limit":
                limit_price = st.number_input("Precio Límite", min_value=0.01, step=0.01)
        
        # Quote actual
        quote = executor.get_quote(symbol)
        if "error" not in quote:
            st.info(f"📊 {symbol}: Bid ${quote['bid']:.2f} | Ask ${quote['ask']:.2f}")
        
        if st.button("🚀 Ejecutar Orden", type="primary"):
            with st.spinner("Ejecutando..."):
                log = executor.place_order(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    order_type=order_type,
                    limit_price=limit_price,
                )
                
                if log.error:
                    st.error(f"❌ Error: {log.error}")
                else:
                    st.success(f"""
                    ✅ Orden ejecutada!
                    - ID: {log.order_id}
                    - Status: {log.status}
                    - Filled Price: ${log.filled_price:.2f if log.filled_price else 'Pending'}
                    """)
                    st.rerun()


if __name__ == "__main__":
    main()

This file is a merged representation of a subset of the codebase, containing files not matching ignore patterns, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching these patterns are excluded: node_modules, __pycache__, .venv, .next, *.pyc, *.pyo, data/*.parquet, reports/*.pdf, logs/*.log, repomix-output.xml
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
app/
  pages/
    1_Live_Trading.py
  __init__.py
  streamlit_app.py
data/
  mt5_orders.db
  orders.db
frontend/
  public/
    file.svg
    globe.svg
    next.svg
    vercel.svg
    window.svg
  src/
    app/
      favicon.ico
      globals.css
      layout.tsx
      page.tsx
  .gitignore
  eslint.config.mjs
  next.config.ts
  package.json
  postcss.config.mjs
  README.md
  tailwind.config.ts
  tsconfig.json
mt5/
  FileCommander.ex5
  FileCommander.mq5
  SocketServer.mq5
scripts/
  generate_report.py
  live_bot_mt5.py
  live_bot.py
src/
  backtest/
    __init__.py
    costs.py
    engine.py
    sizing.py
  config/
    __init__.py
    experiments.py
    settings.py
  data/
    __init__.py
    cache.py
    loader.py
    schemas.py
  evaluation/
    __init__.py
    metrics.py
    monte_carlo.py
    pdf_report.py
    reports.py
  execution/
    __init__.py
    alpaca_engine.py
    mt5_executor.py
  ml/
    __init__.py
    features.py
    model.py
    optimization.py
  optimization/
    __init__.py
    wfo.py
  strategy/
    __init__.py
    base.py
    indicators.py
    ma_cross.py
  ui/
    styles.py
  __init__.py
tests/
  __init__.py
  test_backtest.py
  test_data.py
  test_ml.py
  test_strategy.py
.env.example
.gitignore
api.py
mt5linux.sh
mt5setup.exe
pyproject.toml
README.md
webview2.exe
```

# Files

## File: app/pages/1_Live_Trading.py
````python
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
````

## File: app/__init__.py
````python
# App package
````

## File: frontend/public/file.svg
````xml
<svg fill="none" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg"><path d="M14.5 13.5V5.41a1 1 0 0 0-.3-.7L9.8.29A1 1 0 0 0 9.08 0H1.5v13.5A2.5 2.5 0 0 0 4 16h8a2.5 2.5 0 0 0 2.5-2.5m-1.5 0v-7H8v-5H3v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1M9.5 5V2.12L12.38 5zM5.13 5h-.62v1.25h2.12V5zm-.62 3h7.12v1.25H4.5zm.62 3h-.62v1.25h7.12V11z" clip-rule="evenodd" fill="#666" fill-rule="evenodd"/></svg>
````

## File: frontend/public/globe.svg
````xml
<svg fill="none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><g clip-path="url(#a)"><path fill-rule="evenodd" clip-rule="evenodd" d="M10.27 14.1a6.5 6.5 0 0 0 3.67-3.45q-1.24.21-2.7.34-.31 1.83-.97 3.1M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16m.48-1.52a7 7 0 0 1-.96 0H7.5a4 4 0 0 1-.84-1.32q-.38-.89-.63-2.08a40 40 0 0 0 3.92 0q-.25 1.2-.63 2.08a4 4 0 0 1-.84 1.31zm2.94-4.76q1.66-.15 2.95-.43a7 7 0 0 0 0-2.58q-1.3-.27-2.95-.43a18 18 0 0 1 0 3.44m-1.27-3.54a17 17 0 0 1 0 3.64 39 39 0 0 1-4.3 0 17 17 0 0 1 0-3.64 39 39 0 0 1 4.3 0m1.1-1.17q1.45.13 2.69.34a6.5 6.5 0 0 0-3.67-3.44q.65 1.26.98 3.1M8.48 1.5l.01.02q.41.37.84 1.31.38.89.63 2.08a40 40 0 0 0-3.92 0q.25-1.2.63-2.08a4 4 0 0 1 .85-1.32 7 7 0 0 1 .96 0m-2.75.4a6.5 6.5 0 0 0-3.67 3.44 29 29 0 0 1 2.7-.34q.31-1.83.97-3.1M4.58 6.28q-1.66.16-2.95.43a7 7 0 0 0 0 2.58q1.3.27 2.95.43a18 18 0 0 1 0-3.44m.17 4.71q-1.45-.12-2.69-.34a6.5 6.5 0 0 0 3.67 3.44q-.65-1.27-.98-3.1" fill="#666"/></g><defs><clipPath id="a"><path fill="#fff" d="M0 0h16v16H0z"/></clipPath></defs></svg>
````

## File: frontend/public/next.svg
````xml
<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 394 80"><path fill="#000" d="M262 0h68.5v12.7h-27.2v66.6h-13.6V12.7H262V0ZM149 0v12.7H94v20.4h44.3v12.6H94v21h55v12.6H80.5V0h68.7zm34.3 0h-17.8l63.8 79.4h17.9l-32-39.7 32-39.6h-17.9l-23 28.6-23-28.6zm18.3 56.7-9-11-27.1 33.7h17.8l18.3-22.7z"/><path fill="#000" d="M81 79.3 17 0H0v79.3h13.6V17l50.2 62.3H81Zm252.6-.4c-1 0-1.8-.4-2.5-1s-1.1-1.6-1.1-2.6.3-1.8 1-2.5 1.6-1 2.6-1 1.8.3 2.5 1a3.4 3.4 0 0 1 .6 4.3 3.7 3.7 0 0 1-3 1.8zm23.2-33.5h6v23.3c0 2.1-.4 4-1.3 5.5a9.1 9.1 0 0 1-3.8 3.5c-1.6.8-3.5 1.3-5.7 1.3-2 0-3.7-.4-5.3-1s-2.8-1.8-3.7-3.2c-.9-1.3-1.4-3-1.4-5h6c.1.8.3 1.6.7 2.2s1 1.2 1.6 1.5c.7.4 1.5.5 2.4.5 1 0 1.8-.2 2.4-.6a4 4 0 0 0 1.6-1.8c.3-.8.5-1.8.5-3V45.5zm30.9 9.1a4.4 4.4 0 0 0-2-3.3 7.5 7.5 0 0 0-4.3-1.1c-1.3 0-2.4.2-3.3.5-.9.4-1.6 1-2 1.6a3.5 3.5 0 0 0-.3 4c.3.5.7.9 1.3 1.2l1.8 1 2 .5 3.2.8c1.3.3 2.5.7 3.7 1.2a13 13 0 0 1 3.2 1.8 8.1 8.1 0 0 1 3 6.5c0 2-.5 3.7-1.5 5.1a10 10 0 0 1-4.4 3.5c-1.8.8-4.1 1.2-6.8 1.2-2.6 0-4.9-.4-6.8-1.2-2-.8-3.4-2-4.5-3.5a10 10 0 0 1-1.7-5.6h6a5 5 0 0 0 3.5 4.6c1 .4 2.2.6 3.4.6 1.3 0 2.5-.2 3.5-.6 1-.4 1.8-1 2.4-1.7a4 4 0 0 0 .8-2.4c0-.9-.2-1.6-.7-2.2a11 11 0 0 0-2.1-1.4l-3.2-1-3.8-1c-2.8-.7-5-1.7-6.6-3.2a7.2 7.2 0 0 1-2.4-5.7 8 8 0 0 1 1.7-5 10 10 0 0 1 4.3-3.5c2-.8 4-1.2 6.4-1.2 2.3 0 4.4.4 6.2 1.2 1.8.8 3.2 2 4.3 3.4 1 1.4 1.5 3 1.5 5h-5.8z"/></svg>
````

## File: frontend/public/vercel.svg
````xml
<svg fill="none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1155 1000"><path d="m577.3 0 577.4 1000H0z" fill="#fff"/></svg>
````

## File: frontend/public/window.svg
````xml
<svg fill="none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path fill-rule="evenodd" clip-rule="evenodd" d="M1.5 2.5h13v10a1 1 0 0 1-1 1h-11a1 1 0 0 1-1-1zM0 1h16v11.5a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 0 12.5zm3.75 4.5a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5M7 4.75a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0m1.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5" fill="#666"/></svg>
````

## File: frontend/src/app/globals.css
````css
@import "tailwindcss";

/* Custom CSS Variables */
:root {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --card: 222.2 84% 4.9%;
  --card-foreground: 210 40% 98%;
  --primary: 217.2 91.2% 59.8%;
  --primary-foreground: 222.2 47.4% 11.2%;
  --secondary: 217.2 32.6% 17.5%;
  --secondary-foreground: 210 40% 98%;
  --muted: 217.2 32.6% 17.5%;
  --muted-foreground: 215 20.2% 65.1%;
  --destructive: 0 62.8% 50%;
  --success: 142 76% 36%;
  --border: 217.2 32.6% 17.5%;
}

/* Base Styles */
* {
  border-color: hsl(217.2, 32.6%, 17.5%);
}

body {
  background-color: hsl(222.2, 84%, 4.9%);
  color: hsl(210, 40%, 98%);
  font-family: 'Inter', system-ui, sans-serif;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: hsl(222.2, 84%, 4.9%);
}

::-webkit-scrollbar-thumb {
  background: hsl(217.2, 91.2%, 59.8%);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: hsl(224.3, 76.3%, 48%);
}

/* Glassmorphism effect */
.glass {
  background: rgba(17, 24, 39, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Glow effects */
.glow-primary {
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
}

.glow-success {
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
}

.glow-destructive {
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
}

/* Gradient text */
.gradient-text {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Card hover effect */
.card-hover {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card-hover:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.4),
    0 0 30px rgba(99, 102, 241, 0.15);
}

/* Pulse animation for live indicators */
@keyframes pulse-live {

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.5;
  }
}

.pulse-live {
  animation: pulse-live 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Color utilities */
.bg-background {
  background-color: hsl(222.2, 84%, 4.9%);
}

.text-foreground {
  color: hsl(210, 40%, 98%);
}

.text-muted-foreground {
  color: hsl(215, 20.2%, 65.1%);
}

.bg-primary {
  background-color: hsl(217.2, 91.2%, 59.8%);
}

.text-primary {
  color: hsl(217.2, 91.2%, 59.8%);
}

.text-primary-foreground {
  color: hsl(222.2, 47.4%, 11.2%);
}

.bg-secondary {
  background-color: hsl(217.2, 32.6%, 17.5%);
}

.border-border {
  border-color: hsl(217.2, 32.6%, 17.5%);
}
````

## File: frontend/src/app/layout.tsx
````typescript
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Trading Backtester Pro",
  description: "Backtesting institucional con Machine Learning avanzado",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
````

## File: frontend/src/app/page.tsx
````typescript
"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Wallet,
  Target,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  Percent,
  Play,
  Loader2,
  X,
  ChevronDown,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from "recharts";

const API_URL = "http://localhost:8000";

interface BacktestResult {
  success: boolean;
  stats: Record<string, number>;
  equity_data: Array<{ date: string; value: number }>;
  trades_count: number;
  strategy_name: string;
  error?: string;
}

interface MetricCardProps {
  title: string;
  value: string;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  icon: React.ReactNode;
  delay?: number;
}

function MetricCard({ title, value, change, changeType = "neutral", icon, delay = 0 }: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="glass rounded-2xl p-6 card-hover"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-muted-foreground uppercase tracking-wider font-medium mb-1">
            {title}
          </p>
          <p className="text-3xl font-bold font-mono text-foreground">
            {value}
          </p>
          {change && (
            <div className={`flex items-center gap-1 mt-2 text-sm font-medium ${changeType === "positive" ? "text-green-400" :
                changeType === "negative" ? "text-red-400" :
                  "text-gray-400"
              }`}>
              {changeType === "positive" ? <ArrowUpRight className="w-4 h-4" /> :
                changeType === "negative" ? <ArrowDownRight className="w-4 h-4" /> : null}
              {change}
            </div>
          )}
        </div>
        <div className="p-3 rounded-xl bg-blue-500/10 text-blue-400">
          {icon}
        </div>
      </div>
    </motion.div>
  );
}

function StrategyModal({
  isOpen,
  onClose,
  onSubmit,
  isLoading
}: {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (config: BacktestConfig) => void;
  isLoading: boolean;
}) {
  const [config, setConfig] = useState<BacktestConfig>({
    ticker: "SPY",
    timeframe: "1d",
    strategy_type: "ma_cross",
    fast_period: 10,
    slow_period: 50,
    initial_capital: 100000,
  });

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="glass rounded-2xl p-6 w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">Nueva Estrategia</h2>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Ticker */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">Ticker</label>
            <select
              value={config.ticker}
              onChange={(e) => setConfig({ ...config, ticker: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:outline-none transition-colors"
            >
              <option value="SPY">SPY - S&P 500 ETF</option>
              <option value="QQQ">QQQ - Nasdaq 100</option>
              <option value="AAPL">AAPL - Apple</option>
              <option value="MSFT">MSFT - Microsoft</option>
              <option value="TSLA">TSLA - Tesla</option>
              <option value="NVDA">NVDA - NVIDIA</option>
              <option value="BTC-USD">BTC-USD - Bitcoin</option>
            </select>
          </div>

          {/* Timeframe */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">Timeframe</label>
            <div className="grid grid-cols-3 gap-2">
              {["15m", "1h", "1d"].map((tf) => (
                <button
                  key={tf}
                  onClick={() => setConfig({ ...config, timeframe: tf })}
                  className={`py-2 px-4 rounded-xl font-medium transition-all ${config.timeframe === tf
                      ? "bg-blue-500 text-white"
                      : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                    }`}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>

          {/* Strategy Type */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">Estrategia</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setConfig({ ...config, strategy_type: "ma_cross" })}
                className={`py-3 px-4 rounded-xl font-medium transition-all ${config.strategy_type === "ma_cross"
                    ? "bg-blue-500 text-white"
                    : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                  }`}
              >
                MA Cross
              </button>
              <button
                onClick={() => setConfig({ ...config, strategy_type: "ml" })}
                className={`py-3 px-4 rounded-xl font-medium transition-all ${config.strategy_type === "ml"
                    ? "bg-purple-500 text-white"
                    : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                  }`}
              >
                Machine Learning
              </button>
            </div>
          </div>

          {/* MA Parameters */}
          {config.strategy_type === "ma_cross" && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">MA Rápida</label>
                <input
                  type="number"
                  value={config.fast_period}
                  onChange={(e) => setConfig({ ...config, fast_period: parseInt(e.target.value) })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">MA Lenta</label>
                <input
                  type="number"
                  value={config.slow_period}
                  onChange={(e) => setConfig({ ...config, slow_period: parseInt(e.target.value) })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>
          )}

          {/* Capital */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">Capital Inicial</label>
            <input
              type="number"
              value={config.initial_capital}
              onChange={(e) => setConfig({ ...config, initial_capital: parseFloat(e.target.value) })}
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Submit Button */}
          <button
            onClick={() => onSubmit(config)}
            disabled={isLoading}
            className="w-full py-4 rounded-xl font-semibold text-white bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Ejecutando Backtest...
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                Ejecutar Backtest
              </>
            )}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

interface BacktestConfig {
  ticker: string;
  timeframe: string;
  strategy_type: string;
  fast_period: number;
  slow_period: number;
  initial_capital: number;
}

export default function Dashboard() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [currentConfig, setCurrentConfig] = useState<BacktestConfig | null>(null);

  const runBacktest = async (config: BacktestConfig) => {
    setIsLoading(true);
    setCurrentConfig(config);

    try {
      const response = await fetch(`${API_URL}/api/backtest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      const data = await response.json();
      setResult(data);
      setIsModalOpen(false);
    } catch (error) {
      console.error("Error running backtest:", error);
      setResult({
        success: false,
        stats: {},
        equity_data: [],
        trades_count: 0,
        strategy_name: "",
        error: "Error de conexión. ¿Está corriendo el API? (uv run uvicorn api:app --reload)",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const stats = result?.stats || {};
  const equityData = result?.equity_data || [];

  // Calculate monthly returns from equity data
  const monthlyReturns = equityData.length > 30
    ? Array.from({ length: 12 }, (_, i) => {
      const monthData = equityData.filter((_, idx) => Math.floor(idx / (equityData.length / 12)) === i);
      if (monthData.length < 2) return { month: `M${i + 1}`, return: 0 };
      const start = monthData[0]?.value || 100000;
      const end = monthData[monthData.length - 1]?.value || start;
      return { month: `M${i + 1}`, return: ((end - start) / start) * 100 };
    })
    : [];

  return (
    <div className="min-h-screen bg-background">
      {/* Background gradient */}
      <div className="fixed inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-purple-500/5 pointer-events-none" />

      {/* Strategy Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <StrategyModal
            isOpen={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            onSubmit={runBacktest}
            isLoading={isLoading}
          />
        )}
      </AnimatePresence>

      {/* Content */}
      <div className="relative z-10">
        {/* Header */}
        <header className="border-b border-gray-800/50 backdrop-blur-lg bg-gray-900/80 sticky top-0 z-40">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-blue-500/10">
                  <Zap className="w-6 h-6 text-blue-400" />
                </div>
                <div>
                  <h1 className="text-xl font-bold gradient-text">Trading Backtester Pro</h1>
                  <p className="text-xs text-gray-500">Backtesting institucional • ML avanzado</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                {result?.success && (
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 text-green-400 text-sm font-medium">
                    <div className="w-2 h-2 rounded-full bg-green-400 pulse-live" />
                    {result.strategy_name}
                  </div>
                )}
                <button
                  onClick={() => setIsModalOpen(true)}
                  className="px-4 py-2 rounded-xl bg-blue-500 text-white font-medium hover:bg-blue-600 transition-colors flex items-center gap-2"
                >
                  <Play className="w-4 h-4" />
                  Nueva Estrategia
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="container mx-auto px-6 py-8">
          {/* Error Message */}
          {result?.error && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400"
            >
              <p className="font-medium">Error: {result.error}</p>
            </motion.div>
          )}

          {/* Current Strategy Info */}
          {currentConfig && result?.success && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mb-6 p-4 rounded-xl glass flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                <div className="p-2 rounded-lg bg-blue-500/10">
                  <BarChart3 className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Estrategia Activa</p>
                  <p className="font-semibold text-white">
                    {currentConfig.ticker} • {result.strategy_name} • {currentConfig.timeframe}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400">Capital Inicial</p>
                <p className="font-mono font-semibold text-white">
                  ${currentConfig.initial_capital.toLocaleString()}
                </p>
              </div>
            </motion.div>
          )}

          {/* Hero Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <MetricCard
              title="Equity Total"
              value={result?.success ? `$${(stats.final_equity || 100000).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : "$100,000"}
              change={result?.success ? `${(stats.total_return_pct || 0).toFixed(1)}% Total` : "—"}
              changeType={stats.total_return_pct > 0 ? "positive" : stats.total_return_pct < 0 ? "negative" : "neutral"}
              icon={<Wallet className="w-6 h-6" />}
              delay={0}
            />
            <MetricCard
              title="Sharpe Ratio"
              value={result?.success ? (stats.sharpe_ratio || 0).toFixed(2) : "—"}
              change={stats.sharpe_ratio > 1 ? "Excelente" : stats.sharpe_ratio > 0.5 ? "Bueno" : "Bajo"}
              changeType={stats.sharpe_ratio > 1 ? "positive" : stats.sharpe_ratio > 0.5 ? "neutral" : "negative"}
              icon={<Target className="w-6 h-6" />}
              delay={0.1}
            />
            <MetricCard
              title="Max Drawdown"
              value={result?.success ? `${(stats.max_drawdown_pct || 0).toFixed(1)}%` : "—"}
              change={Math.abs(stats.max_drawdown_pct || 0) < 10 ? "Controlado" : "Alto"}
              changeType={Math.abs(stats.max_drawdown_pct || 0) < 10 ? "positive" : "negative"}
              icon={<TrendingDown className="w-6 h-6" />}
              delay={0.2}
            />
            <MetricCard
              title="Win Rate"
              value={result?.success ? `${(stats.win_rate_pct || 0).toFixed(1)}%` : "—"}
              change={`${stats.total_trades || 0} trades`}
              changeType={stats.win_rate_pct > 50 ? "positive" : "neutral"}
              icon={<Percent className="w-6 h-6" />}
              delay={0.3}
            />
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Equity Chart */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="glass rounded-2xl p-6 card-hover"
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-white">Curva de Equity</h3>
                  <p className="text-sm text-gray-500">Performance acumulado</p>
                </div>
              </div>
              {equityData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={equityData}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="date" stroke="#64748b" fontSize={10} tickFormatter={(v) => v.slice(5)} />
                    <YAxis stroke="#64748b" fontSize={10} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(17, 24, 39, 0.95)",
                        border: "1px solid rgba(255,255,255,0.1)",
                        borderRadius: "12px",
                      }}
                      formatter={(value: number) => [`$${value.toLocaleString()}`, "Equity"]}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#6366f1"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#colorValue)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>Ejecuta un backtest para ver la curva de equity</p>
                  </div>
                </div>
              )}
            </motion.div>

            {/* Stats Grid */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.5 }}
              className="glass rounded-2xl p-6 card-hover"
            >
              <h3 className="text-lg font-semibold text-white mb-4">Estadísticas Detalladas</h3>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { label: "Profit Factor", value: (stats.profit_factor || 0).toFixed(2), icon: <BarChart3 className="w-4 h-4" /> },
                  { label: "Sortino Ratio", value: (stats.sortino_ratio || 0).toFixed(2), icon: <Target className="w-4 h-4" /> },
                  { label: "Calmar Ratio", value: (stats.calmar_ratio || 0).toFixed(2), icon: <Activity className="w-4 h-4" /> },
                  { label: "Avg Trade", value: `${(stats.avg_trade_pct || 0).toFixed(2)}%`, icon: <TrendingUp className="w-4 h-4" /> },
                  { label: "Best Trade", value: `${(stats.best_trade_pct || 0).toFixed(1)}%`, icon: <ArrowUpRight className="w-4 h-4" /> },
                  { label: "Worst Trade", value: `${(stats.worst_trade_pct || 0).toFixed(1)}%`, icon: <ArrowDownRight className="w-4 h-4" /> },
                ].map((stat, index) => (
                  <div key={index} className="p-4 rounded-xl bg-gray-800/50 hover:bg-gray-800 transition-colors">
                    <div className="flex items-center gap-2 text-gray-400 mb-1">
                      {stat.icon}
                      <span className="text-xs uppercase tracking-wider">{stat.label}</span>
                    </div>
                    <p className="text-xl font-bold font-mono text-white">
                      {result?.success ? stat.value : "—"}
                    </p>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>

          {/* Footer */}
          <motion.footer
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.6 }}
            className="mt-12 text-center text-gray-500 text-sm"
          >
            <p>Trading Backtester Pro • Next.js + FastAPI + Python</p>
          </motion.footer>
        </main>
      </div>
    </div>
  );
}
````

## File: frontend/.gitignore
````
# See https://help.github.com/articles/ignoring-files/ for more about ignoring files.

# dependencies
/node_modules
/.pnp
.pnp.*
.yarn/*
!.yarn/patches
!.yarn/plugins
!.yarn/releases
!.yarn/versions

# testing
/coverage

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# env files (can opt-in for committing if needed)
.env*

# vercel
.vercel

# typescript
*.tsbuildinfo
next-env.d.ts
````

## File: frontend/eslint.config.mjs
````javascript
import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
````

## File: frontend/next.config.ts
````typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
};

export default nextConfig;
````

## File: frontend/package.json
````json
{
  "name": "frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint"
  },
  "dependencies": {
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "framer-motion": "^12.26.1",
    "lucide-react": "^0.562.0",
    "next": "16.1.1",
    "react": "19.2.3",
    "react-dom": "19.2.3",
    "recharts": "^3.6.0",
    "tailwind-merge": "^3.4.0"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4",
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "eslint": "^9",
    "eslint-config-next": "16.1.1",
    "tailwindcss": "^4",
    "typescript": "^5"
  }
}
````

## File: frontend/postcss.config.mjs
````javascript
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
````

## File: frontend/README.md
````markdown
This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
````

## File: frontend/tailwind.config.ts
````typescript
import type { Config } from "tailwindcss";

const config: Config = {
    darkMode: ["class"],
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "hsl(222.2, 84%, 4.9%)",
                foreground: "hsl(210, 40%, 98%)",
                card: {
                    DEFAULT: "hsl(222.2, 84%, 4.9%)",
                    foreground: "hsl(210, 40%, 98%)",
                },
                popover: {
                    DEFAULT: "hsl(222.2, 84%, 4.9%)",
                    foreground: "hsl(210, 40%, 98%)",
                },
                primary: {
                    DEFAULT: "hsl(217.2, 91.2%, 59.8%)",
                    foreground: "hsl(222.2, 47.4%, 11.2%)",
                },
                secondary: {
                    DEFAULT: "hsl(217.2, 32.6%, 17.5%)",
                    foreground: "hsl(210, 40%, 98%)",
                },
                muted: {
                    DEFAULT: "hsl(217.2, 32.6%, 17.5%)",
                    foreground: "hsl(215, 20.2%, 65.1%)",
                },
                accent: {
                    DEFAULT: "hsl(217.2, 32.6%, 17.5%)",
                    foreground: "hsl(210, 40%, 98%)",
                },
                destructive: {
                    DEFAULT: "hsl(0, 62.8%, 50%)",
                    foreground: "hsl(210, 40%, 98%)",
                },
                success: {
                    DEFAULT: "hsl(142, 76%, 36%)",
                    foreground: "hsl(355, 100%, 97%)",
                },
                border: "hsl(217.2, 32.6%, 17.5%)",
                input: "hsl(217.2, 32.6%, 17.5%)",
                ring: "hsl(224.3, 76.3%, 48%)",
            },
            borderRadius: {
                lg: "0.75rem",
                md: "0.5rem",
                sm: "0.25rem",
            },
            fontFamily: {
                sans: ["Inter", "system-ui", "sans-serif"],
                mono: ["JetBrains Mono", "monospace"],
            },
            animation: {
                "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
                "glow": "glow 2s ease-in-out infinite alternate",
                "slide-up": "slideUp 0.5s ease-out",
                "fade-in": "fadeIn 0.5s ease-out",
            },
            keyframes: {
                glow: {
                    "0%": { boxShadow: "0 0 5px hsl(217.2, 91.2%, 59.8%), 0 0 10px hsl(217.2, 91.2%, 59.8%)" },
                    "100%": { boxShadow: "0 0 10px hsl(217.2, 91.2%, 59.8%), 0 0 20px hsl(217.2, 91.2%, 59.8%)" },
                },
                slideUp: {
                    "0%": { transform: "translateY(20px)", opacity: "0" },
                    "100%": { transform: "translateY(0)", opacity: "1" },
                },
                fadeIn: {
                    "0%": { opacity: "0" },
                    "100%": { opacity: "1" },
                },
            },
        },
    },
    plugins: [],
};

export default config;
````

## File: frontend/tsconfig.json
````json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "react-jsx",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": [
    "next-env.d.ts",
    "**/*.ts",
    "**/*.tsx",
    ".next/types/**/*.ts",
    ".next/dev/types/**/*.ts",
    "**/*.mts"
  ],
  "exclude": ["node_modules"]
}
````

## File: mt5/FileCommander.mq5
````
//+------------------------------------------------------------------+
//|                                              FileCommander.mq5   |
//|                        Lee comandos de archivo y ejecuta trades  |
//+------------------------------------------------------------------+
#property copyright "Trading Bot"
#property link      ""
#property version   "1.00"
#property strict

// Configuración
input string CommandFile = "python_commands.txt";
input string ResponseFile = "mt5_response.txt";
input bool EnableLogging = true;

//+------------------------------------------------------------------+
//| Expert initialization                                             |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("FileCommander iniciado");
   Print("Esperando comandos en: ", TerminalInfoString(TERMINAL_DATA_PATH), "\\MQL5\\Files\\", CommandFile);
   EventSetMillisecondTimer(500);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization                                           |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   Print("FileCommander detenido");
}

//+------------------------------------------------------------------+
//| Timer - revisa archivo de comandos                                |
//+------------------------------------------------------------------+
void OnTimer()
{
   // Verificar si existe archivo de comandos
   if(!FileIsExist(CommandFile))
      return;
   
   // Leer comando
   int handle = FileOpen(CommandFile, FILE_READ|FILE_TXT|FILE_ANSI);
   if(handle == INVALID_HANDLE)
      return;
   
   string command = FileReadString(handle);
   FileClose(handle);
   
   // Borrar archivo para no repetir
   FileDelete(CommandFile);
   
   if(command == "")
      return;
   
   if(EnableLogging)
      Print("Comando recibido: ", command);
   
   // Procesar y responder
   string response = ProcessCommand(command);
   WriteResponse(response);
}

//+------------------------------------------------------------------+
//| Procesar comando                                                  |
//+------------------------------------------------------------------+
string ProcessCommand(string cmd)
{
   string action = GetJsonValue(cmd, "action");
   string symbol = GetJsonValue(cmd, "symbol");
   double volume = StringToDouble(GetJsonValue(cmd, "volume"));
   
   if(symbol == "") symbol = Symbol();
   if(volume <= 0) volume = 0.01;
   
   if(action == "ping")
      return "{\"status\":\"ok\",\"message\":\"pong\"}";
   
   if(action == "account")
      return GetAccountInfo();
   
   if(action == "positions")
      return GetPositions();
   
   if(action == "buy")
      return ExecuteTrade(symbol, volume, ORDER_TYPE_BUY);
   
   if(action == "sell")
      return ExecuteTrade(symbol, volume, ORDER_TYPE_SELL);
   
   if(action == "close")
      return ClosePos(symbol);
   
   return "{\"status\":\"error\",\"message\":\"Unknown action\"}";
}

//+------------------------------------------------------------------+
//| Ejecutar trade                                                    |
//+------------------------------------------------------------------+
string ExecuteTrade(string sym, double vol, ENUM_ORDER_TYPE type)
{
   MqlTradeRequest request;
   MqlTradeResult result;
   ZeroMemory(request);
   ZeroMemory(result);
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = sym;
   request.volume = vol;
   request.type = type;
   request.deviation = 10;
   request.magic = 123456;
   request.comment = "PythonBot";
   
   if(type == ORDER_TYPE_BUY)
      request.price = SymbolInfoDouble(sym, SYMBOL_ASK);
   else
      request.price = SymbolInfoDouble(sym, SYMBOL_BID);
   
   if(OrderSend(request, result))
   {
      Print("Trade OK: ", sym, " ", EnumToString(type));
      return StringFormat("{\"status\":\"ok\",\"order_id\":%d,\"price\":%.5f}", 
                         result.order, result.price);
   }
   
   Print("Trade ERROR: ", GetLastError());
   return StringFormat("{\"status\":\"error\",\"code\":%d}", GetLastError());
}

//+------------------------------------------------------------------+
//| Cerrar posición                                                   |
//+------------------------------------------------------------------+
string ClosePos(string sym)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionSelectByTicket(ticket))
      {
         if(PositionGetString(POSITION_SYMBOL) == sym)
         {
            MqlTradeRequest request;
            MqlTradeResult result;
            ZeroMemory(request);
            ZeroMemory(result);
            
            request.action = TRADE_ACTION_DEAL;
            request.symbol = sym;
            request.volume = PositionGetDouble(POSITION_VOLUME);
            request.position = ticket;
            request.deviation = 10;
            
            if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
            {
               request.type = ORDER_TYPE_SELL;
               request.price = SymbolInfoDouble(sym, SYMBOL_BID);
            }
            else
            {
               request.type = ORDER_TYPE_BUY;
               request.price = SymbolInfoDouble(sym, SYMBOL_ASK);
            }
            
            if(OrderSend(request, result))
               return "{\"status\":\"ok\",\"message\":\"closed\"}";
         }
      }
   }
   return "{\"status\":\"error\",\"message\":\"no position\"}";
}

//+------------------------------------------------------------------+
//| Info de cuenta                                                    |
//+------------------------------------------------------------------+
string GetAccountInfo()
{
   return StringFormat(
      "{\"status\":\"ok\",\"balance\":%.2f,\"equity\":%.2f,\"margin\":%.2f}",
      AccountInfoDouble(ACCOUNT_BALANCE),
      AccountInfoDouble(ACCOUNT_EQUITY),
      AccountInfoDouble(ACCOUNT_MARGIN)
   );
}

//+------------------------------------------------------------------+
//| Posiciones                                                        |
//+------------------------------------------------------------------+
string GetPositions()
{
   string result = "{\"status\":\"ok\",\"positions\":[";
   
   for(int i = 0; i < PositionsTotal(); i++)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionSelectByTicket(ticket))
      {
         if(i > 0) result += ",";
         result += StringFormat(
            "{\"symbol\":\"%s\",\"volume\":%.2f,\"profit\":%.2f}",
            PositionGetString(POSITION_SYMBOL),
            PositionGetDouble(POSITION_VOLUME),
            PositionGetDouble(POSITION_PROFIT)
         );
      }
   }
   
   result += "]}";
   return result;
}

//+------------------------------------------------------------------+
//| Extraer valor JSON                                                |
//+------------------------------------------------------------------+
string GetJsonValue(string json, string key)
{
   string search = "\"" + key + "\":";
   int pos = StringFind(json, search);
   if(pos < 0) return "";
   
   int start = pos + StringLen(search);
   
   while(start < StringLen(json) && StringGetCharacter(json, start) == ' ')
      start++;
   
   if(StringGetCharacter(json, start) == '"')
   {
      start++;
      int end = StringFind(json, "\"", start);
      if(end < 0) return "";
      return StringSubstr(json, start, end - start);
   }
   
   int end = start;
   while(end < StringLen(json))
   {
      ushort c = StringGetCharacter(json, end);
      if(c == ',' || c == '}') break;
      end++;
   }
   
   return StringSubstr(json, start, end - start);
}

//+------------------------------------------------------------------+
//| Escribir respuesta                                                |
//+------------------------------------------------------------------+
void WriteResponse(string response)
{
   int handle = FileOpen(ResponseFile, FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(handle != INVALID_HANDLE)
   {
      FileWriteString(handle, response);
      FileClose(handle);
      if(EnableLogging)
         Print("Respuesta: ", response);
   }
}
````

## File: scripts/generate_report.py
````python
#!/usr/bin/env python
"""
Generador de Informes de Trading

Genera informes PDF semanales/mensuales desde los logs de órdenes.

Uso:
    # Informe de la última semana
    uv run python scripts/generate_report.py --period week
    
    # Informe del último mes
    uv run python scripts/generate_report.py --period month
    
    # Informe personalizado
    uv run python scripts/generate_report.py --start 2026-01-01 --end 2026-01-07
"""

import argparse
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import Image as RLImage


def load_orders(db_path: Path, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Carga órdenes desde SQLite."""
    if not db_path.exists():
        return pd.DataFrame()
    
    conn = sqlite3.connect(db_path)
    
    query = """
        SELECT * FROM order_logs 
        WHERE created_at >= ? AND created_at <= ?
        ORDER BY created_at DESC
    """
    
    try:
        df = pd.read_sql_query(query, conn, params=[
            start_date.isoformat(), 
            end_date.isoformat()
        ])
    except:
        # Intentar con tabla mt5_order_logs
        try:
            query = """
                SELECT * FROM mt5_order_logs 
                WHERE created_at >= ? AND created_at <= ?
                ORDER BY created_at DESC
            """
            df = pd.read_sql_query(query, conn, params=[
                start_date.isoformat(), 
                end_date.isoformat()
            ])
        except:
            df = pd.DataFrame()
    
    conn.close()
    return df


def calculate_metrics(orders: pd.DataFrame) -> dict:
    """Calcula métricas de performance."""
    if orders.empty:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "avg_trade": 0,
            "best_trade": 0,
            "worst_trade": 0,
        }
    
    # Filtrar solo trades completados
    completed = orders[orders["status"] == "filled"] if "status" in orders.columns else orders
    
    metrics = {
        "total_trades": len(completed),
        "total_orders": len(orders),
    }
    
    # Si tenemos información de slippage
    if "slippage_pct" in completed.columns:
        metrics["avg_slippage"] = completed["slippage_pct"].mean()
    
    # Calcular por símbolo
    if "symbol" in completed.columns:
        metrics["symbols_traded"] = completed["symbol"].nunique()
        metrics["trades_by_symbol"] = completed.groupby("symbol").size().to_dict()
    
    return metrics


def generate_pdf_report(
    orders: pd.DataFrame,
    metrics: dict,
    period_name: str,
    start_date: datetime,
    end_date: datetime,
    output_path: Path,
):
    """Genera informe PDF."""
    
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Título
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=20,
    )
    story.append(Paragraph(f"📊 Informe de Trading - {period_name}", title_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Período
    period_text = f"Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
    story.append(Paragraph(period_text, styles["Normal"]))
    story.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))
    
    # Resumen de métricas
    story.append(Paragraph("📈 Resumen de Actividad", styles["Heading2"]))
    story.append(Spacer(1, 0.1 * inch))
    
    summary_data = [
        ["Métrica", "Valor"],
        ["Total de Órdenes", str(metrics.get("total_orders", 0))],
        ["Trades Ejecutados", str(metrics.get("total_trades", 0))],
        ["Símbolos Operados", str(metrics.get("symbols_traded", 0))],
    ]
    
    if "avg_slippage" in metrics:
        summary_data.append(["Slippage Promedio", f"{metrics['avg_slippage']:.4f}%"])
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a4e69")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#dee2e6")),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Desglose por símbolo
    if "trades_by_symbol" in metrics and metrics["trades_by_symbol"]:
        story.append(Paragraph("🎯 Trades por Símbolo", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))
        
        symbol_data = [["Símbolo", "Cantidad de Trades"]]
        for symbol, count in metrics["trades_by_symbol"].items():
            symbol_data.append([symbol, str(count)])
        
        symbol_table = Table(symbol_data, colWidths=[3*inch, 2*inch])
        symbol_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a4e69")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#dee2e6")),
        ]))
        story.append(symbol_table)
        story.append(Spacer(1, 0.3 * inch))
    
    # Historial de órdenes
    if not orders.empty:
        story.append(Paragraph("📋 Historial de Órdenes", styles["Heading2"]))
        story.append(Spacer(1, 0.1 * inch))
        
        # Seleccionar columnas relevantes
        display_cols = ["timestamp", "symbol", "side", "status"]
        available_cols = [c for c in display_cols if c in orders.columns]
        
        if available_cols:
            display_df = orders[available_cols].head(20)  # Últimas 20
            
            order_data = [available_cols]
            for _, row in display_df.iterrows():
                order_data.append([str(row[col])[:20] for col in available_cols])
            
            col_width = 5.5 * inch / len(available_cols)
            order_table = Table(order_data, colWidths=[col_width] * len(available_cols))
            order_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a4e69")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
                ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#dee2e6")),
            ]))
            story.append(order_table)
    else:
        story.append(Paragraph("No hay órdenes en este período.", styles["Normal"]))
    
    story.append(Spacer(1, 0.5 * inch))
    
    # Footer
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.gray,
    )
    story.append(Paragraph("Generado automáticamente por Portafolio ML Trading System", footer_style))
    
    # Build PDF
    doc.build(story)
    print(f"✅ Informe generado: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generador de Informes de Trading")
    parser.add_argument("--period", choices=["day", "week", "month"], default="week",
                       help="Período del informe")
    parser.add_argument("--start", type=str, help="Fecha inicio (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="Fecha fin (YYYY-MM-DD)")
    parser.add_argument("--output", type=str, help="Archivo de salida")
    
    args = parser.parse_args()
    
    # Determinar fechas
    end_date = datetime.now()
    
    if args.start and args.end:
        start_date = datetime.strptime(args.start, "%Y-%m-%d")
        end_date = datetime.strptime(args.end, "%Y-%m-%d")
        period_name = f"{args.start} a {args.end}"
    elif args.period == "day":
        start_date = end_date - timedelta(days=1)
        period_name = "Diario"
    elif args.period == "week":
        start_date = end_date - timedelta(days=7)
        period_name = "Semanal"
    else:  # month
        start_date = end_date - timedelta(days=30)
        period_name = "Mensual"
    
    print(f"📊 Generando informe {period_name}...")
    print(f"   Período: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
    
    # Cargar órdenes de Alpaca y MT5
    orders_alpaca = load_orders(Path("data/orders.db"), start_date, end_date)
    orders_mt5 = load_orders(Path("data/mt5_orders.db"), start_date, end_date)
    
    # Combinar
    all_orders = pd.concat([orders_alpaca, orders_mt5], ignore_index=True)
    
    print(f"   Órdenes encontradas: {len(all_orders)}")
    
    # Calcular métricas
    metrics = calculate_metrics(all_orders)
    
    # Generar output path
    if args.output:
        output_path = Path(args.output)
    else:
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = reports_dir / f"trading_report_{args.period}_{timestamp}.pdf"
    
    # Generar PDF
    generate_pdf_report(
        orders=all_orders,
        metrics=metrics,
        period_name=period_name,
        start_date=start_date,
        end_date=end_date,
        output_path=output_path,
    )


if __name__ == "__main__":
    main()
````

## File: scripts/live_bot_mt5.py
````python
#!/usr/bin/env python
"""
Bot de Trading Automatizado - MT5 (Forex/CFD)

Ejecuta estrategia ML en MT5 vía FileCommander.
Diseñado para correr mientras estás en la universidad.

Uso:
    uv run python scripts/live_bot_mt5.py --symbol EURUSD --interval 60

Background:
    nohup uv run python scripts/live_bot_mt5.py --symbol EURUSD &

Ver logs:
    tail -f logs/bot_mt5.log
"""

import argparse
import time
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "bot_mt5.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_forex_data(symbol: str, timeframe: str = "1h"):
    """
    Obtiene datos de Forex desde yfinance (formato MT5).
    
    Nota: yfinance tiene datos limitados para forex.
    Mapea símbolos MT5 a yfinance.
    """
    import yfinance as yf
    import pandas as pd
    
    # Mapear símbolos MT5 a yfinance
    symbol_map = {
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "USDJPY=X",
        "USDCHF": "USDCHF=X",
        "AUDUSD": "AUDUSD=X",
        "USDCAD": "USDCAD=X",
        "NZDUSD": "NZDUSD=X",
        "XAUUSD": "GC=F",  # Gold futures
        "US500": "^GSPC",  # S&P 500
        "US30": "^DJI",    # Dow Jones
    }
    
    yf_symbol = symbol_map.get(symbol, f"{symbol}=X")
    
    try:
        ticker = yf.Ticker(yf_symbol)
        
        # Para forex, usar período de 60 días
        if timeframe == "1h":
            df = ticker.history(period="60d", interval="1h")
        elif timeframe == "15m":
            df = ticker.history(period="60d", interval="15m")
        else:
            df = ticker.history(period="2y", interval="1d")
        
        if df.empty:
            return None
        
        df.columns = df.columns.str.lower()
        return df[["open", "high", "low", "close", "volume"]]
        
    except Exception as e:
        logger.error(f"Error obteniendo datos: {e}")
        return None


def run_bot(symbol: str, strategy_type: str, interval_minutes: int, volume: float):
    """Loop principal del bot MT5."""
    from src.execution import MT5Executor
    from src.strategy import MACrossStrategy
    from src.ml import FeatureEngineer, MLModel
    from src.ml.model import MLStrategy
    import warnings
    warnings.filterwarnings("ignore")
    
    # Inicializar
    executor = MT5Executor()
    
    # Verificar conexión
    if not executor.ping():
        logger.error("❌ No se puede conectar a MT5. ¿FileCommander está corriendo?")
        return
    
    logger.info(f"🚀 Bot MT5 iniciado: {symbol} | {strategy_type} | cada {interval_minutes}min")
    
    # Mostrar estado de cuenta
    account = executor.get_account()
    if "error" in account:
        logger.error(f"❌ Error obteniendo cuenta: {account}")
        return
    
    logger.info(f"💰 Balance: ${account['balance']:,.2f} | Equity: ${account['equity']:,.2f}")
    
    # Configurar estrategia
    if strategy_type == "ma_cross":
        strategy = MACrossStrategy(fast_period=10, slow_period=50)
    elif strategy_type == "ml":
        # Cargar datos iniciales para entrenar ML
        logger.info("📊 Cargando datos para entrenar modelo ML...")
        prices = get_forex_data(symbol, "1h")
        
        if prices is None or len(prices) < 200:
            logger.error("❌ No hay suficientes datos para entrenar ML. Usando MA Cross.")
            strategy = MACrossStrategy(fast_period=10, slow_period=50)
        else:
            # Entrenar modelo
            fe = FeatureEngineer()
            features, target = fe.prepare_dataset(prices, horizon=1, dropna=True)
            
            if len(features) < 100:
                logger.error("❌ Datos insuficientes post-limpieza. Usando MA Cross.")
                strategy = MACrossStrategy(fast_period=10, slow_period=50)
            else:
                train_size = int(len(features) * 0.8)
                X_train = features.iloc[:train_size]
                y_train = target.iloc[:train_size]
                
                model = MLModel(model_type="random_forest")
                metrics = model.train(X_train, y_train)
                logger.info(f"✅ Modelo entrenado: Accuracy={metrics.accuracy:.2%}")
                
                strategy = MLStrategy(
                    model=model,
                    feature_engineer=fe,
                    entry_threshold=0.65  # Más conservador para trading real
                )
    else:
        strategy = MACrossStrategy(fast_period=10, slow_period=50)
    
    logger.info(f"📈 Estrategia: {strategy.name}")
    
    last_signal = None
    
    while True:
        try:
            # Obtener datos actualizados
            prices = get_forex_data(symbol, "1h")
            
            if prices is None or len(prices) < 50:
                logger.warning(f"Sin datos suficientes para {symbol}")
                time.sleep(60)
                continue
            
            # Generar señales
            signal_result = strategy.generate_signals(prices)
            
            # Obtener última señal (evitar lookahead: usar la penúltima vela cerrada)
            latest_entry = signal_result.signals["entries"].iloc[-2]  # -2 para vela cerrada
            latest_exit = signal_result.signals["exits"].iloc[-2]
            
            # Obtener posiciones actuales
            positions = executor.get_positions()
            has_position = any(p.get("symbol", "").startswith(symbol[:3]) for p in positions)
            
            # Lógica de ejecución
            if latest_entry and not has_position and last_signal != "entry":
                logger.info(f"🟢 SEÑAL DE COMPRA: {symbol} Vol: {volume}")
                order = executor.buy(symbol, volume=volume)
                
                if order.status == "ok":
                    logger.info(f"   ✅ Orden ejecutada: ID={order.order_id} Price={order.price}")
                    last_signal = "entry"
                else:
                    logger.error(f"   ❌ Error: {order.error}")
            
            elif latest_exit and has_position and last_signal != "exit":
                logger.info(f"🔴 SEÑAL DE VENTA: {symbol}")
                order = executor.close_position(symbol)
                
                if order.status == "ok":
                    logger.info(f"   ✅ Posición cerrada")
                    last_signal = "exit"
                else:
                    logger.error(f"   ❌ Error: {order.error}")
            
            else:
                logger.info(f"⏳ Sin señal | Entry: {latest_entry} | Exit: {latest_exit} | Pos: {has_position}")
            
            # Mostrar estado de cuenta periódicamente
            account = executor.get_account()
            logger.info(f"   💵 Equity: ${account.get('equity', 0):,.2f}")
            
            # Esperar próxima iteración
            time.sleep(interval_minutes * 60)
            
        except KeyboardInterrupt:
            logger.info("🛑 Bot detenido por usuario")
            break
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description="Bot MT5 Automatizado")
    parser.add_argument("--symbol", default="EURUSD", help="Par de divisas")
    parser.add_argument("--strategy", default="ma_cross", choices=["ma_cross", "ml"], 
                        help="Estrategia a usar")
    parser.add_argument("--interval", type=int, default=60, help="Intervalo en minutos")
    parser.add_argument("--volume", type=float, default=0.01, help="Volumen en lotes")
    
    args = parser.parse_args()
    
    print("""
╔═══════════════════════════════════════════════════╗
║           MT5 TRADING BOT                         ║
║   Asegúrate de que FileCommander esté corriendo  ║
║   en MetaTrader 5 antes de iniciar               ║
╚═══════════════════════════════════════════════════╝
    """)
    
    run_bot(
        symbol=args.symbol,
        strategy_type=args.strategy,
        interval_minutes=args.interval,
        volume=args.volume,
    )


if __name__ == "__main__":
    main()
````

## File: src/backtest/__init__.py
````python
# Backtest layer
from .engine import BacktestEngine, BacktestResult
from .costs import TradingCosts
from .sizing import calculate_position_size

__all__ = ["BacktestEngine", "BacktestResult", "TradingCosts", "calculate_position_size"]
````

## File: src/backtest/costs.py
````python
"""Modelo de costos de trading."""

from dataclasses import dataclass


@dataclass
class TradingCosts:
    """
    Costos de trading configurables.
    
    Attributes:
        commission_pct: Comisión como porcentaje del valor del trade (e.g., 0.001 = 0.1%).
        slippage_pct: Slippage estimado como porcentaje (e.g., 0.0005 = 0.05%).
    """

    commission_pct: float = 0.001  # 0.1% por trade
    slippage_pct: float = 0.0005  # 0.05% slippage

    def __post_init__(self):
        if self.commission_pct < 0:
            raise ValueError("commission_pct must be >= 0")
        if self.slippage_pct < 0:
            raise ValueError("slippage_pct must be >= 0")

    @property
    def total_cost_pct(self) -> float:
        """Costo total por trade (entry + exit)."""
        # Multiplicamos por 2 porque se aplica en entry y exit
        return (self.commission_pct + self.slippage_pct) * 2

    def apply_to_price(self, price: float, is_buy: bool) -> float:
        """
        Aplica costos a un precio.
        
        Args:
            price: Precio original.
            is_buy: True para compra, False para venta.
            
        Returns:
            Precio ajustado por costos.
        """
        total = self.commission_pct + self.slippage_pct
        if is_buy:
            # Compramos más caro
            return price * (1 + total)
        else:
            # Vendemos más barato
            return price * (1 - total)
````

## File: src/backtest/sizing.py
````python
"""Position sizing basado en riesgo."""


def calculate_position_size(
    capital: float,
    risk_pct: float,
    entry_price: float,
    stop_loss_price: float,
) -> float:
    """
    Calcula el tamaño de posición arriesgando un porcentaje del capital.
    
    La idea es: si el stop se ejecuta, pierdes exactamente risk_pct de tu capital.
    
    Args:
        capital: Capital disponible.
        risk_pct: Porcentaje a arriesgar (e.g., 0.01 = 1%).
        entry_price: Precio de entrada.
        stop_loss_price: Precio del stop loss.
        
    Returns:
        Número de unidades/acciones a comprar.
        
    Example:
        >>> calculate_position_size(10000, 0.01, 100, 95)
        20.0  # 20 acciones, si baja de 100 a 95 pierdes $100 (1% de $10k)
    """
    if capital <= 0:
        raise ValueError("capital must be > 0")
    if risk_pct <= 0 or risk_pct > 1:
        raise ValueError("risk_pct must be between 0 and 1")
    if entry_price <= 0:
        raise ValueError("entry_price must be > 0")
    if stop_loss_price <= 0:
        raise ValueError("stop_loss_price must be > 0")
    if stop_loss_price >= entry_price:
        raise ValueError("stop_loss_price must be < entry_price for long positions")

    risk_per_share = entry_price - stop_loss_price
    amount_to_risk = capital * risk_pct
    position_size = amount_to_risk / risk_per_share

    return position_size


def calculate_fixed_fraction_size(
    capital: float,
    fraction: float,
    price: float,
) -> float:
    """
    Calcula tamaño de posición usando fracción fija del capital.
    
    Args:
        capital: Capital disponible.
        fraction: Fracción del capital a usar (e.g., 0.1 = 10%).
        price: Precio por unidad.
        
    Returns:
        Número de unidades a comprar.
    """
    if capital <= 0:
        raise ValueError("capital must be > 0")
    if fraction <= 0 or fraction > 1:
        raise ValueError("fraction must be between 0 and 1")
    if price <= 0:
        raise ValueError("price must be > 0")

    investment = capital * fraction
    return investment / price
````

## File: src/config/__init__.py
````python
# Config layer
from .settings import Settings
from .experiments import ExperimentRun

__all__ = ["Settings", "ExperimentRun"]
````

## File: src/config/experiments.py
````python
"""Sistema de guardado de experimentos para reproducibilidad."""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ExperimentRun:
    """
    Representa una corrida de backtest guardada.
    
    Permite reproducibilidad: "este resultado lo saqué con X parámetros".
    """

    # Identificación
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = field(default_factory=datetime.now)

    # Configuración del experimento
    ticker: str = ""
    timeframe: str = ""
    strategy_name: str = ""
    strategy_params: dict = field(default_factory=dict)

    # Rango de datos
    start_date: str = ""
    end_date: str = ""

    # Costos
    commission_pct: float = 0.001
    slippage_pct: float = 0.0005
    initial_capital: float = 10_000.0

    # Resultados
    results: dict = field(default_factory=dict)

    # Metadata
    notes: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convierte a diccionario serializable."""
        data = asdict(self)
        # Convertir datetime a string
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentRun":
        """Crea instancia desde diccionario."""
        # Convertir string a datetime
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

    def save(self, directory: Path | str) -> Path:
        """
        Guarda experimento como JSON.
        
        Args:
            directory: Directorio donde guardar.
            
        Returns:
            Path al archivo guardado.
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        filename = f"{self.timestamp.strftime('%Y%m%d_%H%M%S')}_{self.id}.json"
        filepath = directory / filename

        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

        return filepath

    @classmethod
    def load(cls, filepath: Path | str) -> "ExperimentRun":
        """
        Carga experimento desde JSON.
        
        Args:
            filepath: Path al archivo JSON.
            
        Returns:
            Instancia de ExperimentRun.
        """
        with open(filepath) as f:
            data = json.load(f)
        return cls.from_dict(data)


class ExperimentTracker:
    """Gestiona múltiples experimentos."""

    def __init__(self, experiments_dir: Path | str):
        self.experiments_dir = Path(experiments_dir)
        self.experiments_dir.mkdir(parents=True, exist_ok=True)

    def save(self, run: ExperimentRun) -> Path:
        """Guarda un experimento."""
        return run.save(self.experiments_dir)

    def list_experiments(self) -> list[ExperimentRun]:
        """Lista todos los experimentos guardados."""
        experiments = []
        for filepath in sorted(self.experiments_dir.glob("*.json"), reverse=True):
            try:
                experiments.append(ExperimentRun.load(filepath))
            except Exception:
                continue
        return experiments

    def get_by_id(self, experiment_id: str) -> ExperimentRun | None:
        """Busca experimento por ID."""
        for filepath in self.experiments_dir.glob(f"*_{experiment_id}.json"):
            return ExperimentRun.load(filepath)
        return None
````

## File: src/config/settings.py
````python
"""Configuración del proyecto con Pydantic Settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración centralizada del proyecto.
    
    Los valores pueden sobreescribirse con variables de entorno
    o un archivo .env en la raíz del proyecto.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Data
    data_cache_dir: Path = Path("data/raw")
    cache_max_age_hours: int = 24

    # Backtest defaults
    initial_capital: float = 10_000.0
    default_risk_pct: float = 0.01

    # Costs
    commission_pct: float = 0.001
    slippage_pct: float = 0.0005

    # Experiments
    experiments_dir: Path = Path("data/experiments")

    def ensure_directories(self) -> None:
        """Crea directorios necesarios si no existen."""
        self.data_cache_dir.mkdir(parents=True, exist_ok=True)
        self.experiments_dir.mkdir(parents=True, exist_ok=True)


# Singleton para uso global
_settings: Settings | None = None


def get_settings() -> Settings:
    """Retorna instancia singleton de Settings."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
````

## File: src/data/__init__.py
````python
# Data layer
from .loader import DataLoader
from .cache import CacheManager
from .schemas import PriceData, OHLCVBar, DataMetadata

__all__ = ["DataLoader", "CacheManager", "PriceData", "OHLCVBar", "DataMetadata"]
````

## File: src/data/cache.py
````python
"""Sistema de caché para datos de precios usando Parquet."""

from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd


class CacheManager:
    """Gestiona el caché de datos de precios en formato Parquet."""

    def __init__(self, cache_dir: Path | str, max_age_hours: int = 24):
        """
        Args:
            cache_dir: Directorio donde se guardan los archivos parquet.
            max_age_hours: Edad máxima del caché en horas antes de considerarlo stale.
        """
        self.cache_dir = Path(cache_dir)
        self.max_age_hours = max_age_hours
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Crea el directorio de caché si no existe."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_path(self, ticker: str, timeframe: str) -> Path:
        """
        Genera el path del archivo de caché para un ticker/timeframe.

        Args:
            ticker: Símbolo del activo (e.g., 'SPY', 'AAPL').
            timeframe: Intervalo temporal (e.g., '1d', '1h', '15m').

        Returns:
            Path al archivo parquet.
        """
        # Normaliza ticker a mayúsculas
        ticker = ticker.upper().replace("/", "_").replace(".", "_")
        filename = f"{ticker}_{timeframe}.parquet"
        return self.cache_dir / filename

    def is_cache_valid(self, path: Path) -> bool:
        """
        Verifica si el archivo de caché existe y no está expirado.

        Args:
            path: Path al archivo de caché.

        Returns:
            True si el caché es válido, False si no existe o está expirado.
        """
        if not path.exists():
            return False

        # Verificar edad del archivo
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        age = datetime.now() - mtime
        return age < timedelta(hours=self.max_age_hours)

    def save_to_cache(self, df: pd.DataFrame, path: Path) -> None:
        """
        Guarda un DataFrame en caché como Parquet.

        Args:
            df: DataFrame con datos OHLCV.
            path: Path donde guardar el archivo.
        """
        # Asegurar que el directorio existe
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, engine="pyarrow")

    def load_from_cache(self, path: Path) -> pd.DataFrame:
        """
        Carga un DataFrame desde caché.

        Args:
            path: Path al archivo parquet.

        Returns:
            DataFrame con datos OHLCV.

        Raises:
            FileNotFoundError: Si el archivo no existe.
        """
        if not path.exists():
            raise FileNotFoundError(f"Cache file not found: {path}")
        return pd.read_parquet(path, engine="pyarrow")

    def clear_cache(self, ticker: str | None = None, timeframe: str | None = None) -> int:
        """
        Limpia archivos de caché.

        Args:
            ticker: Si se especifica, solo limpia archivos de ese ticker.
            timeframe: Si se especifica, solo limpia archivos de ese timeframe.

        Returns:
            Número de archivos eliminados.
        """
        count = 0
        for file in self.cache_dir.glob("*.parquet"):
            name = file.stem
            parts = name.rsplit("_", 1)
            if len(parts) != 2:
                continue

            file_ticker, file_tf = parts
            if ticker and file_ticker.upper() != ticker.upper():
                continue
            if timeframe and file_tf != timeframe:
                continue

            file.unlink()
            count += 1

        return count
````

## File: src/data/schemas.py
````python
"""Pydantic schemas para validación de datos de precios."""

from datetime import datetime
from pydantic import BaseModel, Field


class OHLCVBar(BaseModel):
    """Representa una vela OHLCV."""

    timestamp: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: int = Field(ge=0)

    def model_post_init(self, __context) -> None:
        """Valida que high >= low y high >= open/close."""
        if self.high < self.low:
            raise ValueError(f"high ({self.high}) must be >= low ({self.low})")
        if self.high < max(self.open, self.close):
            raise ValueError("high must be >= open and close")
        if self.low > min(self.open, self.close):
            raise ValueError("low must be <= open and close")


class DataMetadata(BaseModel):
    """Metadata de un dataset de precios."""

    ticker: str
    timeframe: str
    source: str = "yfinance"
    timezone: str = "America/New_York"
    start_date: datetime
    end_date: datetime
    bar_count: int = Field(ge=0)
    last_updated: datetime = Field(default_factory=datetime.now)


class PriceData(BaseModel):
    """Container para datos de precios con metadata."""

    metadata: DataMetadata
    bars: list[OHLCVBar] = Field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.bars) == 0
````

## File: src/evaluation/monte_carlo.py
````python
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
````

## File: src/evaluation/pdf_report.py
````python
"""Generador de PDF Alpha Report - Factsheet profesional tipo Goldman Sachs.

Genera un PDF con métricas, gráficos y análisis de la estrategia.

Ejemplo de uso:
    generator = AlphaReportGenerator()
    pdf_bytes = generator.generate(backtest_result, metadata)
    with open("report.pdf", "wb") as f:
        f.write(pdf_bytes)
"""

import io
from datetime import datetime
from typing import Dict, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    Image, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from ..backtest.engine import BacktestResult
from ..data.schemas import DataMetadata


class AlphaReportGenerator:
    """
    Genera PDF profesional tipo Factsheet/Alpha Report.
    
    Incluye:
    - Header con nombre de estrategia y período
    - Métricas clave: Sharpe, Sortino, Max DD, Win Rate
    - Tabla de estadísticas completa
    - Resumen de trades
    - Footer con timestamp
    """
    
    def __init__(
        self,
        title: str = "Alpha Strategy Report",
        subtitle: str = "Quantitative Trading Analysis",
    ):
        """
        Args:
            title: Título del reporte.
            subtitle: Subtítulo descriptivo.
        """
        self.title = title
        self.subtitle = subtitle
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura estilos personalizados."""
        # Título principal
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a2e'),
            spaceAfter=6,
            alignment=TA_CENTER,
        ))
        
        # Subtítulo
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER,
        ))
        
        # Sección header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#16213e'),
            spaceBefore=15,
            spaceAfter=10,
            borderPadding=5,
        ))
        
        # Métrica grande
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            parent=self.styles['Normal'],
            fontSize=20,
            textColor=colors.HexColor('#0f4c75'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        ))
        
        # Métrica label
        self.styles.add(ParagraphStyle(
            name='MetricLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#888888'),
            alignment=TA_CENTER,
        ))
    
    def generate(
        self,
        result: BacktestResult,
        metadata: Optional[DataMetadata] = None,
        strategy_name: str = "Strategy",
        strategy_params: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        Genera PDF como bytes.
        
        Args:
            result: Resultado del backtest.
            metadata: Metadata del dataset.
            strategy_name: Nombre de la estrategia.
            strategy_params: Parámetros de la estrategia.
            
        Returns:
            PDF como bytes (listo para guardar o descargar).
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )
        
        story = []
        
        # Header
        story.extend(self._build_header(strategy_name, metadata))
        
        # Línea separadora
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0e0e0')))
        story.append(Spacer(1, 20))
        
        # Métricas principales
        story.extend(self._build_key_metrics(result))
        story.append(Spacer(1, 20))
        
        # Tabla de estadísticas
        story.extend(self._build_stats_table(result))
        story.append(Spacer(1, 20))
        
        # Resumen de trades
        story.extend(self._build_trades_summary(result))
        story.append(Spacer(1, 30))
        
        # Parámetros de estrategia
        if strategy_params:
            story.extend(self._build_params_section(strategy_params))
        
        # Footer
        story.extend(self._build_footer())
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _build_header(self, strategy_name: str, metadata: Optional[DataMetadata]) -> list:
        """Construye el header del reporte."""
        elements = []
        
        elements.append(Paragraph(self.title, self.styles['MainTitle']))
        elements.append(Paragraph(self.subtitle, self.styles['Subtitle']))
        
        # Info de la estrategia
        if metadata:
            info_text = f"<b>{strategy_name}</b> | {metadata.ticker} | {metadata.timeframe}"
            info_text += f" | {metadata.start_date.strftime('%Y-%m-%d')} to {metadata.end_date.strftime('%Y-%m-%d')}"
        else:
            info_text = f"<b>{strategy_name}</b>"
        
        elements.append(Paragraph(info_text, self.styles['Normal']))
        elements.append(Spacer(1, 10))
        
        return elements
    
    def _build_key_metrics(self, result: BacktestResult) -> list:
        """Construye sección de métricas clave."""
        elements = []
        
        elements.append(Paragraph("Key Performance Metrics", self.styles['SectionHeader']))
        
        stats = result.stats
        
        # Crear tabla de métricas 2x4
        metrics = [
            ("Total Return", f"{stats.get('total_return_pct', 0):.2f}%"),
            ("Sharpe Ratio", f"{stats.get('sharpe_ratio', 0):.2f}"),
            ("Max Drawdown", f"{stats.get('max_drawdown_pct', 0):.2f}%"),
            ("Win Rate", f"{stats.get('win_rate_pct', 0):.1f}%"),
            ("Profit Factor", f"{stats.get('profit_factor', 0):.2f}"),
            ("Avg Trade", f"{stats.get('avg_trade_pct', 0):.2f}%"),
            ("Total Trades", f"{int(stats.get('num_trades', 0))}"),
            ("Sortino Ratio", f"{stats.get('sortino_ratio', 0):.2f}"),
        ]
        
        # 2 filas x 4 columnas
        table_data = []
        for i in range(0, len(metrics), 4):
            row_labels = []
            row_values = []
            for j in range(4):
                if i + j < len(metrics):
                    label, value = metrics[i + j]
                    row_labels.append(label)
                    row_values.append(value)
                else:
                    row_labels.append("")
                    row_values.append("")
            table_data.append(row_values)
            table_data.append(row_labels)
        
        table = Table(table_data, colWidths=[3.5*cm]*4)
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 16),
            ('FONTSIZE', (0, 2), (-1, 2), 16),
            ('FONTSIZE', (0, 1), (-1, 1), 9),
            ('FONTSIZE', (0, 3), (-1, 3), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0f4c75')),
            ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#0f4c75')),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#888888')),
            ('TEXTCOLOR', (0, 3), (-1, 3), colors.HexColor('#888888')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _build_stats_table(self, result: BacktestResult) -> list:
        """Construye tabla de estadísticas detalladas."""
        elements = []
        
        elements.append(Paragraph("Detailed Statistics", self.styles['SectionHeader']))
        
        stats = result.stats
        
        # 2 columnas de stats
        left_stats = [
            ("Initial Capital", f"${stats.get('initial_capital', 10000):,.2f}"),
            ("Final Equity", f"${stats.get('final_equity', 10000):,.2f}"),
            ("Total Return", f"{stats.get('total_return_pct', 0):.2f}%"),
            ("Annual Return", f"{stats.get('annual_return_pct', 0):.2f}%"),
            ("Max Drawdown", f"{stats.get('max_drawdown_pct', 0):.2f}%"),
        ]
        
        right_stats = [
            ("Sharpe Ratio", f"{stats.get('sharpe_ratio', 0):.3f}"),
            ("Sortino Ratio", f"{stats.get('sortino_ratio', 0):.3f}"),
            ("Calmar Ratio", f"{stats.get('calmar_ratio', 0):.3f}"),
            ("Win Rate", f"{stats.get('win_rate_pct', 0):.1f}%"),
            ("Profit Factor", f"{stats.get('profit_factor', 0):.2f}"),
        ]
        
        # Combinar en tabla
        table_data = [["Metric", "Value", "Metric", "Value"]]
        for i in range(max(len(left_stats), len(right_stats))):
            row = []
            if i < len(left_stats):
                row.extend(left_stats[i])
            else:
                row.extend(["", ""])
            if i < len(right_stats):
                row.extend(right_stats[i])
            else:
                row.extend(["", ""])
            table_data.append(row)
        
        table = Table(table_data, colWidths=[4*cm, 3*cm, 4*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _build_trades_summary(self, result: BacktestResult) -> list:
        """Construye resumen de trades."""
        elements = []
        
        elements.append(Paragraph("Trades Summary", self.styles['SectionHeader']))
        
        trades = result.trades
        
        if trades.empty:
            elements.append(Paragraph("No trades executed.", self.styles['Normal']))
            return elements
        
        # Stats básicos de trades
        total_trades = len(trades)
        if 'pnl' in trades.columns:
            winning = len(trades[trades['pnl'] > 0])
            losing = len(trades[trades['pnl'] < 0])
            avg_win = trades[trades['pnl'] > 0]['pnl'].mean() if winning > 0 else 0
            avg_loss = trades[trades['pnl'] < 0]['pnl'].mean() if losing > 0 else 0
        else:
            winning = losing = 0
            avg_win = avg_loss = 0
        
        summary_data = [
            ["Total Trades", str(total_trades)],
            ["Winning Trades", f"{winning} ({winning/total_trades*100:.0f}%)" if total_trades > 0 else "0"],
            ["Losing Trades", f"{losing} ({losing/total_trades*100:.0f}%)" if total_trades > 0 else "0"],
            ["Average Win", f"${avg_win:,.2f}"],
            ["Average Loss", f"${avg_loss:,.2f}"],
        ]
        
        table = Table(summary_data, colWidths=[6*cm, 4*cm])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#e0e0e0')),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _build_params_section(self, params: Dict[str, Any]) -> list:
        """Construye sección de parámetros."""
        elements = []
        
        elements.append(Paragraph("Strategy Parameters", self.styles['SectionHeader']))
        
        table_data = [[k, str(v)] for k, v in params.items()]
        table = Table(table_data, colWidths=[5*cm, 5*cm])
        table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _build_footer(self) -> list:
        """Construye footer."""
        elements = []
        
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0e0e0')))
        elements.append(Spacer(1, 10))
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        footer_text = f"<i>Generated on {timestamp} | Trading Backtester Pro</i>"
        
        elements.append(Paragraph(footer_text, ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#888888'),
            alignment=TA_CENTER,
        )))
        
        return elements
````

## File: src/execution/alpaca_engine.py
````python
"""Alpaca Paper Trading Engine - Ejecución de órdenes en tiempo real.

Motor de ejecución que conecta con Alpaca Paper Trading API para ejecutar
señales generadas por las estrategias.

Ejemplo de uso:
    from src.execution import AlpacaExecutor
    
    executor = AlpacaExecutor()
    
    # Ver cuenta
    account = executor.get_account()
    print(f"Equity: ${account.equity}")
    
    # Ejecutar orden
    order = executor.place_order("SPY", qty=1, side="buy")
    
    # Ver posiciones
    positions = executor.get_positions()
"""

import os
import sqlite3
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path

from dotenv import load_dotenv
import alpaca_trade_api as tradeapi


# Cargar variables de entorno
load_dotenv()


@dataclass
class OrderLog:
    """Log de una orden ejecutada."""
    timestamp: str
    symbol: str
    side: str
    qty: float
    order_type: str
    status: str
    filled_price: Optional[float]
    expected_price: Optional[float]
    slippage: Optional[float]
    order_id: str
    error: Optional[str] = None


class AlpacaExecutor:
    """
    Ejecutor de órdenes usando Alpaca Paper Trading API.
    
    Features:
    - Conexión automática con variables de entorno
    - Ejecución de órdenes market/limit
    - Logging de órdenes en SQLite
    - Tracking de slippage real
    - Manejo de errores robusto
    """
    
    PAPER_URL = "https://paper-api.alpaca.markets"
    LIVE_URL = "https://api.alpaca.markets"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        paper: bool = True,
        db_path: str = "data/orders.db",
    ):
        """
        Args:
            api_key: Alpaca API key (o desde env ALPACA_API_KEY).
            secret_key: Alpaca secret key (o desde env ALPACA_SECRET_KEY).
            paper: Si usar paper trading (True) o live (False).
            db_path: Path para SQLite de logging.
        """
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.secret_key = secret_key or os.getenv("ALPACA_SECRET_KEY")
        self.paper = paper if os.getenv("ALPACA_PAPER", "true").lower() == "true" else False
        
        if not self.api_key or not self.secret_key:
            raise ValueError(
                "Alpaca API keys no encontradas. "
                "Configura ALPACA_API_KEY y ALPACA_SECRET_KEY en .env"
            )
        
        base_url = self.PAPER_URL if self.paper else self.LIVE_URL
        
        self.api = tradeapi.REST(
            key_id=self.api_key,
            secret_key=self.secret_key,
            base_url=base_url,
            api_version='v2'
        )
        
        # Setup database para logging
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Inicializa la base de datos SQLite para logging."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                side TEXT,
                qty REAL,
                order_type TEXT,
                status TEXT,
                filled_price REAL,
                expected_price REAL,
                slippage REAL,
                order_id TEXT,
                error TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _log_order(self, order_log: OrderLog):
        """Guarda log de orden en SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO order_logs 
            (timestamp, symbol, side, qty, order_type, status, 
             filled_price, expected_price, slippage, order_id, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_log.timestamp,
            order_log.symbol,
            order_log.side,
            order_log.qty,
            order_log.order_type,
            order_log.status,
            order_log.filled_price,
            order_log.expected_price,
            order_log.slippage,
            order_log.order_id,
            order_log.error,
        ))
        
        conn.commit()
        conn.close()
    
    def get_account(self) -> Dict[str, Any]:
        """
        Obtiene información de la cuenta.
        
        Returns:
            Dict con equity, cash, buying_power, etc.
        """
        account = self.api.get_account()
        return {
            "equity": float(account.equity),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "portfolio_value": float(account.portfolio_value),
            "currency": account.currency,
            "status": account.status,
            "trading_blocked": account.trading_blocked,
            "pattern_day_trader": account.pattern_day_trader,
        }
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Obtiene posiciones abiertas.
        
        Returns:
            Lista de posiciones con symbol, qty, market_value, etc.
        """
        positions = self.api.list_positions()
        return [
            {
                "symbol": p.symbol,
                "qty": float(p.qty),
                "side": p.side,
                "market_value": float(p.market_value),
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": float(p.unrealized_plpc) * 100,
            }
            for p in positions
        ]
    
    def get_quote(self, symbol: str) -> Dict[str, float]:
        """
        Obtiene cotización actual.
        
        Args:
            symbol: Ticker del activo.
            
        Returns:
            Dict con bid, ask, last price.
        """
        try:
            quote = self.api.get_latest_quote(symbol)
            return {
                "bid": float(quote.bid_price),
                "ask": float(quote.ask_price),
                "mid": (float(quote.bid_price) + float(quote.ask_price)) / 2,
            }
        except Exception as e:
            return {"error": str(e)}
    
    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str = "buy",
        order_type: str = "market",
        limit_price: Optional[float] = None,
        expected_price: Optional[float] = None,
    ) -> OrderLog:
        """
        Ejecuta una orden.
        
        Args:
            symbol: Ticker del activo.
            qty: Cantidad (acciones).
            side: "buy" o "sell".
            order_type: "market" o "limit".
            limit_price: Precio límite (solo para órdenes limit).
            expected_price: Precio esperado para calcular slippage.
            
        Returns:
            OrderLog con detalles de la ejecución.
        """
        timestamp = datetime.now().isoformat()
        
        try:
            # Obtener precio actual si no se especificó expected_price
            if expected_price is None:
                quote = self.get_quote(symbol)
                if "error" not in quote:
                    expected_price = quote["ask"] if side == "buy" else quote["bid"]
            
            # Ejecutar orden
            if order_type == "market":
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    type=order_type,
                    time_in_force='day'
                )
            else:  # limit
                if limit_price is None:
                    raise ValueError("limit_price requerido para órdenes limit")
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side=side,
                    type=order_type,
                    time_in_force='day',
                    limit_price=limit_price
                )
            
            # Crear log
            order_log = OrderLog(
                timestamp=timestamp,
                symbol=symbol,
                side=side,
                qty=qty,
                order_type=order_type,
                status=order.status,
                filled_price=float(order.filled_avg_price) if order.filled_avg_price else None,
                expected_price=expected_price,
                slippage=None,  # Calcular después de fill
                order_id=order.id,
            )
            
            # Calcular slippage si hay filled_price
            if order_log.filled_price and expected_price:
                if side == "buy":
                    order_log.slippage = (order_log.filled_price - expected_price) / expected_price
                else:
                    order_log.slippage = (expected_price - order_log.filled_price) / expected_price
            
            self._log_order(order_log)
            return order_log
            
        except Exception as e:
            order_log = OrderLog(
                timestamp=timestamp,
                symbol=symbol,
                side=side,
                qty=qty,
                order_type=order_type,
                status="error",
                filled_price=None,
                expected_price=expected_price,
                slippage=None,
                order_id="",
                error=str(e),
            )
            self._log_order(order_log)
            return order_log
    
    def close_position(self, symbol: str) -> OrderLog:
        """
        Cierra una posición completamente.
        
        Args:
            symbol: Ticker a cerrar.
            
        Returns:
            OrderLog de la orden de cierre.
        """
        positions = self.get_positions()
        position = next((p for p in positions if p["symbol"] == symbol), None)
        
        if not position:
            return OrderLog(
                timestamp=datetime.now().isoformat(),
                symbol=symbol,
                side="sell",
                qty=0,
                order_type="market",
                status="error",
                filled_price=None,
                expected_price=None,
                slippage=None,
                order_id="",
                error=f"No position found for {symbol}",
            )
        
        side = "sell" if position["side"] == "long" else "buy"
        return self.place_order(symbol, qty=abs(position["qty"]), side=side)
    
    def close_all_positions(self) -> List[OrderLog]:
        """
        Cierra todas las posiciones abiertas.
        
        Returns:
            Lista de OrderLogs.
        """
        positions = self.get_positions()
        logs = []
        
        for pos in positions:
            log = self.close_position(pos["symbol"])
            logs.append(log)
        
        return logs
    
    def get_order_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtiene historial de órdenes desde SQLite.
        
        Args:
            limit: Número máximo de órdenes.
            
        Returns:
            Lista de órdenes ordenadas por fecha descendente.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM order_logs 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    
    def is_market_open(self) -> bool:
        """Verifica si el mercado está abierto."""
        clock = self.api.get_clock()
        return clock.is_open
    
    def get_market_hours(self) -> Dict[str, str]:
        """Obtiene horario del mercado."""
        clock = self.api.get_clock()
        return {
            "is_open": clock.is_open,
            "next_open": str(clock.next_open),
            "next_close": str(clock.next_close),
        }
````

## File: src/ml/__init__.py
````python
# ML module
from .features import FeatureEngineer
from .model import MLStrategy, MLModel

__all__ = ["FeatureEngineer", "MLStrategy", "MLModel"]
````

## File: src/ml/optimization.py
````python
"""Optimización de hiperparámetros con Optuna."""

import optuna
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import asdict

from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.base import clone

from .model import MLModel


class ModelOptimizer:
    """
    Optimizador de hiperparámetros usando Optuna.
    Soporta RF, XGBoost, LightGBM.
    """

    def __init__(self, n_trials: int = 50, cv_folds: int = 5):
        """
        Args:
            n_trials: Número de intentos de optimización.
            cv_folds: Folds para TimeSeriesSplit cross-validation.
        """
        self.n_trials = n_trials
        self.cv_folds = cv_folds

    def optimize(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        model_type: str = "random_forest",
        metric: str = "f1",
    ) -> Dict[str, Any]:
        """
        Ejecuta la optimización y retorna los mejores parámetros.
        
        Args:
            X: Features DataFrame.
            y: Target Series.
            model_type: Tipo de modelo a optimizar.
            metric: Métrica a maximizar ('accuracy', 'precision', 'recall', 'f1').
            
        Returns:
            Diccionario con los mejores parámetros encontrados.
        """
        # Definir función objetivo para Optuna
        def objective(trial):
            params = self._suggest_params(trial, model_type)
            
            # Instanciar modelo base
            model_class = MLModel.SUPPORTED_MODELS[model_type]
            model = model_class(**params)
            
            # Pipeline con scaler (importante para evitar leakage)
            # Para árboles a veces no es crítico escalar, pero es buena práctica
            # especialmente modelos sensibles a magnitud.
            pipeline = Pipeline([
                ("scaler", StandardScaler()),
                ("model", model)
            ])
            
            # CV temporal
            # OJO: Se usaba len(X) >= cv_folds * 10 en MLModel, aquí asumimos datasize suficiente
            tscv = TimeSeriesSplit(n_splits=self.cv_folds)
            
            # Scoring
            # sklearn metrics string names: 'accuracy', 'precision', 'recall', 'f1'
            # Para imbalanced data, 'f1_weighted' o 'f1_macro' puede ser mejor,
            # pero mantendremos simple 'f1' (clase positiva 1) si es binaria.
            scoring = metric if metric != "f1" else "f1"  # Simplificación
            
            try:
                scores = cross_val_score(
                    pipeline, X, y, cv=tscv, scoring=scoring, n_jobs=-1
                )
                return scores.mean()
            except Exception as e:
                # Si falla una combinación por alguna razón, retornamos valor bajo
                return 0.0

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=self.n_trials)

        return study.best_params

    def _suggest_params(self, trial: optuna.Trial, model_type: str) -> Dict[str, Any]:
        """Sugiere parámetros según el tipo de modelo."""
        if model_type == "random_forest":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                "max_depth": trial.suggest_int("max_depth", 3, 20),
                "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
                "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
                "random_state": 42,
                "n_jobs": -1,
                "class_weight": "balanced",
            }
            
        elif model_type == "gradient_boosting":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                "random_state": 42,
            }
            
        elif model_type == "xgboost":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                "max_depth": trial.suggest_int("max_depth", 3, 12),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
                "random_state": 42,
                "n_jobs": -1,
                # "scale_pos_weight" se podría tunear si se calcula ratio neg/pos
            }
            
        elif model_type == "lightgbm":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                "max_depth": trial.suggest_int("max_depth", -1, 15),
                "num_leaves": trial.suggest_int("num_leaves", 20, 100),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
                "random_state": 42,
                "n_jobs": -1,
                "class_weight": "balanced",
                # "verbosity": -1,
            }
            
        return {}
````

## File: src/optimization/__init__.py
````python
"""Módulo de optimización avanzada."""

from .wfo import WalkForwardOptimizer, WFOResult

__all__ = ["WalkForwardOptimizer", "WFOResult"]
````

## File: src/optimization/wfo.py
````python
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
````

## File: src/strategy/__init__.py
````python
# Strategy layer
from .base import Strategy
from .ma_cross import MACrossStrategy

__all__ = ["Strategy", "MACrossStrategy"]
````

## File: src/strategy/base.py
````python
"""Clase base abstracta para estrategias de trading."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd


@dataclass
class SignalResult:
    """
    Resultado de generación de señales.
    
    Attributes:
        signals: DataFrame con columnas 'entries' y 'exits' (bool).
        features: DataFrame con indicadores calculados (opcional).
    """
    signals: pd.DataFrame
    features: pd.DataFrame | None = None

    def __post_init__(self):
        """Valida que signals tenga las columnas requeridas."""
        required_cols = {"entries", "exits"}
        if not required_cols.issubset(self.signals.columns):
            missing = required_cols - set(self.signals.columns)
            raise ValueError(f"signals missing required columns: {missing}")


class Strategy(ABC):
    """
    Clase base abstracta para estrategias de trading.
    
    Output Contract:
        - signals: DataFrame con columnas 'entries' y 'exits' (bool)
        - índice alineado con el DataFrame de precios de entrada
        - features: indicadores calculados (opcional, para debugging/análisis)
    """

    @abstractmethod
    def generate_signals(self, prices: pd.DataFrame) -> SignalResult:
        """
        Genera señales de entrada/salida basadas en precios.

        Args:
            prices: DataFrame con columnas [open, high, low, close, volume]
                    e índice DatetimeIndex.

        Returns:
            SignalResult con signals (entries/exits) y features opcionales.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre de la estrategia para logs/reportes."""
        pass

    @property
    @abstractmethod
    def params(self) -> dict:
        """
        Parámetros de la estrategia para reproducibilidad.
        
        Returns:
            Dict con todos los parámetros configurables.
        """
        pass

    def validate_prices(self, prices: pd.DataFrame) -> None:
        """
        Valida que el DataFrame de precios tenga el formato correcto.

        Args:
            prices: DataFrame a validar.

        Raises:
            ValueError: Si faltan columnas requeridas o está vacío.
        """
        if prices.empty:
            raise ValueError("prices DataFrame is empty")

        required_cols = {"open", "high", "low", "close"}
        missing = required_cols - set(prices.columns)
        if missing:
            raise ValueError(f"prices missing required columns: {missing}")

        if not isinstance(prices.index, pd.DatetimeIndex):
            raise ValueError("prices index must be DatetimeIndex")
````

## File: src/strategy/ma_cross.py
````python
"""Estrategia Moving Average Crossover."""

import pandas as pd

from .base import Strategy, SignalResult
from .indicators import sma


class MACrossStrategy(Strategy):
    """
    Estrategia de cruce de medias móviles.
    
    - Entry (long): MA rápida cruza arriba de MA lenta
    - Exit: MA rápida cruza abajo de MA lenta
    
    Soporta tanto SMA como EMA.
    """

    def __init__(
        self,
        fast_period: int = 10,
        slow_period: int = 50,
        ma_type: str = "sma",
    ):
        """
        Args:
            fast_period: Período de la MA rápida.
            slow_period: Período de la MA lenta.
            ma_type: Tipo de MA ('sma' o 'ema').
        """
        if fast_period >= slow_period:
            raise ValueError(
                f"fast_period ({fast_period}) must be < slow_period ({slow_period})"
            )
        if fast_period < 1:
            raise ValueError("fast_period must be >= 1")
        if ma_type not in ("sma", "ema"):
            raise ValueError(f"ma_type must be 'sma' or 'ema', got '{ma_type}'")

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.ma_type = ma_type

    @property
    def name(self) -> str:
        return f"MACross_{self.ma_type.upper()}_{self.fast_period}_{self.slow_period}"

    @property
    def params(self) -> dict:
        return {
            "fast_period": self.fast_period,
            "slow_period": self.slow_period,
            "ma_type": self.ma_type,
        }

    def generate_signals(self, prices: pd.DataFrame) -> SignalResult:
        """
        Genera señales de entrada/salida basadas en cruce de MAs.

        Args:
            prices: DataFrame OHLCV.

        Returns:
            SignalResult con entries/exits y features (MAs calculadas).
        """
        self.validate_prices(prices)

        close = prices["close"]

        # Calcular medias móviles
        if self.ma_type == "sma":
            from .indicators import sma as ma_func
        else:
            from .indicators import ema as ma_func

        fast_ma = ma_func(close, self.fast_period)
        slow_ma = ma_func(close, self.slow_period)

        # Detectar cruces
        # Entry: fast cruza arriba de slow (fast > slow y antes fast <= slow)
        fast_above_slow = fast_ma > slow_ma
        entries = fast_above_slow & (~fast_above_slow.shift(1).fillna(False))

        # Exit: fast cruza abajo de slow (fast < slow y antes fast >= slow)
        fast_below_slow = fast_ma < slow_ma
        exits = fast_below_slow & (~fast_below_slow.shift(1).fillna(False))

        # Crear DataFrame de señales
        signals = pd.DataFrame(
            {"entries": entries, "exits": exits},
            index=prices.index,
        )

        # Features para análisis/debugging
        features = pd.DataFrame(
            {
                f"ma_fast_{self.fast_period}": fast_ma,
                f"ma_slow_{self.slow_period}": slow_ma,
                "fast_above_slow": fast_above_slow,
            },
            index=prices.index,
        )

        return SignalResult(signals=signals, features=features)
````

## File: src/__init__.py
````python
# src package
````

## File: tests/__init__.py
````python
# Tests package
````

## File: tests/test_data.py
````python
"""Tests para la capa de datos."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from src.data.cache import CacheManager
from src.data.schemas import OHLCVBar, DataMetadata


class TestCacheManager:
    """Tests para CacheManager."""

    def test_get_cache_path(self, tmp_path):
        """Verifica que genera paths correctos."""
        cache = CacheManager(tmp_path)

        path = cache.get_cache_path("SPY", "1d")
        assert path == tmp_path / "SPY_1d.parquet"

        # Normaliza a mayúsculas
        path = cache.get_cache_path("aapl", "1h")
        assert path == tmp_path / "AAPL_1h.parquet"

    def test_save_and_load(self, tmp_path):
        """Verifica guardar y cargar desde caché."""
        cache = CacheManager(tmp_path)

        # Crear DataFrame de prueba
        df = pd.DataFrame({
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.0, 102.0],
            "volume": [1000, 1100],
        })

        path = cache.get_cache_path("TEST", "1d")
        cache.save_to_cache(df, path)

        # Verify file exists
        assert path.exists()

        # Load and compare
        loaded = cache.load_from_cache(path)
        pd.testing.assert_frame_equal(df, loaded)

    def test_is_cache_valid_nonexistent(self, tmp_path):
        """Caché inexistente no es válido."""
        cache = CacheManager(tmp_path)
        path = cache.get_cache_path("NOEXIST", "1d")
        assert not cache.is_cache_valid(path)

    def test_is_cache_valid_fresh(self, tmp_path):
        """Caché recién creado es válido."""
        cache = CacheManager(tmp_path, max_age_hours=24)

        df = pd.DataFrame({"close": [100.0]})
        path = cache.get_cache_path("TEST", "1d")
        cache.save_to_cache(df, path)

        assert cache.is_cache_valid(path)


class TestOHLCVBar:
    """Tests para OHLCVBar schema."""

    def test_valid_bar(self):
        """Bar válida se crea correctamente."""
        bar = OHLCVBar(
            timestamp=datetime.now(),
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=10000,
        )
        assert bar.close == 103.0

    def test_invalid_high_less_than_low(self):
        """High < low debe fallar."""
        with pytest.raises(ValueError, match="high.*must be >= low"):
            OHLCVBar(
                timestamp=datetime.now(),
                open=100.0,
                high=95.0,  # Invalid: less than low
                low=98.0,
                close=100.0,
                volume=10000,
            )

    def test_invalid_negative_price(self):
        """Precios negativos deben fallar."""
        with pytest.raises(ValueError):
            OHLCVBar(
                timestamp=datetime.now(),
                open=-100.0,  # Invalid
                high=105.0,
                low=98.0,
                close=103.0,
                volume=10000,
            )


class TestDataMetadata:
    """Tests para DataMetadata."""

    def test_create_metadata(self):
        """Metadata se crea correctamente."""
        meta = DataMetadata(
            ticker="SPY",
            timeframe="1d",
            source="yfinance",
            timezone="America/New_York",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            bar_count=252,
        )
        assert meta.ticker == "SPY"
        assert meta.bar_count == 252
````

## File: tests/test_strategy.py
````python
"""Tests para el motor de estrategia."""

from datetime import datetime, timedelta

import pandas as pd
import pytest

from src.strategy.base import Strategy, SignalResult
from src.strategy.ma_cross import MACrossStrategy


def create_test_prices(n_bars: int = 100, trend: str = "up") -> pd.DataFrame:
    """Crea DataFrame de precios para testing."""
    dates = pd.date_range(start="2024-01-01", periods=n_bars, freq="D")

    if trend == "up":
        close = [100 + i * 0.5 for i in range(n_bars)]
    elif trend == "down":
        close = [100 - i * 0.5 for i in range(n_bars)]
    else:  # oscillating
        close = [100 + 10 * ((-1) ** i) for i in range(n_bars)]

    return pd.DataFrame({
        "open": [c - 1 for c in close],
        "high": [c + 2 for c in close],
        "low": [c - 2 for c in close],
        "close": close,
        "volume": [10000] * n_bars,
    }, index=dates)


class TestMACrossStrategy:
    """Tests para MACrossStrategy."""

    def test_init_valid_params(self):
        """Inicialización con parámetros válidos."""
        strategy = MACrossStrategy(fast_period=10, slow_period=50)
        assert strategy.fast_period == 10
        assert strategy.slow_period == 50

    def test_init_invalid_fast_greater_than_slow(self):
        """fast >= slow debe fallar."""
        with pytest.raises(ValueError, match="fast_period.*must be < slow_period"):
            MACrossStrategy(fast_period=50, slow_period=10)

    def test_init_invalid_fast_equals_slow(self):
        """fast == slow debe fallar."""
        with pytest.raises(ValueError, match="fast_period.*must be < slow_period"):
            MACrossStrategy(fast_period=20, slow_period=20)

    def test_generate_signals_returns_correct_type(self):
        """generate_signals retorna SignalResult."""
        strategy = MACrossStrategy(fast_period=5, slow_period=20)
        prices = create_test_prices(100)

        result = strategy.generate_signals(prices)

        assert isinstance(result, SignalResult)
        assert "entries" in result.signals.columns
        assert "exits" in result.signals.columns

    def test_signals_aligned_with_prices(self):
        """Señales tienen mismo índice que precios."""
        strategy = MACrossStrategy(fast_period=5, slow_period=20)
        prices = create_test_prices(100)

        result = strategy.generate_signals(prices)

        assert len(result.signals) == len(prices)
        pd.testing.assert_index_equal(result.signals.index, prices.index)

    def test_features_include_moving_averages(self):
        """Features incluyen MAs calculadas."""
        strategy = MACrossStrategy(fast_period=5, slow_period=20)
        prices = create_test_prices(100)

        result = strategy.generate_signals(prices)

        assert result.features is not None
        assert "ma_fast_5" in result.features.columns
        assert "ma_slow_20" in result.features.columns

    def test_name_property(self):
        """Nombre de estrategia es correcto."""
        strategy = MACrossStrategy(fast_period=10, slow_period=50, ma_type="sma")
        assert strategy.name == "MACross_SMA_10_50"

    def test_params_property(self):
        """Parámetros para reproducibilidad."""
        strategy = MACrossStrategy(fast_period=10, slow_period=50, ma_type="ema")
        params = strategy.params

        assert params["fast_period"] == 10
        assert params["slow_period"] == 50
        assert params["ma_type"] == "ema"

    def test_empty_prices_raises_error(self):
        """Precios vacíos generan error."""
        strategy = MACrossStrategy(fast_period=5, slow_period=20)
        empty_prices = pd.DataFrame()

        with pytest.raises(ValueError, match="prices.*empty"):
            strategy.generate_signals(empty_prices)


class TestSignalResult:
    """Tests para SignalResult."""

    def test_valid_signal_result(self):
        """SignalResult válido."""
        signals = pd.DataFrame({
            "entries": [True, False, False],
            "exits": [False, False, True],
        })
        result = SignalResult(signals=signals)
        assert len(result.signals) == 3

    def test_missing_columns_raises_error(self):
        """Columnas faltantes generan error."""
        signals = pd.DataFrame({"entries": [True, False]})  # Missing 'exits'

        with pytest.raises(ValueError, match="missing required columns"):
            SignalResult(signals=signals)
````

## File: .env.example
````
# Data
DATA_CACHE_DIR=data/raw
CACHE_MAX_AGE_HOURS=24

# Backtest defaults
INITIAL_CAPITAL=10000.0
DEFAULT_RISK_PCT=0.01

# Costs
COMMISSION_PCT=0.001
SLIPPAGE_PCT=0.0005
````

## File: .gitignore
````
# Environment
.env
.venv/
venv/
__pycache__/
*.py[cod]
*$py.class

# Data cache
data/raw/
data/experiments/

# IDE
.idea/
.vscode/
*.swp

# Testing
.pytest_cache/
.coverage
htmlcov/

# Build
dist/
build/
*.egg-info/
````

## File: api.py
````python
"""
API FastAPI para Trading Backtester Pro

Expone endpoints para:
- Ejecutar backtests
- Obtener datos de mercado
- Estado del bot
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data import DataLoader
from src.strategy import MACrossStrategy
from src.backtest import BacktestEngine, TradingCosts
from src.ml import FeatureEngineer, MLModel, MLStrategy

app = FastAPI(
    title="Trading Backtester Pro API",
    description="API para backtesting y trading algorítmico",
    version="1.0.0",
)

# CORS para permitir requests del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BacktestRequest(BaseModel):
    ticker: str = "SPY"
    timeframe: str = "1d"
    strategy_type: str = "ma_cross"  # ma_cross | ml
    fast_period: int = 10
    slow_period: int = 50
    initial_capital: float = 100000
    commission_pct: float = 0.001
    sl_pct: Optional[float] = None
    tp_pct: Optional[float] = None


class BacktestResponse(BaseModel):
    success: bool
    stats: dict
    equity_data: list
    trades_count: int
    strategy_name: str
    error: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "Trading Backtester Pro API", "status": "online"}


@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/api/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    try:
        # Load data
        loader = DataLoader()
        prices, metadata = loader.load(
            ticker=request.ticker,
            timeframe=request.timeframe,
            use_cache=True
        )
        
        if prices.empty:
            raise HTTPException(status_code=400, detail="No data available for ticker")
        
        # Create strategy
        if request.strategy_type == "ma_cross":
            strategy = MACrossStrategy(
                fast_period=request.fast_period,
                slow_period=request.slow_period
            )
        elif request.strategy_type == "ml":
            # Train ML model
            fe = FeatureEngineer()
            features, target = fe.prepare_dataset(prices, horizon=1, dropna=True)
            
            if len(features) < 100:
                raise HTTPException(status_code=400, detail="Not enough data for ML training")
            
            train_size = int(len(features) * 0.8)
            X_train = features.iloc[:train_size]
            y_train = target.iloc[:train_size]
            
            model = MLModel(model_type="random_forest")
            model.train(X_train, y_train)
            
            strategy = MLStrategy(model=model, feature_engineer=fe)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown strategy: {request.strategy_type}")
        
        # Generate signals
        signal_result = strategy.generate_signals(prices)
        
        # Run backtest
        costs = TradingCosts(
            commission_pct=request.commission_pct,
            slippage_pct=0.0005
        )
        engine = BacktestEngine(
            initial_capital=request.initial_capital,
            costs=costs
        )
        
        result = engine.run(
            prices=prices,
            signals=signal_result.signals,
            sl_pct=request.sl_pct,
            tp_pct=request.tp_pct
        )
        
        # Format equity data for chart
        equity_data = [
            {"date": date.strftime("%Y-%m-%d"), "value": round(value, 2)}
            for date, value in zip(result.equity.index, result.equity.values)
        ]
        
        # Sample if too many points
        if len(equity_data) > 500:
            step = len(equity_data) // 500
            equity_data = equity_data[::step]
        
        # Convert numpy types to native Python types
        def convert_to_native(obj):
            import numpy as np
            if isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, (np.integer,)):
                return int(obj)
            elif isinstance(obj, (np.floating,)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
        
        native_stats = convert_to_native(result.stats)
        
        return BacktestResponse(
            success=True,
            stats=native_stats,
            equity_data=equity_data,
            trades_count=int(result.stats.get("total_trades", 0)),
            strategy_name=strategy.name
        )
        
    except Exception as e:
        return BacktestResponse(
            success=False,
            stats={},
            equity_data=[],
            trades_count=0,
            strategy_name="",
            error=str(e)
        )


@app.get("/api/tickers")
async def get_tickers():
    """Lista de tickers populares."""
    return {
        "tickers": [
            {"symbol": "SPY", "name": "S&P 500 ETF"},
            {"symbol": "QQQ", "name": "Nasdaq 100 ETF"},
            {"symbol": "AAPL", "name": "Apple Inc."},
            {"symbol": "MSFT", "name": "Microsoft Corp."},
            {"symbol": "GOOGL", "name": "Alphabet Inc."},
            {"symbol": "AMZN", "name": "Amazon.com Inc."},
            {"symbol": "TSLA", "name": "Tesla Inc."},
            {"symbol": "NVDA", "name": "NVIDIA Corp."},
            {"symbol": "META", "name": "Meta Platforms"},
            {"symbol": "BTC-USD", "name": "Bitcoin USD"},
            {"symbol": "ETH-USD", "name": "Ethereum USD"},
        ]
    }


@app.get("/api/bot/status")
async def get_bot_status():
    """Estado del bot de trading."""
    try:
        from src.execution import AlpacaExecutor
        executor = AlpacaExecutor()
        account = executor.get_account()
        positions = executor.get_positions()
        
        return {
            "status": "running",
            "account": account,
            "positions": positions,
            "bot_type": "alpaca"
        }
    except Exception as e:
        return {
            "status": "offline",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
````

## File: mt5linux.sh
````bash
#!/bin/bash
# Copyright 2000-2025, MetaQuotes Ltd.

# MetaTrader and WebView2 download urls
URL_MT5="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
URL_WEBVIEW="https://msedge.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/f2910a1e-e5a6-4f17-b52d-7faf525d17f8/MicrosoftEdgeWebview2Setup.exe"

# Wine version to install: stable or devel
WINE_VERSION="stable"

# Prepare versions
. /etc/os-release

echo OS: $NAME $VERSION_ID

echo Update and install...
if [ "$NAME" = "Fedora Linux" ]; then
    echo Update system
    sudo dnf update
    sudo dnf upgrade -y

    echo Choose Wine repo
    sudo rm /etc/yum.repos.d/winehq*
    if (( $VERSION_ID >= 43 )); then
       sudo dnf5 config-manager addrepo --from-repofile=https://dl.winehq.org/wine-builds/fedora/42/winehq.repo
    elif (( $VERSION_ID >= 42 )); then
       sudo dnf5 config-manager addrepo --from-repofile=https://dl.winehq.org/wine-builds/fedora/42/winehq.repo
    else
       sudo dnf5 config-manager addrepo --from-repofile=https://dl.winehq.org/wine-builds/fedora/41/winehq.repo
    fi

    echo Install Wine and Wine Mono
    sudo dnf update
    sudo dnf install winehq-$WINE_VERSION -y
    sudo dnf install wine-mono -y
else
    echo Update system
    sudo apt update
    sudo apt upgrade -y

    echo Get full version
    sudo apt install bc wget curl -y
    VERSION_FULL=$(echo "$VERSION_ID * 100" | bc -l | cut -d "." -f1)

    echo Choose Wine repo
    sudo rm /etc/apt/sources.list.d/winehq*

    sudo dpkg --add-architecture i386
    sudo mkdir -pm755 /etc/apt/keyrings
    sudo wget -O - https://dl.winehq.org/wine-builds/winehq.key | sudo gpg --dearmor -o /etc/apt/keyrings/winehq-archive.key -

    if [ "$NAME" = "Ubuntu" ]; then
        echo Ubuntu found: $NAME $VERSION_ID
        # Choose repository based on Ubuntu version
        if (( $VERSION_FULL >= 2410 )); then
           sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/plucky/winehq-plucky.sources
        elif (( $VERSION_FULL < 2410 )) && (( $VERSION_FULL >= 2400 )); then
           sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/noble/winehq-noble.sources
        elif (( $VERSION_FULL < 2400 )) && (( $VERSION_FULL >= 2300 )); then
           sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/lunar/winehq-lunar.sources
        elif (( $VERSION_FULL < 2300 )) && (( $VERSION_FULL >= 2210 )); then
           sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/kinetic/winehq-kinetic.sources
        elif (( $VERSION_FULL < 2210 )) && (( $VERSION_FULL >= 2100 )); then
           sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/jammy/winehq-jammy.sources
        elif (( $VERSION_FULL < 2100 )) && (($VERSION_FULL >= 2000 )); then
           sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/focal/winehq-focal.sources
        else
           sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/bionic/winehq-bionic.sources
        fi
    elif [ "$NAME" = "Linux Mint" ]; then
        echo Linux Mint found: $NAME $VERSION_ID
        # Choose repository based on Linux Mint version
        if (( $VERSION_FULL >= 2200 )); then
           sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/noble/winehq-noble.sources
        else
           sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/focal/winehq-focal.sources
        fi
    elif [ "$NAME" = "Fedora Linux" ]; then
        echo Fedora Linux found: $NAME $VERSION_ID
        # Choose repository based on Linux Mint version
        if (( $VERSION_FULL >= 2200 )); then
           sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/noble/winehq-noble.sources
        else
           sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/focal/winehq-focal.sources
        fi
    elif [ "$NAME" = "Debian GNU/Linux" ]; then
        echo Debian Linux found: $NAME $VERSION_ID
        # Choose repository based on Debian version
        if (( $VERSION_FULL >= 13 )); then
           sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/debian/dists/trixie/winehq-trixie.sources
        else
           sudo wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/debian/dists/bookworm/winehq-bookworm.sources
        fi
    else
        echo $NAME $VERSION_ID does not supported
        exit
    fi

    echo Install Wine and Wine Mono
    sudo apt update
    sudo apt install --install-recommends winehq-$WINE_VERSION -y
fi

echo Download MetaTrader and WebView2 Runtime
curl $URL_MT5 --output mt5setup.exe
curl $URL_WEBVIEW --output webview2.exe

echo Set environment to Windows 11
WINEPREFIX=~/.mt5 winecfg -v=win11

echo Install WebView2 Runtime
WINEPREFIX=~/.mt5 wine webview2.exe /silent /install

echo Install MetaTrader 5
WINEPREFIX=~/.mt5 wine mt5setup.exe

echo Please reboot OS
````

## File: mt5/SocketServer.mq5
````
//+------------------------------------------------------------------+
//|                                              SocketServer.mq5    |
//|                        Socket Server para recibir órdenes Python |
//+------------------------------------------------------------------+
#property copyright "Trading Bot"
#property link      ""
#property version   "1.00"
#property strict

// Configuración
input int ServerPort = 5555;
input bool EnableLogging = true;

// Variables globales
int serverSocket = -1;
int clientSocket = -1;

//+------------------------------------------------------------------+
//| Expert initialization                                             |
//+------------------------------------------------------------------+
int OnInit()
{
   // Crear socket
   serverSocket = SocketCreate();
   if(serverSocket < 0)
   {
      Print("Error creando socket: ", GetLastError());
      return INIT_FAILED;
   }
   
   // Bind al puerto
   if(!SocketBind(serverSocket, "127.0.0.1", ServerPort))
   {
      Print("Error en bind: ", GetLastError());
      SocketClose(serverSocket);
      return INIT_FAILED;
   }
   
   // Escuchar
   if(!SocketListen(serverSocket, 1))
   {
      Print("Error en listen: ", GetLastError());
      SocketClose(serverSocket);
      return INIT_FAILED;
   }
   
   Print("Socket Server iniciado en puerto ", ServerPort);
   EventSetMillisecondTimer(100);
   
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization                                           |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   if(clientSocket >= 0) SocketClose(clientSocket);
   if(serverSocket >= 0) SocketClose(serverSocket);
   Print("Socket Server cerrado");
}

//+------------------------------------------------------------------+
//| Timer function                                                    |
//+------------------------------------------------------------------+
void OnTimer()
{
   // Aceptar nueva conexión
   if(clientSocket < 0)
   {
      clientSocket = SocketAccept(serverSocket, 100);
      if(clientSocket >= 0)
         Print("Cliente conectado");
   }
   
   // Leer datos del cliente
   if(clientSocket >= 0)
   {
      uchar buffer[];
      int len = SocketRead(clientSocket, buffer, 1024, 100);
      
      if(len > 0)
      {
         string command = CharArrayToString(buffer, 0, len);
         if(EnableLogging) Print("Recibido: ", command);
         
         string response = ProcessCommand(command);
         SendResponse(response);
      }
      else if(len == 0)
      {
         // Cliente desconectado
         SocketClose(clientSocket);
         clientSocket = -1;
         Print("Cliente desconectado");
      }
   }
}

//+------------------------------------------------------------------+
//| Procesar comando                                                  |
//+------------------------------------------------------------------+
string ProcessCommand(string cmd)
{
   // Extraer valores del JSON simple
   string action = GetJsonValue(cmd, "action");
   string symbol = GetJsonValue(cmd, "symbol");
   double volume = StringToDouble(GetJsonValue(cmd, "volume"));
   
   if(symbol == "") symbol = Symbol();
   if(volume <= 0) volume = 0.01;
   
   if(action == "ping")
      return "{\"status\":\"ok\",\"message\":\"pong\"}";
   
   if(action == "account")
      return GetAccountInfo();
   
   if(action == "positions")
      return GetPositions();
   
   if(action == "buy")
      return ExecuteTrade(symbol, volume, ORDER_TYPE_BUY);
   
   if(action == "sell")
      return ExecuteTrade(symbol, volume, ORDER_TYPE_SELL);
   
   if(action == "close")
      return ClosePos(symbol);
   
   return "{\"status\":\"error\",\"message\":\"Unknown action\"}";
}

//+------------------------------------------------------------------+
//| Ejecutar trade                                                    |
//+------------------------------------------------------------------+
string ExecuteTrade(string sym, double vol, ENUM_ORDER_TYPE type)
{
   MqlTradeRequest request;
   MqlTradeResult result;
   ZeroMemory(request);
   ZeroMemory(result);
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = sym;
   request.volume = vol;
   request.type = type;
   request.deviation = 10;
   request.magic = 123456;
   request.comment = "PythonBot";
   
   if(type == ORDER_TYPE_BUY)
      request.price = SymbolInfoDouble(sym, SYMBOL_ASK);
   else
      request.price = SymbolInfoDouble(sym, SYMBOL_BID);
   
   if(OrderSend(request, result))
   {
      Print("Trade ejecutado: ", sym, " ", EnumToString(type));
      return StringFormat("{\"status\":\"ok\",\"order_id\":%d,\"price\":%.5f}", 
                         result.order, result.price);
   }
   
   Print("Error trade: ", GetLastError());
   return StringFormat("{\"status\":\"error\",\"code\":%d}", GetLastError());
}

//+------------------------------------------------------------------+
//| Cerrar posición                                                   |
//+------------------------------------------------------------------+
string ClosePos(string sym)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionSelectByTicket(ticket))
      {
         if(PositionGetString(POSITION_SYMBOL) == sym)
         {
            MqlTradeRequest request;
            MqlTradeResult result;
            ZeroMemory(request);
            ZeroMemory(result);
            
            request.action = TRADE_ACTION_DEAL;
            request.symbol = sym;
            request.volume = PositionGetDouble(POSITION_VOLUME);
            request.position = ticket;
            request.deviation = 10;
            
            if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
            {
               request.type = ORDER_TYPE_SELL;
               request.price = SymbolInfoDouble(sym, SYMBOL_BID);
            }
            else
            {
               request.type = ORDER_TYPE_BUY;
               request.price = SymbolInfoDouble(sym, SYMBOL_ASK);
            }
            
            if(OrderSend(request, result))
               return "{\"status\":\"ok\",\"message\":\"Position closed\"}";
         }
      }
   }
   return "{\"status\":\"error\",\"message\":\"No position found\"}";
}

//+------------------------------------------------------------------+
//| Info de cuenta                                                    |
//+------------------------------------------------------------------+
string GetAccountInfo()
{
   return StringFormat(
      "{\"status\":\"ok\",\"balance\":%.2f,\"equity\":%.2f,\"margin\":%.2f,\"free_margin\":%.2f}",
      AccountInfoDouble(ACCOUNT_BALANCE),
      AccountInfoDouble(ACCOUNT_EQUITY),
      AccountInfoDouble(ACCOUNT_MARGIN),
      AccountInfoDouble(ACCOUNT_MARGIN_FREE)
   );
}

//+------------------------------------------------------------------+
//| Posiciones abiertas                                               |
//+------------------------------------------------------------------+
string GetPositions()
{
   string result = "{\"status\":\"ok\",\"positions\":[";
   
   for(int i = 0; i < PositionsTotal(); i++)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionSelectByTicket(ticket))
      {
         if(i > 0) result += ",";
         string posType = PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? "buy" : "sell";
         result += StringFormat(
            "{\"symbol\":\"%s\",\"volume\":%.2f,\"profit\":%.2f,\"type\":\"%s\"}",
            PositionGetString(POSITION_SYMBOL),
            PositionGetDouble(POSITION_VOLUME),
            PositionGetDouble(POSITION_PROFIT),
            posType
         );
      }
   }
   
   result += "]}";
   return result;
}

//+------------------------------------------------------------------+
//| Extraer valor de JSON                                             |
//+------------------------------------------------------------------+
string GetJsonValue(string json, string key)
{
   string search = "\"" + key + "\"";
   int pos = StringFind(json, search);
   if(pos < 0) return "";
   
   int colonPos = StringFind(json, ":", pos);
   if(colonPos < 0) return "";
   
   int start = colonPos + 1;
   
   // Saltar espacios
   while(start < StringLen(json) && StringGetCharacter(json, start) == ' ')
      start++;
   
   // Si es string
   if(StringGetCharacter(json, start) == '"')
   {
      start++;
      int end = StringFind(json, "\"", start);
      if(end < 0) return "";
      return StringSubstr(json, start, end - start);
   }
   
   // Si es número
   int end = start;
   while(end < StringLen(json))
   {
      ushort c = StringGetCharacter(json, end);
      if(c == ',' || c == '}' || c == ' ') break;
      end++;
   }
   
   return StringSubstr(json, start, end - start);
}

//+------------------------------------------------------------------+
//| Enviar respuesta                                                  |
//+------------------------------------------------------------------+
void SendResponse(string response)
{
   if(clientSocket < 0) return;
   
   uchar buffer[];
   int len = StringToCharArray(response, buffer) - 1;
   if(len > 0)
      SocketSend(clientSocket, buffer, len);
   
   if(EnableLogging) Print("Enviado: ", response);
}
````

## File: scripts/live_bot.py
````python
#!/usr/bin/env python
"""
Bot de Trading Automatizado - Alpaca Paper Trading

Ejecuta estrategia MA Cross o ML en loop continuo.
Revisa señales cada vez que cierra una vela.

Uso:
    uv run python scripts/live_bot.py --ticker SPY --strategy ma_cross --interval 60

Mantenerlo corriendo en background:
    nohup uv run python scripts/live_bot.py --ticker SPY &

Ver logs:
    tail -f logs/bot.log
"""

import argparse
import time
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_bot(ticker: str, strategy_type: str, interval_minutes: int):
    """Loop principal del bot."""
    from src.data import DataLoader
    from src.strategy import MACrossStrategy
    from src.execution import AlpacaExecutor
    
    # Inicializar
    loader = DataLoader()
    executor = AlpacaExecutor()
    
    if strategy_type == "ma_cross":
        # Parámetros más rápidos para generar señales más frecuentes
        strategy = MACrossStrategy(fast_period=5, slow_period=20)
    else:
        raise ValueError(f"Estrategia no soportada: {strategy_type}")
    
    logger.info(f"🚀 Bot iniciado: {ticker} | {strategy.name} | cada {interval_minutes}min")
    
    # Mostrar estado de cuenta
    account = executor.get_account()
    logger.info(f"💰 Equity: ${account['equity']:,.2f} | Cash: ${account['cash']:,.2f}")
    
    last_signal = None
    
    while True:
        try:
            # Verificar si mercado está abierto
            if not executor.is_market_open():
                logger.info("📴 Mercado cerrado. Esperando...")
                time.sleep(interval_minutes * 60)
                continue
            
            # Cargar datos recientes
            prices, _ = loader.load(ticker, timeframe="1h")
            
            if prices.empty:
                logger.warning(f"Sin datos para {ticker}")
                time.sleep(60)
                continue
            
            # Generar señales
            signal_result = strategy.generate_signals(prices)
            
            # Obtener última señal
            latest_entry = signal_result.signals["entries"].iloc[-1]
            latest_exit = signal_result.signals["exits"].iloc[-1]
            
            # Obtener posiciones actuales
            positions = executor.get_positions()
            has_position = any(p["symbol"] == ticker for p in positions)
            
            # Lógica de ejecución
            if latest_entry and not has_position and last_signal != "entry":
                # COMPRAR
                quote = executor.get_quote(ticker)
                if "error" not in quote:
                    # Calcular qty basado en 10% del capital
                    account = executor.get_account()
                    qty = int((account["cash"] * 0.10) / quote["ask"])
                    
                    if qty > 0:
                        logger.info(f"🟢 SEÑAL DE COMPRA: {ticker} x{qty}")
                        order = executor.place_order(ticker, qty=qty, side="buy")
                        logger.info(f"   → Orden: {order.status} | ID: {order.order_id}")
                        last_signal = "entry"
            
            elif latest_exit and has_position and last_signal != "exit":
                # VENDER
                logger.info(f"🔴 SEÑAL DE VENTA: {ticker}")
                order = executor.close_position(ticker)
                logger.info(f"   → Orden: {order.status} | ID: {order.order_id}")
                last_signal = "exit"
            
            else:
                logger.info(f"⏳ Sin señal | Entry: {latest_entry} | Exit: {latest_exit} | Posición: {has_position}")
            
            # Esperar próxima iteración
            time.sleep(interval_minutes * 60)
            
        except KeyboardInterrupt:
            logger.info("🛑 Bot detenido por usuario")
            break
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            time.sleep(60)  # Esperar y reintentar


def main():
    parser = argparse.ArgumentParser(description="Bot de Trading Automatizado")
    parser.add_argument("--ticker", default="SPY", help="Ticker a operar")
    parser.add_argument("--strategy", default="ma_cross", choices=["ma_cross"], help="Estrategia")
    parser.add_argument("--interval", type=int, default=60, help="Intervalo en minutos")
    
    args = parser.parse_args()
    
    run_bot(
        ticker=args.ticker,
        strategy_type=args.strategy,
        interval_minutes=args.interval,
    )


if __name__ == "__main__":
    main()
````

## File: src/evaluation/__init__.py
````python
# Evaluation layer
from .metrics import calculate_sharpe, calculate_max_drawdown, calculate_win_rate
from .reports import ReportGenerator
from .monte_carlo import MonteCarloSimulator, MonteCarloResult

__all__ = [
    "calculate_sharpe", 
    "calculate_max_drawdown", 
    "calculate_win_rate", 
    "ReportGenerator",
    "MonteCarloSimulator",
    "MonteCarloResult",
]
````

## File: src/evaluation/metrics.py
````python
"""Cálculo de métricas de trading (fuera de UI)."""

import numpy as np
import pandas as pd


def calculate_sharpe(
    returns: pd.Series,
    rf: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """
    Calcula Sharpe ratio anualizado.
    
    Args:
        returns: Serie de retornos (no porcentaje, i.e., 0.01 = 1%).
        rf: Risk-free rate anualizado (default 0).
        periods_per_year: Períodos por año para anualización.
            - 252 para daily
            - 252 * 6.5 para hourly (mercado abierto)
            - 252 * 6.5 * 4 para 15min
            
    Returns:
        Sharpe ratio anualizado.
    """
    if returns.empty or returns.std() == 0:
        return 0.0

    # Convertir rf a período
    rf_per_period = rf / periods_per_year

    excess_returns = returns - rf_per_period
    sharpe = excess_returns.mean() / excess_returns.std()

    # Anualizar
    return sharpe * np.sqrt(periods_per_year)


def calculate_max_drawdown(equity: pd.Series) -> float:
    """
    Calcula maximum drawdown como porcentaje.
    
    Args:
        equity: Serie con valores del portfolio.
        
    Returns:
        Max drawdown como porcentaje negativo (e.g., -15.5).
    """
    if equity.empty:
        return 0.0

    # Running maximum
    running_max = equity.expanding().max()

    # Drawdown en cada punto
    drawdown = (equity - running_max) / running_max * 100

    return drawdown.min()


def calculate_win_rate(trades: pd.DataFrame, pnl_column: str = "pnl") -> float:
    """
    Calcula porcentaje de trades ganadores.
    
    Args:
        trades: DataFrame con trades.
        pnl_column: Nombre de la columna con P&L.
        
    Returns:
        Win rate como porcentaje (0-100).
    """
    if trades.empty or pnl_column not in trades.columns:
        return 0.0

    wins = (trades[pnl_column] > 0).sum()
    total = len(trades)

    return (wins / total) * 100 if total > 0 else 0.0


def calculate_profit_factor(trades: pd.DataFrame, pnl_column: str = "pnl") -> float:
    """
    Calcula profit factor (ganancias brutas / pérdidas brutas).
    
    Args:
        trades: DataFrame con trades.
        pnl_column: Nombre de la columna con P&L.
        
    Returns:
        Profit factor. >1 significa sistema rentable.
    """
    if trades.empty or pnl_column not in trades.columns:
        return 0.0

    pnl = trades[pnl_column]
    gross_profits = pnl[pnl > 0].sum()
    gross_losses = abs(pnl[pnl < 0].sum())

    if gross_losses == 0:
        return float("inf") if gross_profits > 0 else 0.0

    return gross_profits / gross_losses


def calculate_cagr(
    equity: pd.Series,
    periods_per_year: int = 252,
) -> float:
    """
    Calcula Compound Annual Growth Rate.
    
    Args:
        equity: Serie con valores del portfolio.
        periods_per_year: Períodos por año.
        
    Returns:
        CAGR como porcentaje.
    """
    if equity.empty or len(equity) < 2:
        return 0.0

    total_return = equity.iloc[-1] / equity.iloc[0]
    n_periods = len(equity)
    n_years = n_periods / periods_per_year

    if n_years <= 0:
        return 0.0

    cagr = (total_return ** (1 / n_years) - 1) * 100
    return cagr


def get_periods_per_year(timeframe: str) -> int:
    """
    Retorna número de períodos por año según timeframe.
    
    Args:
        timeframe: Intervalo (1d, 1h, 15m, etc).
        
    Returns:
        Períodos aproximados por año de trading.
    """
    mapping = {
        "1m": 252 * 6.5 * 60,   # ~98,280
        "5m": 252 * 6.5 * 12,   # ~19,656
        "15m": 252 * 6.5 * 4,   # ~6,552
        "30m": 252 * 6.5 * 2,   # ~3,276
        "1h": 252 * 6.5,        # ~1,638
        "1d": 252,
        "1wk": 52,
        "1mo": 12,
    }
    return mapping.get(timeframe, 252)


def calculate_sortino_ratio(
    returns: pd.Series,
    rf: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """
    Calcula Sortino ratio anualizado.
    
    Similar a Sharpe pero solo penaliza la volatilidad negativa (downside risk).
    Mejor métrica para evaluar riesgo real de pérdida.
    
    Args:
        returns: Serie de retornos.
        rf: Risk-free rate anualizado.
        periods_per_year: Períodos por año.
        
    Returns:
        Sortino ratio anualizado.
    """
    if returns.empty:
        return 0.0
    
    rf_per_period = rf / periods_per_year
    excess_returns = returns - rf_per_period
    
    # Solo retornos negativos para downside deviation
    downside_returns = excess_returns[excess_returns < 0]
    
    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return float("inf") if excess_returns.mean() > 0 else 0.0
    
    downside_std = downside_returns.std()
    sortino = excess_returns.mean() / downside_std
    
    return sortino * np.sqrt(periods_per_year)


def calculate_calmar_ratio(
    equity: pd.Series,
    periods_per_year: int = 252,
) -> float:
    """
    Calcula Calmar ratio (CAGR / Max Drawdown).
    
    Mide retorno relativo al peor drawdown.
    Importante para saber cuánto tiempo tomaría recuperarse.
    
    Args:
        equity: Serie con valores del portfolio.
        periods_per_year: Períodos por año.
        
    Returns:
        Calmar ratio. Mayor es mejor.
    """
    if equity.empty or len(equity) < 2:
        return 0.0
    
    cagr = calculate_cagr(equity, periods_per_year)
    max_dd = abs(calculate_max_drawdown(equity))
    
    if max_dd == 0:
        return float("inf") if cagr > 0 else 0.0
    
    return cagr / max_dd
````

## File: src/evaluation/reports.py
````python
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
````

## File: src/execution/__init__.py
````python
"""Módulo de ejecución para trading."""

from .alpaca_engine import AlpacaExecutor
from .mt5_executor import MT5Executor

__all__ = ["AlpacaExecutor", "MT5Executor"]
````

## File: src/execution/mt5_executor.py
````python
"""MT5 File-based Executor - Cliente Python para comunicarse con MT5 via archivos.

Escribe comandos JSON a un archivo que MT5 lee y ejecuta.
Más compatible con Wine/Linux que sockets.

Uso:
    executor = MT5FileExecutor()
    result = executor.buy("EURUSD", volume=0.1)
    print(result)
"""

import json
import time
import sqlite3
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from pathlib import Path


@dataclass
class MT5OrderLog:
    """Log de una orden ejecutada en MT5."""
    timestamp: str
    symbol: str
    side: str
    volume: float
    status: str
    order_id: Optional[str]
    price: Optional[float]
    error: Optional[str] = None


class MT5FileExecutor:
    """
    Ejecutor de órdenes para MT5 via comunicación por archivos.
    
    Requiere que FileCommander.mq5 esté corriendo en MT5.
    """
    
    def __init__(
        self,
        mt5_files_path: str = None,
        command_file: str = "python_commands.txt",
        response_file: str = "mt5_response.txt",
        timeout: float = 5.0,
        db_path: str = "data/mt5_orders.db",
    ):
        """
        Args:
            mt5_files_path: Ruta a la carpeta MQL5/Files de MT5.
            command_file: Nombre del archivo de comandos.
            response_file: Nombre del archivo de respuestas.
            timeout: Segundos a esperar por respuesta.
            db_path: Path para SQLite de logging.
        """
        # Detectar path de MT5 automáticamente
        if mt5_files_path is None:
            home = Path.home()
            mt5_files_path = home / ".mt5" / "drive_c" / "Program Files" / "MetaTrader 5" / "MQL5" / "Files"
        
        self.mt5_files_path = Path(mt5_files_path)
        self.command_file = self.mt5_files_path / command_file
        self.response_file = self.mt5_files_path / response_file
        self.timeout = timeout
        
        # Setup database para logging
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Inicializa la base de datos SQLite para logging."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mt5_order_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                side TEXT,
                volume REAL,
                status TEXT,
                order_id TEXT,
                price REAL,
                error TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _log_order(self, order_log: MT5OrderLog):
        """Guarda log de orden en SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO mt5_order_logs 
            (timestamp, symbol, side, volume, status, order_id, price, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_log.timestamp,
            order_log.symbol,
            order_log.side,
            order_log.volume,
            order_log.status,
            order_log.order_id,
            order_log.price,
            order_log.error,
        ))
        
        conn.commit()
        conn.close()
    
    def _send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía comando a MT5 escribiendo archivo y esperando respuesta.
        """
        try:
            # Limpiar respuesta anterior si existe
            if self.response_file.exists():
                self.response_file.unlink()
            
            # Escribir comando
            json_cmd = json.dumps(command)
            self.command_file.write_text(json_cmd)
            
            # Esperar respuesta
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                if self.response_file.exists():
                    response_text = self.response_file.read_text()
                    if response_text:
                        self.response_file.unlink()  # Limpiar
                        return json.loads(response_text)
                time.sleep(0.1)
            
            return {"status": "error", "message": "Timeout esperando respuesta de MT5"}
            
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Invalid JSON response: {e}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def ping(self) -> bool:
        """Verifica conexión con MT5."""
        result = self._send_command({"action": "ping"})
        return result.get("status") == "ok"
    
    def get_account(self) -> Dict[str, Any]:
        """Obtiene información de la cuenta MT5."""
        result = self._send_command({"action": "account"})
        
        if result.get("status") == "ok":
            return {
                "balance": result.get("balance", 0),
                "equity": result.get("equity", 0),
                "margin": result.get("margin", 0),
            }
        return {"error": result.get("message", "Unknown error")}
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Obtiene posiciones abiertas."""
        result = self._send_command({"action": "positions"})
        
        if result.get("status") == "ok":
            return result.get("positions", [])
        return []
    
    def buy(self, symbol: str, volume: float = 0.01) -> MT5OrderLog:
        """Ejecuta orden de compra."""
        timestamp = datetime.now().isoformat()
        
        result = self._send_command({
            "action": "buy",
            "symbol": symbol,
            "volume": volume,
        })
        
        order_log = MT5OrderLog(
            timestamp=timestamp,
            symbol=symbol,
            side="buy",
            volume=volume,
            status=result.get("status", "error"),
            order_id=str(result.get("order_id", "")),
            price=result.get("price"),
            error=result.get("message") if result.get("status") != "ok" else None,
        )
        
        self._log_order(order_log)
        return order_log
    
    def sell(self, symbol: str, volume: float = 0.01) -> MT5OrderLog:
        """Ejecuta orden de venta."""
        timestamp = datetime.now().isoformat()
        
        result = self._send_command({
            "action": "sell",
            "symbol": symbol,
            "volume": volume,
        })
        
        order_log = MT5OrderLog(
            timestamp=timestamp,
            symbol=symbol,
            side="sell",
            volume=volume,
            status=result.get("status", "error"),
            order_id=str(result.get("order_id", "")),
            price=result.get("price"),
            error=result.get("message") if result.get("status") != "ok" else None,
        )
        
        self._log_order(order_log)
        return order_log
    
    def close_position(self, symbol: str) -> MT5OrderLog:
        """Cierra posición abierta."""
        timestamp = datetime.now().isoformat()
        
        result = self._send_command({
            "action": "close",
            "symbol": symbol,
        })
        
        order_log = MT5OrderLog(
            timestamp=timestamp,
            symbol=symbol,
            side="close",
            volume=0,
            status=result.get("status", "error"),
            order_id="",
            price=None,
            error=result.get("message") if result.get("status") != "ok" else None,
        )
        
        self._log_order(order_log)
        return order_log
    
    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str = "buy",
        **kwargs
    ) -> MT5OrderLog:
        """Interfaz compatible con AlpacaExecutor."""
        if side == "buy":
            return self.buy(symbol, volume=qty)
        else:
            return self.sell(symbol, volume=qty)
    
    def is_connected(self) -> bool:
        """Verifica si FileCommander está corriendo en MT5."""
        return self.ping()


# Alias para compatibilidad
MT5Executor = MT5FileExecutor
````

## File: src/strategy/indicators.py
````python
"""Wrappers para indicadores técnicos usando pandas-ta."""

import pandas as pd
import pandas_ta as ta


def sma(series: pd.Series, period: int) -> pd.Series:
    """
    Simple Moving Average.

    Args:
        series: Serie de precios (típicamente close).
        period: Número de períodos para el promedio.

    Returns:
        Serie con SMA calculado.
    """
    result = ta.sma(series, length=period)
    if result is None:
        # Fallback: usar pandas rolling si pandas-ta falla
        return series.rolling(window=period).mean()
    return result


def ema(series: pd.Series, period: int) -> pd.Series:
    """
    Exponential Moving Average.

    Args:
        series: Serie de precios.
        period: Número de períodos.

    Returns:
        Serie con EMA calculado.
    """
    result = ta.ema(series, length=period)
    if result is None:
        return series.ewm(span=period, adjust=False).mean()
    return result


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index.

    Args:
        series: Serie de precios.
        period: Número de períodos (default 14).

    Returns:
        Serie con RSI (0-100).
    """
    result = ta.rsi(series, length=period)
    if result is None:
        # Fallback manual RSI
        delta = series.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    return result


def atr(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> pd.Series:
    """
    Average True Range.

    Args:
        high: Serie de precios high.
        low: Serie de precios low.
        close: Serie de precios close.
        period: Número de períodos (default 14).

    Returns:
        Serie con ATR.
    """
    result = ta.atr(high=high, low=low, close=close, length=period)
    if result is None:
        # Fallback manual ATR
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    return result


def bollinger_bands(
    series: pd.Series, period: int = 20, std: float = 2.0
) -> pd.DataFrame:
    """
    Bollinger Bands.

    Args:
        series: Serie de precios.
        period: Número de períodos para SMA.
        std: Número de desviaciones estándar.

    Returns:
        DataFrame con columnas [lower, mid, upper, bandwidth, percent].
    """
    return ta.bbands(series, length=period, std=std)


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """
    Moving Average Convergence Divergence.

    Args:
        series: Serie de precios.
        fast: Período EMA rápido.
        slow: Período EMA lento.
        signal: Período para línea de señal.

    Returns:
        DataFrame con columnas [MACD, histogram, signal].
    """
    return ta.macd(series, fast=fast, slow=slow, signal=signal)
````

## File: src/ui/styles.py
````python
"""Estilos premium para Trading Backtester Pro - Tema Dark Fintech."""

css = """
<style>
/* ============================================
   TRADING BACKTESTER PRO - PREMIUM DARK THEME
   ============================================ */

/* Import Premium Fonts */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* CSS Variables for consistency */
:root {
    --bg-primary: #0a0e17;
    --bg-secondary: #111827;
    --bg-card: rgba(17, 24, 39, 0.7);
    --bg-card-hover: rgba(30, 41, 59, 0.8);
    --border-color: rgba(99, 102, 241, 0.2);
    --border-glow: rgba(99, 102, 241, 0.4);
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --accent-primary: #6366f1;
    --accent-secondary: #8b5cf6;
    --accent-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
    --success: #10b981;
    --success-glow: rgba(16, 185, 129, 0.3);
    --danger: #ef4444;
    --danger-glow: rgba(239, 68, 68, 0.3);
    --warning: #f59e0b;
    --glass-bg: rgba(15, 23, 42, 0.6);
    --glass-border: rgba(148, 163, 184, 0.1);
}

/* Base Styles */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: var(--bg-primary) !important;
}

/* Main Container Background with subtle pattern */
.main .block-container {
    background: 
        radial-gradient(ellipse at 20% 0%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 100%, rgba(139, 92, 246, 0.06) 0%, transparent 50%),
        var(--bg-primary);
    padding-top: 2rem !important;
}

/* Animated gradient background for header area */
@keyframes gradientFlow {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Sidebar - Sleek Dark */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%) !important;
    border-right: 1px solid var(--border-color) !important;
}

section[data-testid="stSidebar"] .stMarkdown {
    color: var(--text-secondary);
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

/* Headers with gradient */
h1 {
    font-size: 2.8rem !important;
    font-weight: 700 !important;
    background: var(--accent-gradient) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    letter-spacing: -0.02em;
    margin-bottom: 0.5rem !important;
}

h2 {
    font-size: 1.5rem !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    border-bottom: 2px solid var(--accent-primary);
    padding-bottom: 0.5rem;
    margin-top: 2rem !important;
}

h3 {
    font-size: 1.2rem !important;
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
}

/* Glassmorphism Cards */
div[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.8rem !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
}

div[data-testid="stMetricLabel"] {
    font-size: 0.85rem !important;
    color: var(--text-secondary) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-weight: 500 !important;
}

div[data-testid="stMetricDelta"] > div {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 500 !important;
}

/* Metric card container styling */
div[data-testid="metric-container"] {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 
        0 4px 6px -1px rgba(0, 0, 0, 0.2),
        0 2px 4px -1px rgba(0, 0, 0, 0.1),
        inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

div[data-testid="metric-container"]:hover {
    border-color: var(--border-glow) !important;
    transform: translateY(-2px) !important;
    box-shadow: 
        0 10px 15px -3px rgba(0, 0, 0, 0.3),
        0 4px 6px -2px rgba(0, 0, 0, 0.15),
        0 0 20px var(--border-glow),
        inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
}

/* Premium Button Styling */
.stButton > button {
    background: var(--accent-gradient) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 0.75rem 2rem !important;
    letter-spacing: 0.02em !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 
        0 4px 14px 0 rgba(99, 102, 241, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    position: relative !important;
    overflow: hidden !important;
}

.stButton > button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
}

.stButton > button:hover {
    transform: translateY(-3px) scale(1.02) !important;
    box-shadow: 
        0 8px 25px 0 rgba(99, 102, 241, 0.5),
        0 0 30px rgba(139, 92, 246, 0.3) !important;
}

.stButton > button:hover::before {
    left: 100%;
}

.stButton > button:active {
    transform: translateY(-1px) scale(0.98) !important;
}

/* Input fields */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    transition: all 0.2s ease !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div:focus-within,
.stNumberInput > div > div > input:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2) !important;
}

/* Slider styling */
.stSlider > div > div > div {
    background: var(--accent-gradient) !important;
}

.stSlider > div > div > div > div {
    background: white !important;
    border: 2px solid var(--accent-primary) !important;
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4) !important;
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-secondary) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 8px !important;
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}

.stTabs [aria-selected="true"] {
    background: var(--accent-gradient) !important;
    color: white !important;
}

.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
    background: rgba(99, 102, 241, 0.1) !important;
    color: var(--text-primary) !important;
}

/* DataFrame/Table styling */
.stDataFrame {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid var(--border-color) !important;
}

.stDataFrame [data-testid="stDataFrameResizable"] {
    background: var(--bg-secondary) !important;
}

/* Expander styling */
.streamlit-expanderHeader {
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}

.streamlit-expanderHeader:hover {
    border-color: var(--border-glow) !important;
}

/* Progress bar */
.stProgress > div > div {
    background: var(--accent-gradient) !important;
    border-radius: 10px !important;
}

/* Success/Error/Warning messages */
.stSuccess {
    background: rgba(16, 185, 129, 0.1) !important;
    border: 1px solid var(--success) !important;
    border-radius: 12px !important;
}

.stError {
    background: rgba(239, 68, 68, 0.1) !important;
    border: 1px solid var(--danger) !important;
    border-radius: 12px !important;
}

.stWarning {
    background: rgba(245, 158, 11, 0.1) !important;
    border: 1px solid var(--warning) !important;
    border-radius: 12px !important;
}

/* Plotly chart background */
.js-plotly-plot .plotly .modebar {
    opacity: 0.6 !important;
    transition: opacity 0.2s !important;
}

.js-plotly-plot .plotly .modebar:hover {
    opacity: 1 !important;
}

/* Custom animated pulse for live indicators */
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(1.05); }
}

.live-indicator {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Glow effect for positive values */
.positive-glow {
    text-shadow: 0 0 10px var(--success-glow);
    color: var(--success) !important;
}

/* Glow effect for negative values */
.negative-glow {
    text-shadow: 0 0 10px var(--danger-glow);
    color: var(--danger) !important;
}

/* Premium card component */
.premium-card {
    background: var(--glass-bg);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.premium-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.5), transparent);
}

.premium-card:hover {
    border-color: var(--border-glow);
    transform: translateY(-4px);
    box-shadow: 
        0 20px 40px -15px rgba(0, 0, 0, 0.4),
        0 0 30px rgba(99, 102, 241, 0.15);
}

/* Stat badge */
.stat-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 20px;
    padding: 0.4rem 1rem;
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--accent-primary);
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: var(--accent-primary);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--accent-secondary);
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Responsive adjustments */
@media (max-width: 768px) {
    h1 {
        font-size: 2rem !important;
    }
    
    .premium-card {
        padding: 1rem;
    }
}
</style>
"""


def apply_styles():
    """Apply premium dark theme to Streamlit app."""
    import streamlit as st
    st.markdown(css, unsafe_allow_html=True)


def premium_metric_card(label: str, value: str, delta: str = None, delta_color: str = "normal"):
    """
    Create a premium styled metric card.
    
    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta value
        delta_color: 'normal', 'inverse', or specific color
    """
    import streamlit as st
    
    delta_html = ""
    if delta:
        color = "#10b981" if delta.startswith("+") or delta_color == "inverse" else "#ef4444"
        if delta_color == "inverse":
            color = "#ef4444" if delta.startswith("+") else "#10b981"
        delta_html = f'<div style="color: {color}; font-size: 0.9rem; font-weight: 500; font-family: JetBrains Mono, monospace;">{delta}</div>'
    
    html = f'''
    <div class="premium-card">
        <div style="color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; font-weight: 500;">
            {label}
        </div>
        <div style="color: #f8fafc; font-size: 2rem; font-weight: 700; font-family: JetBrains Mono, monospace; margin-bottom: 0.25rem;">
            {value}
        </div>
        {delta_html}
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)


def section_header(title: str, icon: str = ""):
    """Create a styled section header."""
    import streamlit as st
    
    html = f'''
    <div style="display: flex; align-items: center; gap: 0.75rem; margin: 2rem 0 1rem 0;">
        <span style="font-size: 1.5rem;">{icon}</span>
        <h2 style="margin: 0; padding: 0; border: none; background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 1.4rem; font-weight: 600;">
            {title}
        </h2>
        <div style="flex: 1; height: 2px; background: linear-gradient(90deg, rgba(99, 102, 241, 0.4), transparent);"></div>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)
````

## File: tests/test_ml.py
````python
"""Tests para el módulo de ML."""

import pandas as pd
import numpy as np
import pytest

from src.ml.features import FeatureEngineer
from src.ml.model import MLModel, MLStrategy, MLModelMetrics


def create_test_prices(n_bars: int = 200) -> pd.DataFrame:
    """Crea DataFrame de precios para testing con tendencia y ruido."""
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=n_bars, freq="D")
    
    # Crear precios con tendencia + ruido
    trend = np.linspace(100, 150, n_bars)
    noise = np.random.randn(n_bars) * 2
    close = trend + noise
    
    return pd.DataFrame({
        "open": close - np.random.rand(n_bars),
        "high": close + np.random.rand(n_bars) * 2,
        "low": close - np.random.rand(n_bars) * 2,
        "close": close,
        "volume": np.random.randint(10000, 100000, n_bars),
    }, index=dates)


class TestFeatureEngineer:
    """Tests para FeatureEngineer."""

    def test_create_features_returns_dataframe(self):
        """create_features retorna DataFrame."""
        fe = FeatureEngineer()
        prices = create_test_prices()
        
        features = fe.create_features(prices)
        
        assert isinstance(features, pd.DataFrame)
        assert len(features) == len(prices)

    def test_features_have_expected_columns(self):
        """Features incluyen columnas esperadas."""
        fe = FeatureEngineer()
        prices = create_test_prices()
        
        features = fe.create_features(prices)
        
        # Verificar algunas features clave
        assert "return_1d" in features.columns
        assert "rsi" in features.columns
        assert "atr" in features.columns
        assert "ma_cross" in features.columns
        assert "momentum_5d" in features.columns

    def test_create_target_returns_series(self):
        """create_target retorna Series binaria."""
        fe = FeatureEngineer()
        prices = create_test_prices()
        
        target = fe.create_target(prices, horizon=1)
        
        assert isinstance(target, pd.Series)
        assert set(target.dropna().unique()).issubset({0, 1})

    def test_prepare_dataset_removes_nan(self):
        """prepare_dataset elimina NaN cuando dropna=True."""
        fe = FeatureEngineer()
        prices = create_test_prices()
        
        features, target = fe.prepare_dataset(prices, dropna=True)
        
        assert not features.isna().any().any()
        assert not target.isna().any()
        assert len(features) == len(target)


class TestMLModel:
    """Tests para MLModel."""

    def test_init_random_forest(self):
        """Inicializar con RandomForest."""
        model = MLModel(model_type="random_forest")
        assert model.model_type == "random_forest"

    def test_init_invalid_model_type(self):
        """Tipo de modelo inválido genera error."""
        with pytest.raises(ValueError, match="Model type must be one of"):
            MLModel(model_type="invalid_model")

    def test_train_returns_metrics(self):
        """train retorna MLModelMetrics."""
        fe = FeatureEngineer()
        prices = create_test_prices(200)
        X, y = fe.prepare_dataset(prices)
        
        model = MLModel(model_type="random_forest")
        metrics = model.train(X, y, test_size=0.2, cv_folds=3)
        
        assert isinstance(metrics, MLModelMetrics)
        assert 0 <= metrics.accuracy <= 1
        assert 0 <= metrics.precision <= 1

    def test_predict_after_train(self):
        """predict funciona después de entrenar."""
        fe = FeatureEngineer()
        prices = create_test_prices(200)
        X, y = fe.prepare_dataset(prices)
        
        model = MLModel(model_type="random_forest")
        model.train(X, y)
        
        predictions = model.predict(X)
        
        assert len(predictions) == len(X)
        assert set(predictions).issubset({0, 1})

    def test_predict_before_train_raises_error(self):
        """predict sin entrenar genera error."""
        model = MLModel()
        X = pd.DataFrame({"a": [1, 2, 3]})
        
        with pytest.raises(RuntimeError, match="must be trained"):
            model.predict(X)


class TestMLStrategy:
    """Tests para MLStrategy."""

    def test_generate_signals_returns_signal_result(self):
        """generate_signals retorna SignalResult."""
        # Entrenar modelo primero
        fe = FeatureEngineer()
        prices = create_test_prices(200)
        X, y = fe.prepare_dataset(prices)
        
        model = MLModel(model_type="random_forest")
        model.train(X, y)
        
        strategy = MLStrategy(model=model, feature_engineer=fe)
        result = strategy.generate_signals(prices)
        
        assert "entries" in result.signals.columns
        assert "exits" in result.signals.columns
        assert len(result.signals) == len(prices)

    def test_name_property(self):
        """name refleja configuración."""
        fe = FeatureEngineer()
        model = MLModel(model_type="gradient_boosting")
        # Entrenar para que no falle
        prices = create_test_prices(200)
        X, y = fe.prepare_dataset(prices)
        model.train(X, y)
        
        strategy = MLStrategy(model=model, feature_engineer=fe, entry_threshold=0.7)
        
        assert "gradient_boosting" in strategy.name
        assert "0.7" in strategy.name


class TestNoLookaheadBias:
    """Test crítico: verifica que no hay lookahead bias en features."""

    def test_features_do_not_change_with_future_data(self):
        """
        Verifica que features en día t NO cambian si agregamos datos del día t+1.
        
        Si feature[día_t] cambia cuando agregamos día_t+1,
        significa que tiene lookahead bias (usa info del futuro).
        """
        fe = FeatureEngineer()
        prices = create_test_prices(200)
        
        # Tomar subset hasta día 100
        prices_until_100 = prices.iloc[:100]
        
        # Calcular features
        features_100 = fe.create_features(prices_until_100)
        
        # Ahora tomar hasta día 101 (agregamos 1 día más)
        prices_until_101 = prices.iloc[:101]
        features_101 = fe.create_features(prices_until_101)
        
        # Verificar que features en día 99 NO cambiaron
        day_99_before = features_100.iloc[-1]
        day_99_after = features_101.iloc[-2]
        
        # Deben ser IDÉNTICOS (tolerancia numérica para floats)
        pd.testing.assert_series_equal(
            day_99_before, 
            day_99_after,
            check_names=False,
            rtol=1e-10,
        )

    def test_features_use_lagged_prices(self):
        """
        Verifica que features usan datos de t-1, no t.
        
        El primer dato de features debería ser NaN porque 
        no hay datos anteriores disponibles.
        """
        fe = FeatureEngineer()
        prices = create_test_prices(100)
        
        features = fe.create_features(prices)
        
        # La primera fila debería tener NaN en features que requieren lookback
        first_row = features.iloc[0]
        
        # return_1d, sma_5, etc. deberían ser NaN en la primera fila
        # porque usan .shift(1) + rolling
        assert pd.isna(first_row["return_1d"]), "return_1d debería ser NaN en primera fila"
        
    def test_target_predicts_future(self):
        """
        Verifica que target predice el futuro, no el pasado.
        
        target[día_t] = 1 si precio[día_t+horizon] > precio[día_t]
        """
        fe = FeatureEngineer()
        prices = create_test_prices(100)
        
        # Usar prepare_dataset que elimina NaN correctamente
        features, target = fe.prepare_dataset(prices, horizon=1, dropna=True)
        
        # Debería haber menos filas que prices (por NaN eliminados)
        assert len(target) < len(prices)
        
        # Verificar que target[t] refleja si precio[t+1] > precio[t]
        # Usamos los índices originales del target
        for idx in target.index[:-1]:  # Excluir último porque no tiene siguiente
            loc = prices.index.get_loc(idx)
            if loc + 1 < len(prices):
                expected = 1 if prices["close"].iloc[loc + 1] > prices["close"].iloc[loc] else 0
                actual = target.loc[idx]
                assert actual == expected, f"Target incorrecto en {idx}"
````

## File: src/data/loader.py
````python
"""DataLoader para descarga y carga de datos de precios."""

from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

from .cache import CacheManager
from .schemas import DataMetadata


class DataLoader:
    """
    Carga datos de precios desde yfinance con caché local.
    
    Output Contract:
        - prices: DataFrame con columnas [open, high, low, close, volume]
        - índice: DatetimeIndex (timezone-aware, America/New_York)
        - metadata: dict con timezone, fuente, frecuencia, rango
    """

    # Mapeo de timeframes a intervalos de yfinance
    TIMEFRAME_MAP = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "1d": "1d",
        "1wk": "1wk",
        "1mo": "1mo",
    }

    # Límites de historia para intradía (yfinance restrictions)
    INTRADAY_LIMITS = {
        "1m": 7,      # 7 días
        "5m": 60,     # 60 días
        "15m": 60,    # 60 días
        "30m": 60,    # 60 días
        "1h": 730,    # 2 años
    }

    def __init__(
        self,
        cache_dir: Path | str = "data/raw",
        source: str = "yfinance",
        cache_max_age_hours: int = 24,
    ):
        """
        Args:
            cache_dir: Directorio para caché de datos.
            source: Fuente de datos (solo 'yfinance' por ahora).
            cache_max_age_hours: Horas antes de refrescar caché.
        """
        self.cache = CacheManager(cache_dir, cache_max_age_hours)
        self.source = source

    def load(
        self,
        ticker: str,
        timeframe: str = "1d",
        start: datetime | str | None = None,
        end: datetime | str | None = None,
        use_cache: bool = True,
    ) -> tuple[pd.DataFrame, DataMetadata]:
        """
        Carga datos de precios para un ticker.

        Args:
            ticker: Símbolo del activo (e.g., 'SPY', 'AAPL').
            timeframe: Intervalo temporal ('1d', '1h', '15m', etc.).
            start: Fecha de inicio (default: máximo disponible).
            end: Fecha de fin (default: hoy).
            use_cache: Si usar caché local.

        Returns:
            Tuple de (DataFrame OHLCV, DataMetadata).

        Raises:
            ValueError: Si el timeframe no es válido.
        """
        if timeframe not in self.TIMEFRAME_MAP:
            raise ValueError(
                f"Invalid timeframe '{timeframe}'. "
                f"Valid options: {list(self.TIMEFRAME_MAP.keys())}"
            )

        cache_path = self.cache.get_cache_path(ticker, timeframe)

        # Intentar cargar desde caché
        if use_cache and self.cache.is_cache_valid(cache_path):
            df = self.cache.load_from_cache(cache_path)
            # Filtrar por fechas si se especifican
            df = self._filter_by_dates(df, start, end)
            metadata = self._create_metadata(ticker, timeframe, df)
            return df, metadata

        # Descargar desde yfinance
        df = self._download_from_yfinance(ticker, timeframe, start, end)

        # Guardar en caché (datos completos, sin filtrar)
        if use_cache and not df.empty:
            self.cache.save_to_cache(df, cache_path)

        # Filtrar por fechas para retornar
        df = self._filter_by_dates(df, start, end)
        metadata = self._create_metadata(ticker, timeframe, df)

        return df, metadata

    def _download_from_yfinance(
        self,
        ticker: str,
        timeframe: str,
        start: datetime | str | None,
        end: datetime | str | None,
    ) -> pd.DataFrame:
        """Descarga datos desde yfinance."""
        interval = self.TIMEFRAME_MAP[timeframe]

        # Para intradía, yfinance tiene límites de historia
        period = None
        if timeframe in self.INTRADAY_LIMITS and start is None:
            # Usar period en vez de start/end para intradía sin fecha específica
            days = self.INTRADAY_LIMITS[timeframe]
            period = f"{days}d"
            start = None
            end = None
        elif start is None and timeframe in ["1d", "1wk", "1mo"]:
            # Para datos diarios/semanales sin rango, usar 2 años por defecto
            period = "2y"

        yf_ticker = yf.Ticker(ticker)

        if period:
            df = yf_ticker.history(period=period, interval=interval)
        else:
            df = yf_ticker.history(start=start, end=end, interval=interval)

        if df.empty:
            return pd.DataFrame()

        # Normalizar nombres de columnas a minúsculas
        df.columns = df.columns.str.lower()

        # Mantener solo OHLCV
        ohlcv_cols = ["open", "high", "low", "close", "volume"]
        df = df[[c for c in ohlcv_cols if c in df.columns]]

        # Asegurar que el índice tiene nombre
        df.index.name = "timestamp"
        
        # Validar calidad de datos (especialmente para intradía)
        self._validate_data_quality(df, ticker, timeframe)

        return df
    
    def _validate_data_quality(self, df: pd.DataFrame, ticker: str, timeframe: str):
        """
        Valida calidad de datos y emite warnings si hay problemas.
        
        Especialmente importante para datos intradía de yfinance.
        """
        import warnings
        
        if df.empty:
            return
        
        issues = []
        
        # 1. Verificar duplicados en índice
        if df.index.duplicated().any():
            n_dups = df.index.duplicated().sum()
            issues.append(f"⚠️ {n_dups} timestamps duplicados detectados")
        
        # 2. Detectar gaps en datos intradía
        if timeframe in ["1m", "5m", "15m", "30m", "1h"]:
            expected_freq = {"1m": "1min", "5m": "5min", "15m": "15min", 
                           "30m": "30min", "1h": "1h"}[timeframe]
            
            # Calcular gaps (solo días de trading, ignorar noches/fines de semana)
            time_diffs = df.index.to_series().diff()
            if len(time_diffs) > 1:
                # Gap grande = más de 4x el intervalo esperado (para ignorar overnight)
                interval_td = pd.Timedelta(expected_freq)
                large_gaps = (time_diffs > interval_td * 4).sum()
                if large_gaps > 10:
                    issues.append(f"⚠️ {large_gaps} gaps detectados en datos (normal para overnight/weekends)")
        
        # 3. Verificar rango de datos para intradía
        if timeframe in self.INTRADAY_LIMITS:
            days_of_data = (df.index[-1] - df.index[0]).days
            expected_days = self.INTRADAY_LIMITS[timeframe]
            if days_of_data < expected_days * 0.5:
                issues.append(f"⚠️ Solo {days_of_data} días de datos (yfinance limita intradía a ~{expected_days} días)")
        
        # 4. Verificar valores NaN
        nan_count = df.isna().sum().sum()
        if nan_count > 0:
            issues.append(f"⚠️ {nan_count} valores NaN en datos")
        
        # 5. Verificar precios cero o negativos
        if (df[["open", "high", "low", "close"]] <= 0).any().any():
            issues.append("⚠️ Precios cero o negativos detectados")
        
        # Emitir warnings consolidados
        if issues:
            warning_msg = f"\n[DataLoader] {ticker} ({timeframe}):\n" + "\n".join(issues)
            warnings.warn(warning_msg, UserWarning, stacklevel=3)

    def _filter_by_dates(
        self,
        df: pd.DataFrame,
        start: datetime | str | None,
        end: datetime | str | None,
    ) -> pd.DataFrame:
        """Filtra DataFrame por rango de fechas."""
        if df.empty:
            return df

        if start:
            if isinstance(start, str):
                start = pd.Timestamp(start)
            # Hacer timezone-aware si el índice lo es
            if df.index.tz is not None and start.tz is None:
                start = start.tz_localize(df.index.tz)
            df = df[df.index >= start]

        if end:
            if isinstance(end, str):
                end = pd.Timestamp(end)
            if df.index.tz is not None and end.tz is None:
                end = end.tz_localize(df.index.tz)
            df = df[df.index <= end]

        return df

    def _create_metadata(
        self, ticker: str, timeframe: str, df: pd.DataFrame
    ) -> DataMetadata:
        """Crea metadata para el dataset."""
        if df.empty:
            return DataMetadata(
                ticker=ticker.upper(),
                timeframe=timeframe,
                source=self.source,
                timezone="UTC",
                start_date=datetime.now(),
                end_date=datetime.now(),
                bar_count=0,
            )

        tz = str(df.index.tz) if df.index.tz else "UTC"

        return DataMetadata(
            ticker=ticker.upper(),
            timeframe=timeframe,
            source=self.source,
            timezone=tz,
            start_date=df.index.min().to_pydatetime(),
            end_date=df.index.max().to_pydatetime(),
            bar_count=len(df),
        )
````

## File: tests/test_backtest.py
````python
"""Tests para el motor de backtesting."""

import pandas as pd
import pytest

from src.backtest.costs import TradingCosts
from src.backtest.sizing import calculate_position_size, calculate_fixed_fraction_size


class TestTradingCosts:
    """Tests para TradingCosts."""

    def test_default_costs(self):
        """Costos por defecto."""
        costs = TradingCosts()
        assert costs.commission_pct == 0.001
        assert costs.slippage_pct == 0.0005

    def test_total_cost_pct(self):
        """Costo total es entry + exit."""
        costs = TradingCosts(commission_pct=0.001, slippage_pct=0.0005)
        # (0.001 + 0.0005) * 2 = 0.003
        assert costs.total_cost_pct == 0.003

    def test_apply_to_price_buy(self):
        """Precio de compra se ajusta hacia arriba."""
        costs = TradingCosts(commission_pct=0.001, slippage_pct=0.0005)
        price = 100.0
        adjusted = costs.apply_to_price(price, is_buy=True)
        # 100 * (1 + 0.0015) = 100.15
        assert adjusted == pytest.approx(100.15)

    def test_apply_to_price_sell(self):
        """Precio de venta se ajusta hacia abajo."""
        costs = TradingCosts(commission_pct=0.001, slippage_pct=0.0005)
        price = 100.0
        adjusted = costs.apply_to_price(price, is_buy=False)
        # 100 * (1 - 0.0015) = 99.85
        assert adjusted == pytest.approx(99.85)

    def test_negative_commission_raises_error(self):
        """Comisión negativa genera error."""
        with pytest.raises(ValueError, match="commission_pct must be >= 0"):
            TradingCosts(commission_pct=-0.001)


class TestPositionSizing:
    """Tests para funciones de sizing."""

    def test_calculate_position_size(self):
        """Sizing con riesgo fijo."""
        # capital=10000, risk=1%, entry=100, stop=95
        # risk_per_share = 5, amount_to_risk = 100
        # position = 100 / 5 = 20 shares
        size = calculate_position_size(
            capital=10000,
            risk_pct=0.01,
            entry_price=100,
            stop_loss_price=95,
        )
        assert size == 20.0

    def test_calculate_position_size_different_risk(self):
        """Sizing con 2% de riesgo."""
        size = calculate_position_size(
            capital=10000,
            risk_pct=0.02,
            entry_price=100,
            stop_loss_price=95,
        )
        assert size == 40.0

    def test_position_size_invalid_capital(self):
        """Capital <= 0 genera error."""
        with pytest.raises(ValueError, match="capital must be > 0"):
            calculate_position_size(
                capital=0,
                risk_pct=0.01,
                entry_price=100,
                stop_loss_price=95,
            )

    def test_position_size_stop_above_entry(self):
        """Stop >= entry genera error (para longs)."""
        with pytest.raises(ValueError, match="stop_loss_price must be < entry_price"):
            calculate_position_size(
                capital=10000,
                risk_pct=0.01,
                entry_price=100,
                stop_loss_price=105,  # Invalid for long
            )

    def test_fixed_fraction_size(self):
        """Sizing con fracción fija."""
        # capital=10000, fraction=10%, price=100
        # investment = 1000, shares = 10
        size = calculate_fixed_fraction_size(
            capital=10000,
            fraction=0.1,
            price=100,
        )
        assert size == 10.0

    def test_fixed_fraction_invalid_fraction(self):
        """Fracción > 1 genera error."""
        with pytest.raises(ValueError, match="fraction must be between 0 and 1"):
            calculate_fixed_fraction_size(
                capital=10000,
                fraction=1.5,
                price=100,
            )


class TestExecutionPrice:
    """Tests para verificar que las órdenes se ejecutan al precio correcto (open t+1)."""

    @pytest.fixture
    def sample_prices(self):
        """Crea datos de precio con valores conocidos para verificar ejecución."""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        return pd.DataFrame({
            "open": [100, 102, 104, 103, 105, 106, 104, 107, 108, 110],
            "high": [101, 105, 106, 105, 108, 109, 107, 110, 111, 112],
            "low": [99, 101, 102, 101, 103, 104, 102, 105, 106, 108],
            "close": [100, 103, 105, 102, 106, 107, 103, 108, 109, 111],
            "volume": [1000] * 10,
        }, index=dates)

    @pytest.fixture
    def sample_signals(self, sample_prices):
        """Señal de entrada en día 1, salida en día 5."""
        signals = pd.DataFrame(index=sample_prices.index)
        signals["entries"] = [False, True, False, False, False, False, False, False, False, False]
        signals["exits"] = [False, False, False, False, False, True, False, False, False, False]
        return signals

    def test_entry_executes_at_next_open(self, sample_prices, sample_signals):
        """
        Verifica que una señal en día t se ejecuta al open de día t+1.
        
        Señal de entrada en día 1 (close=103) debe ejecutarse al open de día 2 (=104).
        """
        from src.backtest.engine import BacktestEngine
        from src.backtest.costs import TradingCosts
        
        engine = BacktestEngine(
            initial_capital=10000,
            costs=TradingCosts(commission_pct=0, slippage_pct=0)  # Sin costos para test limpio
        )
        
        result = engine.run(prices=sample_prices, signals=sample_signals)
        
        # Verificar que hay al menos 1 trade
        assert len(result.trades) >= 1, "Debería haber al menos 1 trade"
        
        # El entry_price debería ser el open del día siguiente a la señal
        # Señal en día 1 -> ejecución en día 2 -> open de día 2 = 104
        entry_price = result.trades.iloc[0]["entry_price"]
        expected_open = sample_prices["open"].iloc[2]  # Día 2 (índice 2)
        
        assert entry_price == pytest.approx(expected_open, rel=0.01), \
            f"Entry price {entry_price} debería ser open del día siguiente: {expected_open}"

    def test_exit_executes_at_next_open(self, sample_prices, sample_signals):
        """
        Verifica que una señal de salida en día t se ejecuta al open de día t+1.
        
        Señal de salida en día 5 (close=107) debe ejecutarse al open de día 6 (=104).
        """
        from src.backtest.engine import BacktestEngine
        from src.backtest.costs import TradingCosts
        
        engine = BacktestEngine(
            initial_capital=10000,
            costs=TradingCosts(commission_pct=0, slippage_pct=0)
        )
        
        result = engine.run(prices=sample_prices, signals=sample_signals)
        
        if len(result.trades) >= 1:
            # El exit_price debería ser el open del día siguiente a la señal de salida
            # Señal en día 5 -> ejecución en día 6 -> open de día 6 = 104
            exit_price = result.trades.iloc[0]["exit_price"]
            expected_open = sample_prices["open"].iloc[6]  # Día 6 (índice 6)
            
            assert exit_price == pytest.approx(expected_open, rel=0.01), \
                f"Exit price {exit_price} debería ser open del día siguiente: {expected_open}"


class TestFrequencyAnnualization:
    """Tests para verificar que las métricas se annualizan correctamente según timeframe."""

    def test_sharpe_daily_uses_252_periods(self):
        """Sharpe en datos diarios debe usar 252 períodos para annualización."""
        from src.evaluation.metrics import calculate_sharpe
        import numpy as np
        
        # Crear retornos diarios simulados (252 días = 1 año)
        np.random.seed(42)
        daily_returns = pd.Series(np.random.normal(0.001, 0.02, 252))
        
        sharpe = calculate_sharpe(daily_returns, periods_per_year=252)
        
        # Sharpe debe ser cercano a: mean/std * sqrt(252)
        expected = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        assert sharpe == pytest.approx(expected, rel=0.01)

    def test_sharpe_hourly_uses_more_periods(self):
        """Sharpe en datos horarios debe usar más períodos (~1638 horas de trading/año)."""
        from src.evaluation.metrics import calculate_sharpe
        import numpy as np
        
        np.random.seed(42)
        hourly_returns = pd.Series(np.random.normal(0.0001, 0.005, 100))
        
        # ~6.5 horas de trading por día * 252 ≈ 1638
        periods_hourly = int(252 * 6.5)
        sharpe = calculate_sharpe(hourly_returns, periods_per_year=periods_hourly)
        
        expected = (hourly_returns.mean() / hourly_returns.std()) * np.sqrt(periods_hourly)
        assert sharpe == pytest.approx(expected, rel=0.01)

    def test_freq_inferred_from_daily_index(self):
        """Verifica que freq='1D' se infiere de índice DatetimeIndex diario."""
        from src.backtest.engine import BacktestEngine
        from src.backtest.costs import TradingCosts
        
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        prices = pd.DataFrame({
            "open": range(100, 130),
            "high": range(101, 131),
            "low": range(99, 129),
            "close": range(100, 130),
            "volume": [1000] * 30,
        }, index=dates)
        
        signals = pd.DataFrame({
            "entries": [False] * 30,
            "exits": [False] * 30,
        }, index=dates)
        signals.iloc[5, 0] = True  # Entry día 5
        signals.iloc[15, 1] = True  # Exit día 15
        
        engine = BacktestEngine(initial_capital=10000, costs=TradingCosts())
        result = engine.run(prices=prices, signals=signals)
        
        # Si freq se infirió correctamente, stats debe existir
        assert "sharpe_ratio" in result.stats
        assert result.stats["sharpe_ratio"] is not None
````

## File: README.md
````markdown
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
````

## File: src/backtest/engine.py
````python
"""Motor de backtesting usando vectorbt."""

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd
import vectorbt as vbt

from .costs import TradingCosts


@dataclass
class BacktestResult:
    """
    Resultado de un backtest.
    
    Output Contract:
        - trades: DataFrame con entry/exit time, prices, pnl, fees
        - equity: Series con curva de capital
        - stats: dict con Sharpe, drawdown, win_rate, etc.
    """

    trades: pd.DataFrame
    equity: pd.Series
    stats: dict = field(default_factory=dict)
    portfolio: object = None  # vectorbt Portfolio object

    @property
    def total_return(self) -> float:
        """Retorno total como porcentaje."""
        if self.equity.empty:
            return 0.0
        return (self.equity.iloc[-1] / self.equity.iloc[0] - 1) * 100

    @property
    def num_trades(self) -> int:
        """Número total de trades."""
        return len(self.trades)


class BacktestEngine:
    """
    Motor de backtesting wrapper de vectorbt.
    
    Features:
        - Ejecución t→t+1 (evita lookahead bias)
        - Costos y slippage configurables
        - Métricas estandarizadas
    """

    def __init__(
        self,
        initial_capital: float = 10_000.0,
        costs: TradingCosts | None = None,
    ):
        """
        Args:
            initial_capital: Capital inicial para el backtest.
            costs: Modelo de costos (default: TradingCosts()).
        """
        if initial_capital <= 0:
            raise ValueError("initial_capital must be > 0")

        self.initial_capital = initial_capital
        self.costs = costs or TradingCosts()

    def run(
        self,
        prices: pd.DataFrame,
        signals: pd.DataFrame,
        execution_delay: int = 1,
        size_pct: float = 1.0,
        sl_pct: float | None = None,
        tp_pct: float | None = None,
    ) -> BacktestResult:
        """
        Ejecuta backtest con las señales dadas.

        Args:
            prices: DataFrame OHLCV.
            signals: DataFrame con columnas 'entries' y 'exits' (bool).
            execution_delay: Delay en barras para ejecución (1 = t→t+1).
            size_pct: Porcentaje del capital a usar por trade.
            sl_pct: Stop-loss como porcentaje (e.g., 0.02 = 2% abajo del entry).
            tp_pct: Take-profit como porcentaje (e.g., 0.05 = 5% arriba del entry).

        Returns:
            BacktestResult con trades, equity y stats.
        """
        if prices.empty:
            raise ValueError("prices DataFrame is empty")
        if signals.empty:
            raise ValueError("signals DataFrame is empty")

        # Alinear índices
        common_idx = prices.index.intersection(signals.index)
        prices = prices.loc[common_idx]
        signals = signals.loc[common_idx]

        # Aplicar delay de ejecución (señal en t → ejecución en t+delay)
        # Forzar dtype bool después del shift
        entries = signals["entries"].shift(execution_delay).fillna(False).astype(bool)
        exits = signals["exits"].shift(execution_delay).fillna(False).astype(bool)

        # Usar precio de apertura para ejecución realista
        exec_price = prices["open"] if "open" in prices.columns else prices["close"]

        # Configurar stop-loss y take-profit
        sl_stop = sl_pct if sl_pct is not None else None
        tp_stop = tp_pct if tp_pct is not None else None

        # Inferir frecuencia dinámicamente del índice
        freq = pd.infer_freq(prices.index)
        if freq is None and len(prices.index) >= 2:
            # Fallback: calcular delta entre primeras dos barras
            delta = prices.index[1] - prices.index[0]
            # Convertir a string para vectorbt
            if delta.days >= 1:
                freq = f"{delta.days}D"
            elif delta.seconds >= 3600:
                freq = f"{delta.seconds // 3600}H"
            else:
                freq = f"{delta.seconds // 60}T"
        freq = freq or "1D"

        # Crear portfolio con vectorbt
        # NOTA: price= define el precio de ejecución de órdenes
        #       open= se usa para stops intrabar
        portfolio = vbt.Portfolio.from_signals(
            close=prices["close"],
            price=exec_price,  # 🔥 Precio de ejecución de órdenes
            open=prices["open"] if "open" in prices.columns else None,
            high=prices["high"] if "high" in prices.columns else None,
            low=prices["low"] if "low" in prices.columns else None,
            entries=entries,
            exits=exits,
            init_cash=self.initial_capital,
            size=size_pct,
            size_type="percent",
            fees=self.costs.commission_pct,
            slippage=self.costs.slippage_pct,
            sl_stop=sl_stop,
            tp_stop=tp_stop,
            freq=freq,
        )

        # Extraer trades
        trades_df = self._extract_trades(portfolio)

        # Extraer equity curve
        equity = portfolio.value()

        # Calcular stats
        stats = self._calculate_stats(portfolio, trades_df)

        # Agregar info de SL/TP a stats
        stats["sl_pct"] = sl_pct
        stats["tp_pct"] = tp_pct

        return BacktestResult(
            trades=trades_df,
            equity=equity,
            stats=stats,
            portfolio=portfolio,
        )

    def _extract_trades(self, portfolio) -> pd.DataFrame:
        """Extrae tabla de trades del portfolio."""
        try:
            trades = portfolio.trades.records_readable
            if trades.empty:
                return pd.DataFrame(columns=[
                    "entry_time", "exit_time", "entry_price", "exit_price",
                    "size", "pnl", "return_pct", "duration"
                ])

            # Renombrar columnas para consistencia
            trades = trades.rename(columns={
                "Entry Timestamp": "entry_time",
                "Exit Timestamp": "exit_time",
                "Avg Entry Price": "entry_price",
                "Avg Exit Price": "exit_price",
                "Size": "size",
                "PnL": "pnl",
                "Return": "return_pct",
                "Duration": "duration",
            })

            # Seleccionar columnas relevantes
            cols = ["entry_time", "exit_time", "entry_price", "exit_price",
                    "size", "pnl", "return_pct"]
            available = [c for c in cols if c in trades.columns]
            return trades[available]

        except Exception:
            return pd.DataFrame()

    def _calculate_stats(self, portfolio, trades_df: pd.DataFrame) -> dict:
        """Calcula métricas completas del backtest."""
        stats = {}

        try:
            pf_stats = portfolio.stats()
            equity = portfolio.value()

            # Métricas básicas de vectorbt
            stats["total_return_pct"] = pf_stats.get("Total Return [%]", 0)
            stats["sharpe_ratio"] = pf_stats.get("Sharpe Ratio", 0)
            stats["max_drawdown_pct"] = pf_stats.get("Max Drawdown [%]", 0)
            stats["win_rate_pct"] = pf_stats.get("Win Rate [%]", 0)
            stats["profit_factor"] = pf_stats.get("Profit Factor", 0)
            stats["num_trades"] = pf_stats.get("Total Trades", 0)
            stats["avg_trade_pct"] = pf_stats.get("Avg Trade [%]", 0)
            
            # Métricas adicionales para PDF y UI
            stats["sortino_ratio"] = pf_stats.get("Sortino Ratio", 0)
            stats["calmar_ratio"] = pf_stats.get("Calmar Ratio", 0)
            stats["annual_return_pct"] = pf_stats.get("Annualized Return [%]", 0)
            stats["annual_volatility_pct"] = pf_stats.get("Annualized Volatility [%]", 0)
            stats["omega_ratio"] = pf_stats.get("Omega Ratio", 0)
            
            # Capital y equity
            stats["initial_capital"] = self.initial_capital
            stats["final_equity"] = float(equity.iloc[-1]) if len(equity) > 0 else self.initial_capital
            
            # Trades stats
            if not trades_df.empty and "pnl" in trades_df.columns:
                wins = trades_df[trades_df["pnl"] > 0]
                losses = trades_df[trades_df["pnl"] < 0]
                stats["avg_win"] = float(wins["pnl"].mean()) if len(wins) > 0 else 0
                stats["avg_loss"] = float(losses["pnl"].mean()) if len(losses) > 0 else 0
                stats["best_trade"] = float(trades_df["pnl"].max()) if len(trades_df) > 0 else 0
                stats["worst_trade"] = float(trades_df["pnl"].min()) if len(trades_df) > 0 else 0
            else:
                stats["avg_win"] = 0
                stats["avg_loss"] = 0
                stats["best_trade"] = 0
                stats["worst_trade"] = 0

            # Convertir NaN/inf a 0
            stats = {k: (0 if (pd.isna(v) or np.isinf(v)) else v) for k, v in stats.items()}

        except Exception:
            stats = {
                "total_return_pct": 0,
                "sharpe_ratio": 0,
                "max_drawdown_pct": 0,
                "win_rate_pct": 0,
                "profit_factor": 0,
                "num_trades": 0,
                "avg_trade_pct": 0,
                "sortino_ratio": 0,
                "calmar_ratio": 0,
                "annual_return_pct": 0,
                "annual_volatility_pct": 0,
                "omega_ratio": 0,
                "initial_capital": self.initial_capital,
                "final_equity": self.initial_capital,
                "avg_win": 0,
                "avg_loss": 0,
                "best_trade": 0,
                "worst_trade": 0,
            }

        return stats
````

## File: src/ml/features.py
````python
"""Feature engineering para modelos ML de trading - SIN LOOKAHEAD BIAS."""

import pandas as pd
import numpy as np
from typing import List

from ..strategy.indicators import sma, ema, rsi, atr, macd, bollinger_bands


class FeatureEngineer:
    """
    Genera features técnicos para modelos de ML.
    
    CRÍTICO: Todos los features en tiempo t usan SOLO información hasta t-1.
    Esto se logra calculando features normalmente y luego haciendo .shift(1)
    al DataFrame completo al final.
    
    Features incluidos:
    - Retornos (1, 5, 10, 20 períodos)
    - Medias móviles (ratios y cruces)
    - RSI
    - Volatilidad (ATR, std)
    - MACD
    - Bollinger Bands (posición)
    - Volume features
    """

    def __init__(
        self,
        sma_periods: List[int] = [5, 10, 20, 50],
        rsi_period: int = 14,
        atr_period: int = 14,
        lookback_periods: List[int] = [1, 5, 10, 20],
    ):
        """
        Args:
            sma_periods: Períodos para SMAs.
            rsi_period: Período para RSI.
            atr_period: Período para ATR.
            lookback_periods: Períodos para retornos históricos.
        """
        self.sma_periods = sma_periods
        self.rsi_period = rsi_period
        self.atr_period = atr_period
        self.lookback_periods = lookback_periods

    def create_features(self, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Genera DataFrame de features a partir de precios OHLCV.
        
        CRÍTICO: 
        1. Calculamos features con precios normales (sin shift)
        2. Al FINAL hacemos df.shift(1) para que feature[t] use datos hasta t-1
        
        Esto es correcto porque:
        - sma(close, 20) en día t usa close[t-19:t+1] (incluye t)
        - Luego .shift(1) mueve todo, entonces en día t del output 
          tendrás el SMA calculado hasta t-1 ✅
        
        Args:
            prices: DataFrame con columnas [open, high, low, close, volume].
            
        Returns:
            DataFrame con features calculados, mismo índice que prices.
        """
        df = pd.DataFrame(index=prices.index)
        
        # Usamos precios SIN shift - el shift se hace al final
        close = prices["close"]
        high = prices["high"]
        low = prices["low"]
        volume = prices["volume"] if "volume" in prices.columns else None

        # 1. Retornos históricos
        for period in self.lookback_periods:
            df[f"return_{period}d"] = close.pct_change(period)

        # 2. Medias móviles y ratios
        for period in self.sma_periods:
            ma = sma(close, period)
            df[f"sma_{period}"] = ma
            df[f"close_to_sma_{period}"] = close / ma - 1  # Distancia relativa

        # 3. Cruces de MAs (features binarios para cada par)
        if len(self.sma_periods) >= 2:
            fast_ma = sma(close, self.sma_periods[0])
            slow_ma = sma(close, self.sma_periods[-1])
            df["ma_cross"] = (fast_ma > slow_ma).astype(int)
            df["ma_diff"] = (fast_ma - slow_ma) / slow_ma

        # 4. RSI
        df["rsi"] = rsi(close, self.rsi_period)
        df["rsi_oversold"] = (df["rsi"] < 30).astype(int)
        df["rsi_overbought"] = (df["rsi"] > 70).astype(int)

        # 5. Volatilidad
        df["atr"] = atr(high, low, close, self.atr_period)
        df["atr_pct"] = df["atr"] / close  # ATR como % del precio
        
        for period in [5, 20]:
            df[f"volatility_{period}d"] = close.pct_change().rolling(period).std()

        # 6. MACD
        macd_df = macd(close)
        if macd_df is not None and not macd_df.empty:
            macd_cols = macd_df.columns.tolist()
            if len(macd_cols) >= 3:
                df["macd"] = macd_df.iloc[:, 0]
                df["macd_signal"] = macd_df.iloc[:, 2]
                df["macd_hist"] = macd_df.iloc[:, 1]

        # 7. Bollinger Bands
        bb_df = bollinger_bands(close)
        if bb_df is not None and not bb_df.empty:
            bb_cols = bb_df.columns.tolist()
            lower_col = [c for c in bb_cols if "BBL" in c]
            upper_col = [c for c in bb_cols if "BBU" in c]
            
            if lower_col and upper_col:
                bb_lower = bb_df[lower_col[0]]
                bb_upper = bb_df[upper_col[0]]
                bb_range = bb_upper - bb_lower
                df["bb_position"] = (close - bb_lower) / bb_range  # 0-1
                df["bb_width"] = bb_range / close

        # 8. Volume features
        if volume is not None:
            df["volume_sma_20"] = sma(volume, 20)
            df["volume_ratio"] = volume / df["volume_sma_20"]
            df["volume_change"] = volume.pct_change()

        # 9. Features de precio
        df["high_low_range"] = (high - low) / close
        df["close_position"] = (close - low) / (high - low)

        # 10. Momentum
        for period in [5, 10, 20]:
            df[f"momentum_{period}d"] = close / close.shift(period) - 1

        # 🔥 CRÍTICO: Shiftear TODO el DataFrame al final
        # Esto garantiza que feature[t] usa SOLO datos hasta t-1
        df = df.shift(1)
        
        # Limpiar infinitos que pueden generarse por división por cero
        df = df.replace([np.inf, -np.inf], np.nan)

        return df

    def create_target(
        self,
        prices: pd.DataFrame,
        horizon: int = 1,
        threshold: float = 0.0,
    ) -> pd.Series:
        """
        Crea variable target para clasificación.
        
        Target en día t predice si el precio subirá en los próximos 'horizon' días.
        
        Fórmula:
            target[t] = 1 si (precio[t+horizon] / precio[t]) - 1 > threshold
            
        Equivalente a:
            target[t] = 1 si precio[t+horizon] > precio[t] * (1 + threshold)
        
        Ejemplo con horizon=1, threshold=0.0:
            target[t] = 1 si precio[t+1] > precio[t]
        
        Args:
            prices: DataFrame con precios.
            horizon: Períodos hacia adelante para predecir.
            threshold: Umbral de retorno mínimo para considerar "subida".
            
        Returns:
            Series con 1 (subirá) o 0 (bajará/lateral).
        """
        close = prices["close"]
        future_price = close.shift(-horizon)
        future_return = (future_price / close) - 1
        
        target = (future_return > threshold).astype(int)
        
        return target

    def prepare_dataset(
        self,
        prices: pd.DataFrame,
        horizon: int = 1,
        threshold: float = 0.0,
        dropna: bool = True,
    ) -> tuple[pd.DataFrame, pd.Series]:
        """
        Prepara dataset completo SIN lookahead bias.
        
        IMPORTANTE: 
        - Features en día t usan datos hasta t-1 (por el shift al final)
        - Target en día t predice retorno de t a t+horizon
        - Modelo aprende: "dado lo que sabía ayer, ¿subirá hoy?"
        
        Args:
            prices: DataFrame con precios OHLCV.
            horizon: Períodos hacia adelante para target.
            threshold: Umbral para target.
            dropna: Si eliminar filas con NaN.
            
        Returns:
            Tuple de (features DataFrame, target Series).
        """
        features = self.create_features(prices)
        target = self.create_target(prices, horizon, threshold)

        if dropna:
            combined = pd.concat([features, target.rename("target")], axis=1)
            combined = combined.dropna()
            features = combined.drop("target", axis=1)
            target = combined["target"]

        return features, target
````

## File: src/ml/model.py
````python
"""Modelo ML y estrategia predictiva para trading."""

from dataclasses import dataclass, field
from typing import Any, Optional
import pickle
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler

from ..strategy.base import Strategy, SignalResult
from .features import FeatureEngineer


@dataclass
class MLModelMetrics:
    """Métricas de evaluación del modelo."""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    cv_scores: list = field(default_factory=list)
    feature_importance: dict = field(default_factory=dict)


class MLModel:
    """
    Wrapper para modelos de ML de clasificación.
    
    Soporta:
    - RandomForest
    - GradientBoosting (sklearn)
    - XGBoost
    - LightGBM
    """

    SUPPORTED_MODELS = {
        "random_forest": RandomForestClassifier,
        "gradient_boosting": GradientBoostingClassifier,
        "xgboost": XGBClassifier,
        "lightgbm": LGBMClassifier,
    }

    def __init__(
        self,
        model_type: str = "random_forest",
        model_params: Optional[dict] = None,
        scale_features: bool = True,
    ):
        """
        Args:
            model_type: Tipo de modelo ('random_forest', 'xgboost', etc).
            model_params: Parámetros para el modelo.
            scale_features: Si escalar features antes de entrenar.
        """
        if model_type not in self.SUPPORTED_MODELS:
            raise ValueError(f"Model type must be one of {list(self.SUPPORTED_MODELS.keys())}")

        self.model_type = model_type
        self.model_params = model_params or self._default_params(model_type)
        self.scale_features = scale_features

        self._model = None
        self._scaler = StandardScaler() if scale_features else None
        self._feature_names: list[str] = []
        self._is_trained = False

    def _default_params(self, model_type: str) -> dict:
        """Parámetros por defecto para cada tipo de modelo."""
        if model_type == "random_forest":
            return {
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 10,
                "min_samples_leaf": 5,
                "random_state": 42,
                "n_jobs": -1,
                "class_weight": "balanced",
            }
        elif model_type == "gradient_boosting":
            return {
                "n_estimators": 100,
                "max_depth": 5,
                "learning_rate": 0.1,
                "random_state": 42,
            }
        elif model_type == "xgboost":
            return {
                "n_estimators": 100,
                "max_depth": 6,
                "learning_rate": 0.1,
                "random_state": 42,
                "n_jobs": -1,
                # XGBoost specific for imbalanced data (optional)
                # "scale_pos_weight": 1, 
            }
        elif model_type == "lightgbm":
            return {
                "n_estimators": 100,
                "max_depth": -1,
                "num_leaves": 31,
                "learning_rate": 0.1,
                "random_state": 42,
                "n_jobs": -1,
                "class_weight": "balanced",
            }
        return {}

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
        cv_folds: int = 5,
    ) -> MLModelMetrics:
        """
        Entrena el modelo y retorna métricas.
        
        Usa TimeSeriesSplit para validación cruzada (evita data leakage temporal).
        
        Args:
            X: Features DataFrame.
            y: Target Series.
            test_size: Proporción para test set.
            cv_folds: Número de folds para cross-validation temporal.
            
        Returns:
            MLModelMetrics con resultados de evaluación.
        """
        from sklearn.model_selection import TimeSeriesSplit
        from sklearn.pipeline import Pipeline
        
        self._feature_names = list(X.columns)

        # Split temporal (train antes, test después)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False  # NO shuffle para series temporales
        )

        # Scale si es necesario
        if self.scale_features and self._scaler is not None:
            X_train_scaled = self._scaler.fit_transform(X_train)
            X_test_scaled = self._scaler.transform(X_test)
        else:
            X_train_scaled = X_train.values
            X_test_scaled = X_test.values

        # Crear y entrenar modelo
        model_class = self.SUPPORTED_MODELS[self.model_type]
        self._model = model_class(**self.model_params)
        self._model.fit(X_train_scaled, y_train)
        self._is_trained = True

        # Predicciones
        y_pred = self._model.predict(X_test_scaled)

        # Métricas
        metrics = MLModelMetrics(
            accuracy=accuracy_score(y_test, y_pred),
            precision=precision_score(y_test, y_pred, zero_division=0),
            recall=recall_score(y_test, y_pred, zero_division=0),
            f1=f1_score(y_test, y_pred, zero_division=0),
        )

        # Cross-validation con TimeSeriesSplit y Pipeline (evita data leakage)
        if cv_folds > 1 and len(X_train) >= cv_folds * 10:
            tscv = TimeSeriesSplit(n_splits=cv_folds)
            
            # Crear pipeline para que scaler se fit en cada fold
            steps = []
            if self.scale_features:
                steps.append(("scaler", StandardScaler()))
            steps.append(("model", model_class(**self.model_params)))
            
            pipe = Pipeline(steps)
            cv_scores = cross_val_score(pipe, X_train, y_train, cv=tscv)
            metrics.cv_scores = cv_scores.tolist()

        # Feature importance
        if hasattr(self._model, "feature_importances_"):
            importances = self._model.feature_importances_
            metrics.feature_importance = dict(zip(self._feature_names, importances))

        return metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Genera predicciones.
        
        Args:
            X: Features DataFrame.
            
        Returns:
            Array de predicciones (0 o 1).
        """
        if not self._is_trained:
            raise RuntimeError("Model must be trained before predicting")

        # Asegurar mismo orden de features
        X = X[self._feature_names]

        if self.scale_features and self._scaler is not None:
            X_scaled = self._scaler.transform(X)
        else:
            X_scaled = X.values

        return self._model.predict(X_scaled)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Genera probabilidades de predicción.
        
        Args:
            X: Features DataFrame.
            
        Returns:
            Array de probabilidades para clase positiva.
        """
        if not self._is_trained:
            raise RuntimeError("Model must be trained before predicting")

        X = X[self._feature_names]

        if self.scale_features and self._scaler is not None:
            X_scaled = self._scaler.transform(X)
        else:
            X_scaled = X.values

        return self._model.predict_proba(X_scaled)[:, 1]

    def save(self, path: Path | str) -> None:
        """Guarda modelo entrenado."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        state = {
            "model": self._model,
            "scaler": self._scaler,
            "feature_names": self._feature_names,
            "model_type": self.model_type,
            "model_params": self.model_params,
        }
        with open(path, "wb") as f:
            pickle.dump(state, f)

    @classmethod
    def load(cls, path: Path | str) -> "MLModel":
        """Carga modelo guardado."""
        with open(path, "rb") as f:
            state = pickle.load(f)
        
        instance = cls(
            model_type=state["model_type"],
            model_params=state["model_params"],
        )
        instance._model = state["model"]
        instance._scaler = state["scaler"]
        instance._feature_names = state["feature_names"]
        instance._is_trained = True
        return instance


class MLStrategy(Strategy):
    """
    Estrategia basada en modelo ML.
    
    Genera señales de entry cuando el modelo predice subida con
    probabilidad mayor al threshold, y exit cuando predice bajada.
    """

    def __init__(
        self,
        model: MLModel,
        feature_engineer: FeatureEngineer,
        entry_threshold: float = 0.6,
        exit_threshold: float = 0.4,
    ):
        """
        Args:
            model: Modelo ML entrenado.
            feature_engineer: FeatureEngineer para crear features.
            entry_threshold: Probabilidad mínima para entry.
            exit_threshold: Probabilidad máxima para exit.
        """
        self.model = model
        self.feature_engineer = feature_engineer
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold

    @property
    def name(self) -> str:
        return f"ML_{self.model.model_type}_thresh_{self.entry_threshold}"

    @property
    def params(self) -> dict:
        return {
            "model_type": self.model.model_type,
            "entry_threshold": self.entry_threshold,
            "exit_threshold": self.exit_threshold,
        }

    def generate_signals(self, prices: pd.DataFrame) -> SignalResult:
        """
        Genera señales basadas en predicciones del modelo.
        
        Args:
            prices: DataFrame OHLCV.
            
        Returns:
            SignalResult con entries/exits y features.
        """
        self.validate_prices(prices)

        # Generar features
        features = self.feature_engineer.create_features(prices)
        
        # Eliminar NaN (modelo no puede predecir con NaN)
        valid_mask = ~features.isna().any(axis=1)
        features_clean = features[valid_mask]

        # Inicializar señales como False
        entries = pd.Series(False, index=prices.index)
        exits = pd.Series(False, index=prices.index)

        if len(features_clean) > 0:
            # Predecir probabilidades
            proba = self.model.predict_proba(features_clean)
            proba_series = pd.Series(proba, index=features_clean.index)

            # Entry: probabilidad > entry_threshold
            # Exit: probabilidad < exit_threshold
            entries.loc[features_clean.index] = proba_series > self.entry_threshold
            exits.loc[features_clean.index] = proba_series < self.exit_threshold
            
            # 🔥 Limpiar conflictos: si entries y exits son True simultáneamente, priorizar entries
            conflict_mask = entries & exits
            exits = exits & ~conflict_mask

            # Agregar probabilidad a features
            features["ml_probability"] = np.nan
            features.loc[features_clean.index, "ml_probability"] = proba
        
        # Forzar dtype bool para evitar problemas con pandas
        entries = entries.astype(bool)
        exits = exits.astype(bool)

        signals = pd.DataFrame({"entries": entries, "exits": exits}, index=prices.index)

        return SignalResult(signals=signals, features=features)
````

## File: pyproject.toml
````toml
[project]
name = "portafolio-ml"
version = "0.1.0"
description = "Sistema de backtesting de trading con arquitectura modular"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "pandas-ta>=0.3.14b",
    "vectorbt>=0.26.0",
    "yfinance>=0.2.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "streamlit>=1.30.0",
    "pyarrow>=14.0.0",
    "plotly>=5.18.0",
    "openpyxl>=3.1.0",
    "scikit-learn>=1.4.0",
    "xgboost>=2.0.0",
    "lightgbm>=4.0.0",
    "optuna>=3.0.0",
    "reportlab>=4.4.7",
    "alpaca-trade-api>=3.2.0",
    "python-dotenv>=1.2.1",
    "fastapi>=0.128.0",
    "uvicorn>=0.40.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"

[tool.hatch.build.targets.wheel]
packages = ["src"]
````

## File: app/streamlit_app.py
````python
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
import pandas as pd
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
    
    # Premium Header
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">⚡ Trading Backtester Pro</h1>
        <p style="color: #94a3b8; font-size: 1.1rem; margin: 0;">
            Backtesting institucional • Machine Learning • Análisis avanzado
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats banner
    st.markdown("""
    <div class="premium-card" style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap; padding: 1rem 2rem;">
        <div class="stat-badge">🎯 Estrategias ML</div>
        <div class="stat-badge">📊 Walk-Forward Optimization</div>
        <div class="stat-badge">🔬 Monte Carlo Simulation</div>
        <div class="stat-badge">📈 Paper Trading</div>
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

        # Tabs para diferentes vistas
        tab_charts, tab_trades, tab_advanced = st.tabs([
            "📊 Gráficos", 
            "📋 Trades", 
            "🔬 Análisis Avanzado"
        ])
        
        with tab_charts:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Precio y Señales")
                display_price_chart(prices, signals)
            with col2:
                st.subheader("Equity vs Buy & Hold")
                display_equity_chart(backtest_result, prices=prices, initial_capital=initial_capital)
        
        with tab_trades:
            display_trades_table(backtest_result)
            
            # Botón para generar PDF Report
            st.divider()
            col_pdf, col_space = st.columns([1, 3])
            with col_pdf:
                # Generar PDF al hacer click
                try:
                    from src.evaluation.pdf_report import AlphaReportGenerator
                    from datetime import datetime
                    
                    pdf_gen = AlphaReportGenerator(
                        title="Alpha Strategy Report",
                        subtitle=f"{strategy_type} Strategy Analysis"
                    )
                    pdf_bytes = pdf_gen.generate(
                        result=backtest_result,
                        metadata=metadata,
                        strategy_name=strategy_type,
                        strategy_params={"ticker": ticker, "timeframe": timeframe}
                    )
                    
                    st.download_button(
                        label="📄 Descargar PDF Report",
                        data=pdf_bytes,
                        file_name=f"alpha_report_{ticker}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                except Exception as e:
                    st.error(f"Error generando PDF: {e}")
        
        with tab_advanced:
            st.markdown("### 🔬 Análisis de Robustez")
            
            adv_col1, adv_col2 = st.columns(2)
            
            with adv_col1:
                st.markdown("#### 🎲 Monte Carlo Simulation")
                with st.spinner("Ejecutando 1000 simulaciones..."):
                    from src.evaluation import MonteCarloSimulator
                    mc = MonteCarloSimulator(n_simulations=1000)
                    returns = backtest_result.equity.pct_change().dropna()
                    if len(returns) > 10:
                        mc_result = mc.simulate(returns)
                        
                        # Métricas MC
                        mc_cols = st.columns(3)
                        mc_cols[0].metric("VaR 95%", f"{mc_result.var_95*100:.1f}%")
                        mc_cols[1].metric("P(Ganancia)", f"{mc_result.prob_positive*100:.0f}%")
                        mc_cols[2].metric("Max DD Esperado", f"{mc_result.mean_max_drawdown*100:.1f}%")
                        
                        # Fan Chart
                        fig_mc = mc.create_fan_chart(mc_result)
                        st.plotly_chart(fig_mc, use_container_width=True)
                    else:
                        st.warning("Datos insuficientes para Monte Carlo")
            
            with adv_col2:
                st.markdown("#### 🔄 Walk-Forward Optimization")
                if strategy_type == "MA Cross":
                    with st.spinner("Ejecutando WFO (puede tardar)..."):
                        from src.optimization import WalkForwardOptimizer
                        wfo = WalkForwardOptimizer(n_splits=3, train_pct=0.7, n_trials=15)
                        try:
                            wfo_result = wfo.optimize(
                                prices=prices,
                                strategy_class=MACrossStrategy,
                                param_space={'fast_period': (5, 30), 'slow_period': (30, 100)}
                            )
                            
                            # Métricas WFO
                            wfo_cols = st.columns(3)
                            wfo_cols[0].metric("OOS Sharpe", f"{wfo_result.oos_sharpe:.2f}")
                            wfo_cols[1].metric("Estabilidad", f"{wfo_result.param_stability:.2f}")
                            wfo_cols[2].metric("Overfitting", wfo_result.summary['Overfitting Risk'])
                            
                            # Matriz de parámetros
                            st.markdown("**Parámetros por Fold:**")
                            st.dataframe(wfo_result.param_matrix, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error en WFO: {e}")
                else:
                    st.info("WFO disponible solo para estrategia MA Cross")
        
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
            features, target = fe.prepare_dataset(prices, horizon=1, dropna=True)
            
            # Validar que hay suficientes datos
            if len(features) < 100:
                st.error(f"❌ Datos insuficientes para ML: solo {len(features)} filas después de limpiar NaNs. Se necesitan al menos 100.")
                st.info("💡 Intenta con un ticker con más historial o usa timeframe diario (1d)")
                return None
            
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
                    
                    # Feature Importance Chart
                    if metrics.feature_importance:
                        import plotly.express as px
                        fi_df = pd.DataFrame({
                            'feature': list(metrics.feature_importance.keys()),
                            'importance': list(metrics.feature_importance.values())
                        }).sort_values('importance', ascending=True).tail(15)
                        
                        fig = px.bar(fi_df, x='importance', y='feature', 
                                     orientation='h', title='Top 15 Feature Importance')
                        fig.update_layout(template="plotly_dark", height=400,
                                          paper_bgcolor='rgba(0,0,0,0)', 
                                          plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig, use_container_width=True)

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

def display_metrics(result):
    """Muestra métricas principales en cards."""
    stats = result.stats

    # Primera fila: métricas principales
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
    
    # Segunda fila: métricas avanzadas
    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    
    with col_a:
        st.metric("Sortino", f"{stats.get('sortino_ratio', 0):.2f}")
    
    with col_b:
        st.metric("Calmar", f"{stats.get('calmar_ratio', 0):.2f}")
    
    with col_c:
        st.metric("Profit Factor", f"{stats.get('profit_factor', 0):.2f}")
    
    with col_d:
        st.metric("Avg Trade", f"{stats.get('avg_trade_pct', 0):.2f}%")
    
    with col_e:
        st.metric("Annual Return", f"{stats.get('annual_return_pct', 0):.1f}%")


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
````

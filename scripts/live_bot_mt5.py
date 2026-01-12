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

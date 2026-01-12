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

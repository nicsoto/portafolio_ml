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

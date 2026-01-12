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

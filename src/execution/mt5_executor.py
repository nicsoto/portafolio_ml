"""MT5 Socket Executor - Cliente Python para comunicarse con MT5 vía Socket.

Envía comandos JSON a un socket server corriendo en MT5 (SocketServer.mq5).
Funciona en Linux sin necesidad del paquete MetaTrader5.

Uso:
    executor = MT5Executor(host="127.0.0.1", port=5555)
    result = executor.buy("EURUSD", volume=0.1)
    print(result)
"""

import socket
import json
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


class MT5Executor:
    """
    Ejecutor de órdenes para MT5 vía Socket Bridge.
    
    Requiere que SocketServer.mq5 esté corriendo en MT5.
    Comunica vía JSON sobre TCP socket.
    """
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5555,
        timeout: float = 5.0,
        db_path: str = "data/mt5_orders.db",
    ):
        """
        Args:
            host: IP del servidor MT5 (localhost para Wine local).
            port: Puerto del SocketServer.mq5.
            timeout: Timeout para conexiones.
            db_path: Path para SQLite de logging.
        """
        self.host = host
        self.port = port
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
        Envía comando JSON al servidor MT5 y recibe respuesta.
        
        Args:
            command: Diccionario con el comando.
            
        Returns:
            Respuesta parseada como diccionario.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.connect((self.host, self.port))
                
                # Enviar comando como JSON
                json_cmd = json.dumps(command)
                sock.sendall(json_cmd.encode('utf-8'))
                
                # Recibir respuesta
                response = sock.recv(4096).decode('utf-8')
                
                return json.loads(response)
                
        except socket.timeout:
            return {"status": "error", "message": "Connection timeout"}
        except ConnectionRefusedError:
            return {"status": "error", "message": "Connection refused. Is MT5 running with SocketServer.mq5?"}
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Invalid JSON response: {e}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def ping(self) -> bool:
        """Verifica conexión con MT5."""
        result = self._send_command({"action": "ping"})
        return result.get("status") == "ok"
    
    def get_account(self) -> Dict[str, Any]:
        """
        Obtiene información de la cuenta MT5.
        
        Returns:
            Dict con balance, equity, margin, free_margin.
        """
        result = self._send_command({"action": "account"})
        
        if result.get("status") == "ok":
            return {
                "balance": result.get("balance", 0),
                "equity": result.get("equity", 0),
                "margin": result.get("margin", 0),
                "free_margin": result.get("free_margin", 0),
            }
        return {"error": result.get("message", "Unknown error")}
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Obtiene posiciones abiertas.
        
        Returns:
            Lista de posiciones.
        """
        result = self._send_command({"action": "positions"})
        
        if result.get("status") == "ok":
            return result.get("positions", [])
        return []
    
    def buy(self, symbol: str, volume: float = 0.01) -> MT5OrderLog:
        """
        Ejecuta orden de compra.
        
        Args:
            symbol: Par de divisas (ej: EURUSD).
            volume: Volumen en lotes.
            
        Returns:
            MT5OrderLog con resultado.
        """
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
        """
        Ejecuta orden de venta.
        
        Args:
            symbol: Par de divisas (ej: EURUSD).
            volume: Volumen en lotes.
            
        Returns:
            MT5OrderLog con resultado.
        """
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
        """
        Cierra posición abierta.
        
        Args:
            symbol: Par de divisas.
            
        Returns:
            MT5OrderLog con resultado.
        """
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
        """
        Interfaz compatible con AlpacaExecutor.
        
        Args:
            symbol: Par de divisas.
            qty: Volumen en lotes.
            side: "buy" o "sell".
            
        Returns:
            MT5OrderLog con resultado.
        """
        if side == "buy":
            return self.buy(symbol, volume=qty)
        else:
            return self.sell(symbol, volume=qty)
    
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
            SELECT * FROM mt5_order_logs 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    
    def is_connected(self) -> bool:
        """Alias para ping()."""
        return self.ping()

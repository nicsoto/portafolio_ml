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

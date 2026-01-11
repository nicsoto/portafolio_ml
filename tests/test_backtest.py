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

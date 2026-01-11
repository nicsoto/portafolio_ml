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

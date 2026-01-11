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

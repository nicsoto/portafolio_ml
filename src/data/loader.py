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

        return df

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

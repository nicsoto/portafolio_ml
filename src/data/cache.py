"""Sistema de caché para datos de precios usando Parquet."""

from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd


class CacheManager:
    """Gestiona el caché de datos de precios en formato Parquet."""

    def __init__(self, cache_dir: Path | str, max_age_hours: int = 24):
        """
        Args:
            cache_dir: Directorio donde se guardan los archivos parquet.
            max_age_hours: Edad máxima del caché en horas antes de considerarlo stale.
        """
        self.cache_dir = Path(cache_dir)
        self.max_age_hours = max_age_hours
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Crea el directorio de caché si no existe."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_path(self, ticker: str, timeframe: str) -> Path:
        """
        Genera el path del archivo de caché para un ticker/timeframe.

        Args:
            ticker: Símbolo del activo (e.g., 'SPY', 'AAPL').
            timeframe: Intervalo temporal (e.g., '1d', '1h', '15m').

        Returns:
            Path al archivo parquet.
        """
        # Normaliza ticker a mayúsculas
        ticker = ticker.upper().replace("/", "_").replace(".", "_")
        filename = f"{ticker}_{timeframe}.parquet"
        return self.cache_dir / filename

    def is_cache_valid(self, path: Path) -> bool:
        """
        Verifica si el archivo de caché existe y no está expirado.

        Args:
            path: Path al archivo de caché.

        Returns:
            True si el caché es válido, False si no existe o está expirado.
        """
        if not path.exists():
            return False

        # Verificar edad del archivo
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        age = datetime.now() - mtime
        return age < timedelta(hours=self.max_age_hours)

    def save_to_cache(self, df: pd.DataFrame, path: Path) -> None:
        """
        Guarda un DataFrame en caché como Parquet.

        Args:
            df: DataFrame con datos OHLCV.
            path: Path donde guardar el archivo.
        """
        # Asegurar que el directorio existe
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, engine="pyarrow")

    def load_from_cache(self, path: Path) -> pd.DataFrame:
        """
        Carga un DataFrame desde caché.

        Args:
            path: Path al archivo parquet.

        Returns:
            DataFrame con datos OHLCV.

        Raises:
            FileNotFoundError: Si el archivo no existe.
        """
        if not path.exists():
            raise FileNotFoundError(f"Cache file not found: {path}")
        return pd.read_parquet(path, engine="pyarrow")

    def clear_cache(self, ticker: str | None = None, timeframe: str | None = None) -> int:
        """
        Limpia archivos de caché.

        Args:
            ticker: Si se especifica, solo limpia archivos de ese ticker.
            timeframe: Si se especifica, solo limpia archivos de ese timeframe.

        Returns:
            Número de archivos eliminados.
        """
        count = 0
        for file in self.cache_dir.glob("*.parquet"):
            name = file.stem
            parts = name.rsplit("_", 1)
            if len(parts) != 2:
                continue

            file_ticker, file_tf = parts
            if ticker and file_ticker.upper() != ticker.upper():
                continue
            if timeframe and file_tf != timeframe:
                continue

            file.unlink()
            count += 1

        return count

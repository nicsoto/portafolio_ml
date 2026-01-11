"""Configuración del proyecto con Pydantic Settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración centralizada del proyecto.
    
    Los valores pueden sobreescribirse con variables de entorno
    o un archivo .env en la raíz del proyecto.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Data
    data_cache_dir: Path = Path("data/raw")
    cache_max_age_hours: int = 24

    # Backtest defaults
    initial_capital: float = 10_000.0
    default_risk_pct: float = 0.01

    # Costs
    commission_pct: float = 0.001
    slippage_pct: float = 0.0005

    # Experiments
    experiments_dir: Path = Path("data/experiments")

    def ensure_directories(self) -> None:
        """Crea directorios necesarios si no existen."""
        self.data_cache_dir.mkdir(parents=True, exist_ok=True)
        self.experiments_dir.mkdir(parents=True, exist_ok=True)


# Singleton para uso global
_settings: Settings | None = None


def get_settings() -> Settings:
    """Retorna instancia singleton de Settings."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

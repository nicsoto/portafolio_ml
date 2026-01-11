"""Tests para la capa de datos."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from src.data.cache import CacheManager
from src.data.schemas import OHLCVBar, DataMetadata


class TestCacheManager:
    """Tests para CacheManager."""

    def test_get_cache_path(self, tmp_path):
        """Verifica que genera paths correctos."""
        cache = CacheManager(tmp_path)

        path = cache.get_cache_path("SPY", "1d")
        assert path == tmp_path / "SPY_1d.parquet"

        # Normaliza a mayúsculas
        path = cache.get_cache_path("aapl", "1h")
        assert path == tmp_path / "AAPL_1h.parquet"

    def test_save_and_load(self, tmp_path):
        """Verifica guardar y cargar desde caché."""
        cache = CacheManager(tmp_path)

        # Crear DataFrame de prueba
        df = pd.DataFrame({
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.0, 102.0],
            "volume": [1000, 1100],
        })

        path = cache.get_cache_path("TEST", "1d")
        cache.save_to_cache(df, path)

        # Verify file exists
        assert path.exists()

        # Load and compare
        loaded = cache.load_from_cache(path)
        pd.testing.assert_frame_equal(df, loaded)

    def test_is_cache_valid_nonexistent(self, tmp_path):
        """Caché inexistente no es válido."""
        cache = CacheManager(tmp_path)
        path = cache.get_cache_path("NOEXIST", "1d")
        assert not cache.is_cache_valid(path)

    def test_is_cache_valid_fresh(self, tmp_path):
        """Caché recién creado es válido."""
        cache = CacheManager(tmp_path, max_age_hours=24)

        df = pd.DataFrame({"close": [100.0]})
        path = cache.get_cache_path("TEST", "1d")
        cache.save_to_cache(df, path)

        assert cache.is_cache_valid(path)


class TestOHLCVBar:
    """Tests para OHLCVBar schema."""

    def test_valid_bar(self):
        """Bar válida se crea correctamente."""
        bar = OHLCVBar(
            timestamp=datetime.now(),
            open=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=10000,
        )
        assert bar.close == 103.0

    def test_invalid_high_less_than_low(self):
        """High < low debe fallar."""
        with pytest.raises(ValueError, match="high.*must be >= low"):
            OHLCVBar(
                timestamp=datetime.now(),
                open=100.0,
                high=95.0,  # Invalid: less than low
                low=98.0,
                close=100.0,
                volume=10000,
            )

    def test_invalid_negative_price(self):
        """Precios negativos deben fallar."""
        with pytest.raises(ValueError):
            OHLCVBar(
                timestamp=datetime.now(),
                open=-100.0,  # Invalid
                high=105.0,
                low=98.0,
                close=103.0,
                volume=10000,
            )


class TestDataMetadata:
    """Tests para DataMetadata."""

    def test_create_metadata(self):
        """Metadata se crea correctamente."""
        meta = DataMetadata(
            ticker="SPY",
            timeframe="1d",
            source="yfinance",
            timezone="America/New_York",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            bar_count=252,
        )
        assert meta.ticker == "SPY"
        assert meta.bar_count == 252

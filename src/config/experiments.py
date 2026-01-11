"""Sistema de guardado de experimentos para reproducibilidad."""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ExperimentRun:
    """
    Representa una corrida de backtest guardada.
    
    Permite reproducibilidad: "este resultado lo saqué con X parámetros".
    """

    # Identificación
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = field(default_factory=datetime.now)

    # Configuración del experimento
    ticker: str = ""
    timeframe: str = ""
    strategy_name: str = ""
    strategy_params: dict = field(default_factory=dict)

    # Rango de datos
    start_date: str = ""
    end_date: str = ""

    # Costos
    commission_pct: float = 0.001
    slippage_pct: float = 0.0005
    initial_capital: float = 10_000.0

    # Resultados
    results: dict = field(default_factory=dict)

    # Metadata
    notes: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convierte a diccionario serializable."""
        data = asdict(self)
        # Convertir datetime a string
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentRun":
        """Crea instancia desde diccionario."""
        # Convertir string a datetime
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

    def save(self, directory: Path | str) -> Path:
        """
        Guarda experimento como JSON.
        
        Args:
            directory: Directorio donde guardar.
            
        Returns:
            Path al archivo guardado.
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        filename = f"{self.timestamp.strftime('%Y%m%d_%H%M%S')}_{self.id}.json"
        filepath = directory / filename

        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

        return filepath

    @classmethod
    def load(cls, filepath: Path | str) -> "ExperimentRun":
        """
        Carga experimento desde JSON.
        
        Args:
            filepath: Path al archivo JSON.
            
        Returns:
            Instancia de ExperimentRun.
        """
        with open(filepath) as f:
            data = json.load(f)
        return cls.from_dict(data)


class ExperimentTracker:
    """Gestiona múltiples experimentos."""

    def __init__(self, experiments_dir: Path | str):
        self.experiments_dir = Path(experiments_dir)
        self.experiments_dir.mkdir(parents=True, exist_ok=True)

    def save(self, run: ExperimentRun) -> Path:
        """Guarda un experimento."""
        return run.save(self.experiments_dir)

    def list_experiments(self) -> list[ExperimentRun]:
        """Lista todos los experimentos guardados."""
        experiments = []
        for filepath in sorted(self.experiments_dir.glob("*.json"), reverse=True):
            try:
                experiments.append(ExperimentRun.load(filepath))
            except Exception:
                continue
        return experiments

    def get_by_id(self, experiment_id: str) -> ExperimentRun | None:
        """Busca experimento por ID."""
        for filepath in self.experiments_dir.glob(f"*_{experiment_id}.json"):
            return ExperimentRun.load(filepath)
        return None

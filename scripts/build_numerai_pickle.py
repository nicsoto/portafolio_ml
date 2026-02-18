#!/usr/bin/env python
"""
Genera el pickle callable para subir a Numerai.

Usa una FUNCION con closure (no una clase) para evitar problemas
de serialización entre Python 3.13 y 3.12.

Versión simplificada:
- Sin scipy (usa numpy puro para ranking)
- Sin feature neutralization (reduce memoria y evita OOM en el contenedor)
- Patrón idéntico al hello_numerai.ipynb oficial

Uso:
    uv run python scripts/build_numerai_pickle.py
"""

import cloudpickle
from pathlib import Path


def main():
    local_path = Path("models/numerai_v3_ensemble.pkl")
    output_path = Path("models/numerai_v3_ensemble_callable.pkl")

    if not local_path.exists():
        print(f"❌ No se encontró {local_path}")
        print("   Entrena primero: uv run python scripts/numerai_train_v3.py --train")
        return

    # 1. Cargar el dict con los modelos entrenados
    print(f"📂 Cargando {local_path}...")
    with open(local_path, "rb") as f:
        result = cloudpickle.load(f)

    models = result["models"]
    feature_cols = list(result["feature_cols"])

    print(f"   Modelos: {len(models)}")
    print(f"   Features: {len(feature_cols)}")
    print(f"   Targets: {list(models.keys())}")

    # 2. Crear función predict con closure
    #    Patrón oficial hello_numerai.ipynb:
    #    - Función simple con closure
    #    - Sin scipy, sin neutralización
    #    - Ranking con numpy puro
    def predict(live_features, live_benchmark_models):
        import numpy as np
        import pandas as pd

        # Filtrar features disponibles
        available = [c for c in feature_cols if c in live_features.columns]
        X = live_features[available]

        # Ensemble: promedio de predicciones de cada modelo
        n = len(X)
        preds_sum = np.zeros(n)
        n_models = 0
        for tgt_name, mdl in models.items():
            raw = mdl.predict(X)
            # Rank normalize con numpy puro (sin scipy)
            order = raw.argsort().argsort()  # double argsort = rank
            ranked = (order + 0.5) / n
            preds_sum += ranked
            n_models += 1

        ensemble = preds_sum / n_models

        # Rank normalize final (asegurar rango [0, 1])
        order = ensemble.argsort().argsort()
        final = (order + 0.5) / n

        submission = pd.Series(final, index=live_features.index)
        return submission.to_frame("prediction")

    # 3. Serializar la función
    print(f"💾 Guardando callable en {output_path}...")
    with open(output_path, "wb") as f:
        cloudpickle.dump(predict, f)

    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"   Tamaño: {size_mb:.1f} MB")

    # 4. Verificar
    print("\n🧪 Verificando...")
    with open(output_path, "rb") as f:
        loaded = cloudpickle.load(f)

    print(f"   Tipo: {type(loaded)}")
    print(f"   Callable: {callable(loaded)}")

    import inspect
    sig = inspect.signature(loaded)
    print(f"   Parámetros: {list(sig.parameters.keys())}")
    print(f"   Num args: {len(sig.parameters)}")

    import pandas as pd
    live = pd.read_parquet("data/numerai/live.parquet")
    print(f"   Live shape: {live.shape}")

    out = loaded(live, pd.DataFrame())
    print(f"   ✅ Output shape: {out.shape}")
    print(f"   ✅ Columnas: {out.columns.tolist()}")
    print(f"   ✅ Tipo output: {type(out)}")
    print(f"   ✅ Rango: [{out['prediction'].min():.6f}, {out['prediction'].max():.6f}]")
    print(f"   ✅ NaN: {out['prediction'].isna().sum()}")
    assert type(out) is pd.DataFrame, "Output debe ser pd.DataFrame"
    assert out["prediction"].min() >= 0, "Mínimo debe ser >= 0"
    assert out["prediction"].max() <= 1, "Máximo debe ser <= 1"
    assert out["prediction"].isna().sum() == 0, "No debe haber NaN"
    assert out.iloc[:, 0].between(0, 1).all(), "Todos entre 0 y 1"

    print(f"\n🎉 Todas las validaciones pasaron.")
    print(f"   Sube este archivo a Numerai: {output_path}")


if __name__ == "__main__":
    main()

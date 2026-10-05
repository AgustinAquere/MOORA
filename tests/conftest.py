import sys
from pathlib import Path

import numpy as np
import pytest

# Permite ejecutar `pytest` desde la raíz del proyecto sin instalar el paquete.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def proveedores():
    """Ejemplo ilustrativo del TP (Sección 4.6, Tablas 2 y 3)."""
    return {
        "alternatives": ["Proveedor A", "Proveedor B", "Proveedor C", "Proveedor D"],
        "criteria": ["Precio", "Calidad", "Plazo", "Capacidad"],
        "matrix": np.array(
            [
                [120, 8, 10, 5000],
                [100, 7, 15, 4000],
                [135, 9, 7, 6000],
                [110, 6, 12, 4500],
            ],
            dtype=float,
        ),
        "weights": np.array([0.35, 0.30, 0.15, 0.20]),
        "is_benefit": np.array([False, True, False, True]),
        # Valores publicados en la Tabla 3 del informe (4 decimales).
        "y": [0.0142, -0.0289, 0.0516, -0.0337],
        "y_rank": [2, 3, 1, 4],
        "d": [0.0299, 0.0527, 0.0524, 0.0593],
        "d_rank": [1, 3, 2, 4],
    }


@pytest.fixture
def robots():
    """Actividad MOORA de la cátedra (García Alcaraz et al., 2007), resuelta en Excel."""
    return {
        "matrix": np.array(
            [
                [8500, 90, 1.4, 5.2, 7.0, 6.2],
                [4750, 85, 1.3, 5.4, 6.2, 5.8],
                [7200, 98, 1.6, 7.0, 5.6, 6.8],
                [4800, 95, 1.3, 6.4, 4.8, 6.6],
                [6300, 105, 0.9, 4.2, 6.4, 5.0],
                [9400, 93, 1.9, 8.4, 5.0, 7.0],
            ]
        ),
        # Los pesos publicados (0,17051; 0,17512; ...) son 37/217, 38/217, ...
        "weights": np.array([37, 38, 34, 36, 34, 38]) / 217,
        "is_benefit": np.array([False, True, True, True, True, True]),
        # Planilla de la actividad (5 decimales).
        "y": [0.24969, 0.26741, 0.28864, 0.27922, 0.22941, 0.28744],
        "y_rank": [5, 4, 1, 3, 6, 2],
        "d": [0.03706, 0.03251, 0.02421, 0.02678, 0.04551, 0.04595],
        "d_rank": [4, 3, 1, 2, 5, 6],
    }

"""Validación de las entradas del problema.

Las funciones devuelven un :class:`ValidationReport` con errores (impiden el
cálculo) y advertencias (el cálculo es posible, pero conviene revisar), con
mensajes en español pensados para mostrarse directamente en la interfaz.
"""

from __future__ import annotations

import math
import numbers
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

BENEFIT = "Beneficio"
COST = "Costo"
DIRECTIONS = (BENEFIT, COST)

_BENEFIT_ALIASES = {"beneficio", "max", "max.", "maximo", "máximo", "maximizar", "maximize", "benefit", "+", "mayor"}
_COST_ALIASES = {"costo", "coste", "min", "min.", "minimo", "mínimo", "minimizar", "minimize", "cost", "-", "menor"}

#: Cantidad máxima de celdas que se listan en un mensaje.
_MAX_LISTED = 8


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def merge(self, other: "ValidationReport") -> "ValidationReport":
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        return self


@dataclass(frozen=True)
class ProblemInputs:
    """Entradas ya validadas y listas para el motor de cálculo."""

    matrix: np.ndarray
    weights: np.ndarray
    is_benefit: np.ndarray
    alternatives: list[str]
    criteria: list[str]


# ---------------------------------------------------------------------------
# Conversión de valores
# ---------------------------------------------------------------------------

def is_blank(value) -> bool:
    if value is None or value is pd.NA or value is pd.NaT:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def parse_number(value) -> float | None:
    """Convierte un valor de celda a ``float``.

    Acepta coma o punto decimal, separadores de miles y porcentajes
    (``"35%"`` → 0.35). Devuelve ``None`` si la celda está vacía.

    Raises:
        ValueError: si el valor no es numérico.
    """
    if is_blank(value):
        return None
    if isinstance(value, bool):
        raise ValueError(f"'{value}' no es un número.")
    if isinstance(value, numbers.Real):
        f = float(value)
        if math.isnan(f):
            return None
        if math.isinf(f):
            raise ValueError("Valor infinito.")
        return f
    text = str(value).strip().replace(" ", "").replace(" ", "")
    percent = text.endswith("%")
    if percent:
        text = text[:-1]
    if "," in text and "." in text:
        # El separador que aparece último es el decimal: "1.234,5" o "1,234.5".
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif text.count(",") == 1:
        text = text.replace(",", ".")
    try:
        f = float(text)
    except ValueError:
        raise ValueError(f"'{value}' no es un número.") from None
    if not math.isfinite(f):
        raise ValueError(f"'{value}' no es un número finito.")
    return f / 100 if percent else f


def parse_direction(value) -> bool | None:
    """``True`` si es beneficio, ``False`` si es costo, ``None`` si no se reconoce."""
    if is_blank(value):
        return None
    key = str(value).strip().lower()
    if key in _BENEFIT_ALIASES:
        return True
    if key in _COST_ALIASES:
        return False
    return None


def unique_labels(names, prefix: str) -> list[str]:
    """Nombres no vacíos y sin repetir, para usar como encabezados de tabla."""
    out: list[str] = []
    seen: set[str] = set()
    for i, name in enumerate(names):
        label = "" if is_blank(name) else str(name).strip()
        label = label or f"{prefix}{i + 1}"
        base, k = label, 2
        while label in seen:
            label = f"{base} ({k})"
            k += 1
        seen.add(label)
        out.append(label)
    return out


def _listing(items: list[str]) -> str:
    shown = ", ".join(items[:_MAX_LISTED])
    if len(items) > _MAX_LISTED:
        shown += f" y {len(items) - _MAX_LISTED} más"
    return shown


# ---------------------------------------------------------------------------
# Validaciones
# ---------------------------------------------------------------------------

def validate_dimensions(m: int, n: int) -> ValidationReport:
    report = ValidationReport()
    if m < 1:
        report.errors.append("El problema debe tener al menos 1 alternativa (m ≥ 1).")
    if n < 1:
        report.errors.append("El problema debe tener al menos 1 criterio (n ≥ 1).")
    if m == 1:
        report.warnings.append("Hay una sola alternativa: el ranking es trivial y la correlación de Spearman no está definida.")
    if n == 1:
        report.warnings.append("Hay un solo criterio: el problema es unicriterio y no admite análisis de sensibilidad de pesos.")
    return report


def validate_names(names, kind: str) -> ValidationReport:
    """Verifica que no haya nombres vacíos ni repetidos. ``kind``: "alternativa" o "criterio"."""
    report = ValidationReport()
    cleaned = ["" if is_blank(v) else str(v).strip() for v in names]
    empty = [str(i + 1) for i, v in enumerate(cleaned) if not v]
    if empty:
        report.errors.append(f"Hay {kind}s sin nombre (posición {_listing(empty)}).")
    seen, dup = set(), []
    for v in cleaned:
        if v and v in seen and v not in dup:
            dup.append(v)
        seen.add(v)
    if dup:
        report.errors.append(f"Hay nombres de {kind} repetidos: {_listing(dup)}.")
    return report


def coerce_matrix(values) -> tuple[np.ndarray, list[tuple[int, int]], list[tuple[int, int, object]]]:
    """Convierte la tabla en floats.

    Returns:
        (matriz con NaN en celdas inválidas, celdas vacías, celdas no numéricas con su valor).
    """
    raw = values.to_numpy(dtype=object) if isinstance(values, pd.DataFrame) else np.asarray(values, dtype=object)
    if raw.ndim != 2:
        raw = raw.reshape(raw.shape[0] if raw.ndim else 0, -1)
    out = np.full(raw.shape, np.nan)
    empty, invalid = [], []
    for (i, j), v in np.ndenumerate(raw):
        try:
            f = parse_number(v)
        except ValueError:
            invalid.append((i, j, v))
            continue
        if f is None:
            empty.append((i, j))
        else:
            out[i, j] = f
    return out, empty, invalid


def validate_matrix(values, alternatives, criteria) -> tuple[ValidationReport, np.ndarray | None]:
    """Valida la matriz de decisión. Devuelve la matriz numérica si no hay errores."""
    alternatives, criteria = list(alternatives), list(criteria)
    report = validate_dimensions(len(alternatives), len(criteria))
    if not report.ok:
        return report, None
    x, empty, invalid = coerce_matrix(values)
    if x.shape != (len(alternatives), len(criteria)):
        report.errors.append(
            f"La matriz tiene {x.shape[0]}×{x.shape[1]} celdas, pero hay "
            f"{len(alternatives)} alternativas y {len(criteria)} criterios."
        )
        return report, None

    def cell(i, j):
        return f"{alternatives[i]} / {criteria[j]}"

    if empty:
        report.errors.append(f"Hay {len(empty)} celda(s) vacía(s): {_listing([cell(i, j) for i, j in empty])}.")
    if invalid:
        report.errors.append(
            f"Hay {len(invalid)} valor(es) no numérico(s): "
            f"{_listing([f'{cell(i, j)} = «{v}»' for i, j, v in invalid])}."
        )

    complete = np.all(np.isfinite(x), axis=0)
    zero_cols = [criteria[j] for j in range(x.shape[1]) if complete[j] and np.all(x[:, j] == 0)]
    if zero_cols:
        report.errors.append(
            f"La suma de cuadrados es 0 en {_listing(zero_cols)}: todos los valores son 0 y la "
            "normalización vectorial dividiría por cero. Corrija los datos o elimine el criterio."
        )
    neg_cols = [criteria[j] for j in range(x.shape[1]) if np.any(x[:, j] < 0)]
    if neg_cols:
        report.warnings.append(
            f"Hay valores negativos en {_listing(neg_cols)}. La normalización vectorial los admite, pero "
            "conviene verificar su interpretación; el método de entropía no puede usarse con ellos."
        )
    if x.shape[0] > 1:
        const_cols = [
            criteria[j]
            for j in range(x.shape[1])
            if complete[j] and criteria[j] not in zero_cols and np.ptp(x[:, j]) == 0
        ]
        if const_cols:
            report.warnings.append(
                f"El criterio {_listing(const_cols)} tiene el mismo valor en todas las alternativas: no discrimina."
            )
    return report, (x if report.ok else None)


def validate_directions(directions, criteria) -> tuple[ValidationReport, np.ndarray | None]:
    criteria = list(criteria)
    report = ValidationReport()
    directions = list(directions)
    if len(directions) != len(criteria):
        report.errors.append(f"Se esperaban {len(criteria)} sentidos y hay {len(directions)}.")
        return report, None
    parsed = [parse_direction(d) for d in directions]
    missing = [criteria[j] for j, p in enumerate(parsed) if p is None]
    if missing:
        report.errors.append(f"Falta indicar el sentido (Beneficio / Costo) de: {_listing(missing)}.")
        return report, None
    return report, np.array(parsed, dtype=bool)


def validate_weights(weights, criteria) -> tuple[ValidationReport, np.ndarray | None]:
    """Valida los pesos. Si no suman 1 se normalizan y se emite una advertencia."""
    criteria = list(criteria)
    report = ValidationReport()
    weights = list(weights)
    if len(weights) != len(criteria):
        report.errors.append(f"Se esperaban {len(criteria)} pesos y hay {len(weights)}.")
        return report, None
    parsed: list[float | None] = []
    bad: list[str] = []
    for j, v in enumerate(weights):
        try:
            parsed.append(parse_number(v))
        except ValueError:
            parsed.append(None)
            bad.append(criteria[j])
    empty = [criteria[j] for j, p in enumerate(parsed) if p is None and criteria[j] not in bad]
    if empty:
        report.errors.append(f"Falta el peso de: {_listing(empty)}.")
    if bad:
        report.errors.append(f"Peso no numérico en: {_listing(bad)}.")
    if not report.ok:
        return report, None
    w = np.array(parsed, dtype=float)
    neg = [criteria[j] for j in np.flatnonzero(w < 0)]
    if neg:
        report.errors.append(f"Los pesos no pueden ser negativos ({_listing(neg)}).")
        return report, None
    total = w.sum()
    if total <= 0:
        report.errors.append("La suma de los pesos es 0: asigne un peso positivo a al menos un criterio.")
        return report, None
    if abs(total - 1.0) > 1e-4:
        report.warnings.append(
            f"Los pesos suman {total:.4f} (≠ 1): se normalizaron automáticamente dividiendo cada uno por la suma."
        )
    zero = [criteria[j] for j in np.flatnonzero(w == 0)]
    if zero:
        report.warnings.append(f"Los criterios {_listing(zero)} tienen peso 0 y no influyen en el resultado.")
    return report, w / total


def validate_problem(alternatives, criteria, values, directions, weights) -> tuple[ValidationReport, ProblemInputs | None]:
    """Validación completa del problema. Devuelve las entradas listas para ``engine.solve``."""
    alternatives = ["" if is_blank(a) else str(a).strip() for a in alternatives]
    criteria = ["" if is_blank(c) else str(c).strip() for c in criteria]
    report = ValidationReport()
    report.merge(validate_names(alternatives, "alternativa"))
    report.merge(validate_names(criteria, "criterio"))
    labels_a = unique_labels(alternatives, "A")
    labels_c = unique_labels(criteria, "C")

    mat_report, x = validate_matrix(values, labels_a, labels_c)
    report.merge(mat_report)
    if len(labels_c) < 1:
        return report, None
    dir_report, benefit = validate_directions(directions, labels_c)
    report.merge(dir_report)
    w_report, w = validate_weights(weights, labels_c)
    report.merge(w_report)
    if not report.ok:
        return report, None
    return report, ProblemInputs(matrix=x, weights=w, is_benefit=benefit, alternatives=labels_a, criteria=labels_c)

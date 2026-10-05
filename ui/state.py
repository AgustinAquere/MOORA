"""Estado de la sesión de Streamlit y cálculo del análisis completo.

El problema se guarda en ``st.session_state["problem"]``. Las tablas editables
(``st.data_editor``) reciben una "foto" del problema y una clave con un número
de versión (``nonce``): cada vez que el problema cambia desde afuera del editor
(cargar un ejemplo, importar, cambiar de paso, redimensionar) se incrementa la
versión y el editor se vuelve a crear con los datos actuales.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import streamlit as st

from data_io.examples import DEFAULT_EXAMPLE, EXAMPLES
from data_io.serializers import ImportedProblem
from data_io.validators import (
    BENEFIT,
    ProblemInputs,
    ValidationReport,
    is_blank,
    unique_labels,
    validate_matrix,
    validate_problem,
)
from engine import (
    EntropyResult,
    MooraResult,
    RankingComparison,
    compare_rankings,
    entropy_analysis,
    equal_weights,
    solve,
)

STEPS = [
    "1 · Datos del problema",
    "2 · Criterios y pesos",
    "3 · Resultados paso a paso",
    "4 · Comparación y gráficos",
    "5 · Análisis de sensibilidad",
    "6 · Exportación",
]

DIRECT, EQUAL, ENTROPY = "Asignación directa", "Pesos iguales (1/n)", "Entropía (objetivo)"
WEIGHT_METHODS = (DIRECT, EQUAL, ENTROPY)

ALT_COL = "Alternativa"


@dataclass
class Problem:
    name: str
    alternatives: list[str]
    criteria: list[str]
    values: np.ndarray  # m×n float, NaN = celda vacía
    directions: list[str]
    weights: list[float | None]  # pesos de la asignación directa
    weight_method: str = DIRECT

    @property
    def m(self) -> int:
        return len(self.alternatives)

    @property
    def n(self) -> int:
        return len(self.criteria)


@dataclass
class Analysis:
    report: ValidationReport
    weights_used: np.ndarray | None = None
    entropy: EntropyResult | None = None
    inputs: ProblemInputs | None = None
    result: MooraResult | None = None
    comparison: RankingComparison | None = None
    weight_messages: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.result is not None


# ---------------------------------------------------------------------------
# Inicialización y acceso
# ---------------------------------------------------------------------------

def init_state() -> None:
    ss = st.session_state
    ss.setdefault("nonce", 0)
    ss.setdefault("step", STEPS[0])
    ss.setdefault("decimals", 4)
    if "problem" not in ss:
        set_problem(problem_from_example(DEFAULT_EXAMPLE))


def get_problem() -> Problem:
    return st.session_state["problem"]


def set_problem(p: Problem) -> None:
    ss = st.session_state
    ss["problem"] = p
    ss["problem_name_input"] = p.name
    ss["dim_m"] = max(p.m, 1)
    ss["dim_n"] = max(p.n, 1)
    ss["weight_method_input"] = p.weight_method
    ss.pop("sensitivity_cfg", None)
    refresh_editors()


def refresh_editors() -> None:
    """Recrea las tablas editables a partir del problema actual."""
    ss = st.session_state
    p = get_problem()
    ss["nonce"] = ss.get("nonce", 0) + 1
    ss["matrix_snapshot"] = matrix_editor_frame(p)
    ss["names_snapshot"] = names_editor_frame(p)
    ss["criteria_snapshot"] = criteria_editor_frame(p)


def go_to(step: str) -> None:
    st.session_state["step"] = step
    refresh_editors()


# ---------------------------------------------------------------------------
# Construcción de problemas
# ---------------------------------------------------------------------------

def problem_from_example(name: str) -> Problem:
    ex = EXAMPLES[name]
    return Problem(
        name=ex.name,
        alternatives=list(ex.alternatives),
        criteria=list(ex.criteria),
        values=np.array(ex.values, dtype=float),
        directions=list(ex.directions),
        weights=list(ex.weights),
    )


def problem_from_import(imp: ImportedProblem, name: str) -> Problem:
    n = len(imp.criteria)
    return Problem(
        name=name,
        alternatives=list(imp.alternatives),
        criteria=list(imp.criteria),
        values=imp.values.to_numpy(dtype=float),
        directions=list(imp.directions) if imp.directions else [BENEFIT] * n,
        weights=list(imp.weights) if imp.weights else [1.0 / n] * n,
    )


def empty_problem(m: int, n: int, name: str = "Nuevo problema") -> Problem:
    return Problem(
        name=name,
        alternatives=[f"A{i + 1}" for i in range(m)],
        criteria=[f"C{j + 1}" for j in range(n)],
        values=np.full((m, n), np.nan),
        directions=[BENEFIT] * n,
        weights=[round(1.0 / n, 6)] * n,
    )


def resized(p: Problem, m: int, n: int) -> Problem:
    """Copia del problema con nueva dimensión, conservando los datos que entran."""
    values = np.full((m, n), np.nan)
    mm, nn = min(m, p.m), min(n, p.n)
    values[:mm, :nn] = p.values[:mm, :nn]
    alts = p.alternatives[:m] + [f"A{i + 1}" for i in range(p.m, m)]
    crits = p.criteria[:n] + [f"C{j + 1}" for j in range(p.n, n)]
    new_w = 1.0 / n
    return Problem(
        name=p.name,
        alternatives=alts,
        criteria=crits,
        values=values,
        directions=p.directions[:n] + [BENEFIT] * max(0, n - p.n),
        weights=p.weights[:n] + [round(new_w, 6)] * max(0, n - p.n),
        weight_method=p.weight_method,
    )


# ---------------------------------------------------------------------------
# Tablas editables
# ---------------------------------------------------------------------------

def matrix_editor_frame(p: Problem) -> pd.DataFrame:
    df = pd.DataFrame(p.values, columns=unique_labels(p.criteria, "C"))
    df.insert(0, ALT_COL, pd.Series(p.alternatives, dtype=object))
    return df


def names_column(j: int) -> str:
    return f"Criterio {j + 1}"


def names_editor_frame(p: Problem) -> pd.DataFrame:
    """Una sola fila con el nombre de cada criterio (se edita en el paso 1)."""
    return pd.DataFrame([p.criteria], columns=[names_column(j) for j in range(p.n)], dtype=object)


def rename_criteria(edited_rows: dict) -> bool:
    """Aplica los cambios de la fila de nombres; devuelve True si cambió algún nombre."""
    p = get_problem()
    changed = False
    for changes in edited_rows.values():
        for col, value in changes.items():
            j = int(str(col).rsplit(" ", 1)[-1]) - 1
            if 0 <= j < p.n:
                new = _text(value)
                changed = changed or new != p.criteria[j]
                p.criteria[j] = new
    return changed


def criteria_editor_frame(p: Problem) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Criterio": pd.Series(p.criteria, dtype=object),
            "Sentido": pd.Series(p.directions, dtype=object),
            "Peso": pd.Series([np.nan if w is None else w for w in p.weights], dtype=float),
        }
    )


def _text(value) -> str:
    return "" if is_blank(value) else str(value).strip()


def apply_matrix_edit(p: Problem, edited: pd.DataFrame) -> None:
    p.alternatives = [_text(v) for v in edited[ALT_COL].tolist()]
    values = edited.drop(columns=[ALT_COL]).apply(pd.to_numeric, errors="coerce")
    p.values = values.to_numpy(dtype=float)


def apply_criteria_edit(p: Problem, edited: pd.DataFrame, include_weights: bool) -> None:
    p.criteria = [_text(v) for v in edited["Criterio"].tolist()]
    p.directions = [_text(v) for v in edited["Sentido"].tolist()]
    if include_weights:
        p.weights = [None if is_blank(v) else float(v) for v in edited["Peso"].tolist()]


# ---------------------------------------------------------------------------
# Análisis completo (validación + cálculo)
# ---------------------------------------------------------------------------

def analyze(p: Problem) -> Analysis:
    """Valida el problema, resuelve los pesos según el método elegido y calcula MOORA."""
    report = ValidationReport()
    analysis = Analysis(report=report)
    labels_a = unique_labels(p.alternatives, "A")
    labels_c = unique_labels(p.criteria, "C")

    weights = p.weights
    if p.weight_method == EQUAL and p.n >= 1:
        weights = equal_weights(p.n).tolist()
    elif p.weight_method == ENTROPY and p.n >= 1:
        _, x = validate_matrix(p.values, labels_a, labels_c)
        if x is None:
            weights = equal_weights(p.n).tolist()  # los errores de la matriz ya se informan abajo
            analysis.weight_messages.append("Los pesos por entropía se calcularán cuando la matriz sea válida.")
        else:
            try:
                analysis.entropy = entropy_analysis(x)
                weights = analysis.entropy.weights.tolist()
            except ValueError as exc:
                report.errors.append(f"Método de entropía: {exc}")
                weights = equal_weights(p.n).tolist()

    val_report, inputs = validate_problem(p.alternatives, p.criteria, p.values, p.directions, weights)
    report.merge(val_report)
    analysis.inputs = inputs if report.ok else None
    if inputs is not None:
        analysis.weights_used = inputs.weights
    if analysis.inputs is None:
        return analysis
    try:
        analysis.result = solve(inputs.matrix, inputs.weights, inputs.is_benefit, inputs.alternatives, inputs.criteria)
    except ValueError as exc:  # red de seguridad: la validación debería haberlo evitado
        report.errors.append(str(exc))
        return analysis
    analysis.comparison = compare_rankings(analysis.result)
    return analysis

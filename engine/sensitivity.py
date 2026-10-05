"""Análisis de sensibilidad de MOORA respecto del peso de un criterio.

Se varía el peso ``w_k`` de un criterio dentro de un rango y los demás pesos se
renormalizan proporcionalmente para que la suma siga siendo 1:

    w_j' = w_j · (1 - w_k') / (1 - w_k)      para j ≠ k

Para cada valor de ``w_k'`` se recalculan ambos rankings. Los puntos donde
cambia la mejor alternativa se detectan sobre la grilla y luego se refinan por
bisección, de modo que el valor informado es exacto hasta ~1e-10.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .moora import (
    RATIO_SYSTEM,
    REFERENCE_POINT,
    as_decision_matrix,
    as_direction_vector,
    rank,
    reference_deviations,
    reference_point,
    vector_normalize,
)
from .weights import normalize_weights

#: Si la suma de los demás pesos es menor que esto, se reparten en partes iguales.
_REST_EPS = 1e-12
_BISECTION_STEPS = 50


def redistribute_weights(weights, index: int, new_weight: float) -> np.ndarray:
    """Asigna ``new_weight`` al criterio ``index`` y renormaliza los demás.

    Los demás pesos conservan sus proporciones relativas. Si el criterio tenía
    todo el peso (``w_k = 1``), el resto ``1 - w_k'`` se reparte en partes iguales.
    """
    w = normalize_weights(weights)
    n = w.size
    if not 0 <= index < n:
        raise ValueError(f"Índice de criterio fuera de rango: {index}.")
    new_weight = float(new_weight)
    if not 0.0 <= new_weight <= 1.0:
        raise ValueError("El nuevo peso debe estar entre 0 y 1.")
    if n == 1:
        if abs(new_weight - 1.0) > 1e-9:
            raise ValueError("Con un único criterio su peso es necesariamente 1.")
        return np.ones(1)
    rest = 1.0 - w[index]
    if rest <= _REST_EPS:
        out = np.full(n, (1.0 - new_weight) / (n - 1))
    else:
        out = w * (1.0 - new_weight) / rest
    out[index] = new_weight
    return out


def _scores(normalized, sign, deviations, weight_rows):
    """Puntajes y_i y d_i para cada fila de pesos (G×n) → (G×m, G×m)."""
    y = weight_rows @ (normalized * sign).T
    d = (weight_rows[:, None, :] * deviations[None, :, :]).max(axis=2)
    return y, d


@dataclass(frozen=True)
class SensitivityResult:
    alternatives: list[str]
    criteria: list[str]
    criterion_index: int
    base_weight: float
    grid: np.ndarray
    weights_grid: np.ndarray
    ratio_scores: np.ndarray
    ratio_ranks: np.ndarray
    reference_scores: np.ndarray
    reference_ranks: np.ndarray
    change_points: pd.DataFrame

    @property
    def criterion(self) -> str:
        return self.criteria[self.criterion_index]

    def _winner_names(self, ranks_row) -> str:
        return " / ".join(self.alternatives[i] for i in np.flatnonzero(ranks_row == 1))

    def long_frame(self) -> pd.DataFrame:
        """Formato largo: una fila por (peso, método, alternativa)."""
        frames = []
        for method, scores, ranks in (
            (RATIO_SYSTEM, self.ratio_scores, self.ratio_ranks),
            (REFERENCE_POINT, self.reference_scores, self.reference_ranks),
        ):
            g, m = scores.shape
            frames.append(
                pd.DataFrame(
                    {
                        f"Peso {self.criterion}": np.repeat(self.grid, m),
                        "Método": method,
                        "Alternativa": np.tile(self.alternatives, g),
                        "Puntaje": scores.ravel(),
                        "Posición": ranks.ravel(),
                    }
                )
            )
        return pd.concat(frames, ignore_index=True)

    def winners_frame(self) -> pd.DataFrame:
        """Mejor alternativa de cada método para cada valor de la grilla."""
        df = pd.DataFrame(self.weights_grid, columns=[f"w {c}" for c in self.criteria])
        df.insert(0, f"Peso {self.criterion}", self.grid)
        df[f"Mejor ({RATIO_SYSTEM})"] = [self._winner_names(r) for r in self.ratio_ranks]
        df[f"Mejor ({REFERENCE_POINT})"] = [self._winner_names(r) for r in self.reference_ranks]
        return df

    def stability_interval(self, method: str) -> tuple[float, float] | None:
        """Intervalo de ``w_k`` (dentro del rango analizado) en el que se mantiene
        la mejor alternativa del peso actual. ``None`` si el peso actual está fuera
        del rango analizado."""
        lo, hi = float(self.grid[0]), float(self.grid[-1])
        if not lo - 1e-12 <= self.base_weight <= hi + 1e-12:
            return None
        cps = self.change_points
        if not cps.empty:
            pts = cps.loc[cps["Método"] == method, "Peso"].to_numpy(dtype=float)
            below = pts[pts <= self.base_weight + 1e-12]
            above = pts[pts > self.base_weight + 1e-12]
            if below.size:
                lo = float(below.max())
            if above.size:
                hi = float(above.min())
        return lo, hi


def sensitivity_analysis(
    matrix,
    weights,
    is_benefit,
    criterion_index: int,
    w_min: float = 0.0,
    w_max: float = 1.0,
    steps: int = 101,
    alternatives=None,
    criteria=None,
) -> SensitivityResult:
    """Recalcula ambos rankings variando el peso del criterio ``criterion_index``.

    Args:
        w_min, w_max: rango del peso analizado (0 ≤ w_min < w_max ≤ 1).
        steps: cantidad de puntos de la grilla (≥ 2). El peso actual se agrega a
            la grilla si cae dentro del rango.
    """
    x = as_decision_matrix(matrix)
    m, n = x.shape
    if n < 2:
        raise ValueError("El análisis de sensibilidad requiere al menos 2 criterios.")
    benefit = as_direction_vector(is_benefit, n)
    w = normalize_weights(weights)
    if w.size != n:
        raise ValueError(f"Se esperaban {n} pesos y se recibieron {w.size}.")
    if not 0 <= criterion_index < n:
        raise ValueError(f"Índice de criterio fuera de rango: {criterion_index}.")
    if not (0.0 <= w_min < w_max <= 1.0):
        raise ValueError("El rango de pesos debe cumplir 0 ≤ mínimo < máximo ≤ 1.")
    steps = int(steps)
    if steps < 2:
        raise ValueError("La grilla debe tener al menos 2 puntos.")

    alts = list(alternatives) if alternatives is not None else [f"A{i + 1}" for i in range(m)]
    crits = list(criteria) if criteria is not None else [f"C{j + 1}" for j in range(n)]

    normalized = vector_normalize(x)
    sign = np.where(benefit, 1.0, -1.0)
    deviations = reference_deviations(normalized, reference_point(normalized, benefit))
    base = float(w[criterion_index])

    grid = np.linspace(w_min, w_max, steps)
    if w_min <= base <= w_max:
        grid = np.unique(np.append(grid, base))
    weight_rows = np.array([redistribute_weights(w, criterion_index, t) for t in grid])
    y, d = _scores(normalized, sign, deviations, weight_rows)
    y_ranks = np.array([rank(row, higher_is_better=True) for row in y])
    d_ranks = np.array([rank(row, higher_is_better=False) for row in d])

    def winners_at(t: float, method: str) -> tuple[int, ...]:
        row = redistribute_weights(w, criterion_index, t)[None, :]
        yy, dd = _scores(normalized, sign, deviations, row)
        if method == RATIO_SYSTEM:
            r = rank(yy[0], higher_is_better=True)
        else:
            r = rank(dd[0], higher_is_better=False)
        return tuple(np.flatnonzero(r == 1))

    def names(key: tuple[int, ...]) -> str:
        return " / ".join(alts[i] for i in key)

    records = []
    for method, ranks in ((RATIO_SYSTEM, y_ranks), (REFERENCE_POINT, d_ranks)):
        keys = [tuple(np.flatnonzero(r == 1)) for r in ranks]
        for g in range(1, len(grid)):
            if keys[g] == keys[g - 1]:
                continue
            lo, hi = float(grid[g - 1]), float(grid[g])
            k_lo = keys[g - 1]
            for _ in range(_BISECTION_STEPS):
                mid = 0.5 * (lo + hi)
                if winners_at(mid, method) == k_lo:
                    lo = mid
                else:
                    hi = mid
            records.append(
                {
                    "Método": method,
                    "Peso": 0.5 * (lo + hi),
                    "Mejor antes": names(keys[g - 1]),
                    "Mejor después": names(keys[g]),
                }
            )
    change_points = pd.DataFrame(records, columns=["Método", "Peso", "Mejor antes", "Mejor después"])

    return SensitivityResult(
        alternatives=alts,
        criteria=crits,
        criterion_index=criterion_index,
        base_weight=base,
        grid=grid,
        weights_grid=weight_rows,
        ratio_scores=y,
        ratio_ranks=y_ranks,
        reference_scores=d,
        reference_ranks=d_ranks,
        change_points=change_points,
    )


def stability_table(matrix, weights, is_benefit, criteria=None, alternatives=None, steps: int = 201) -> pd.DataFrame:
    """Para cada criterio, intervalo de su peso en [0, 1] en el que la mejor
    alternativa actual de cada método no cambia. Cuanto más angosto el intervalo,
    más determinante es ese criterio para la decisión."""
    x = as_decision_matrix(matrix)
    n = x.shape[1]
    crits = list(criteria) if criteria is not None else [f"C{j + 1}" for j in range(n)]
    rows = []
    for k in range(n):
        res = sensitivity_analysis(
            x, weights, is_benefit, k, 0.0, 1.0, steps, alternatives=alternatives, criteria=crits
        )
        row = {"Criterio": crits[k], "Peso actual": res.base_weight}
        for label, method in (("SR", RATIO_SYSTEM), ("PR", REFERENCE_POINT)):
            lo, hi = res.stability_interval(method)
            row[f"{label}: desde"] = lo
            row[f"{label}: hasta"] = hi
            row[f"{label}: amplitud"] = hi - lo
        rows.append(row)
    return pd.DataFrame(rows).set_index("Criterio")

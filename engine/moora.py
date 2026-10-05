"""Métodos MOORA: Sistema de Razones y Enfoque de Punto de Referencia.

Notación (m alternativas, n criterios):

* ``x_ij``  : matriz de decisión.
* ``x*_ij`` : normalización vectorial ``x_ij / sqrt(sum_i x_ij^2)``.
* ``w_j``   : pesos (se normalizan para que sumen 1).
* Sistema de Razones: ``y_i = sum_{j∈Max} w_j x*_ij - sum_{j∈Min} w_j x*_ij``
  (ranking de mayor a menor).
* Punto de Referencia: ``r_j = max_i x*_ij`` (beneficio) o ``min_i x*_ij`` (costo);
  ``d_i = max_j w_j |r_j - x*_ij|`` (ranking de menor a mayor).

Todas las funciones son puras (sin dependencias de la interfaz) y validan sus
entradas lanzando ``ValueError`` con mensajes en español.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

import numpy as np
import pandas as pd

from .weights import normalize_weights

#: Diferencia absoluta por debajo de la cual dos puntajes se consideran empatados.
#: Los puntajes de MOORA están acotados en [-1, 1], por eso alcanza con una
#: tolerancia absoluta.
TIE_TOLERANCE = 1e-12

RATIO_SYSTEM = "Sistema de Razones"
REFERENCE_POINT = "Punto de Referencia"


class ZeroNormColumnError(ValueError):
    """Una o más columnas tienen suma de cuadrados igual a 0 (todas sus celdas son 0)."""

    def __init__(self, columns: list[int]):
        self.columns = list(columns)
        cols = ", ".join(str(j + 1) for j in self.columns)
        super().__init__(
            f"La suma de cuadrados es 0 en la(s) columna(s) {cols}: todos sus valores son 0 "
            "y la normalización vectorial dividiría por cero."
        )


# ---------------------------------------------------------------------------
# Conversión y validación de entradas
# ---------------------------------------------------------------------------

def as_decision_matrix(matrix) -> np.ndarray:
    """Convierte la entrada en una matriz ``float`` de m×n (m, n ≥ 1) sin vacíos."""
    try:
        x = np.asarray(matrix, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("La matriz de decisión contiene valores no numéricos.") from exc
    if x.ndim != 2:
        raise ValueError("La matriz de decisión debe ser bidimensional (alternativas × criterios).")
    m, n = x.shape
    if m < 1 or n < 1:
        raise ValueError("La matriz de decisión debe tener al menos 1 alternativa y 1 criterio.")
    if not np.all(np.isfinite(x)):
        raise ValueError("La matriz de decisión tiene celdas vacías o no numéricas.")
    return x


def as_direction_vector(is_benefit, n: int) -> np.ndarray:
    """Vector booleano de sentidos: ``True`` = beneficio (Max), ``False`` = costo (Min)."""
    arr = np.asarray(is_benefit)
    if arr.ndim != 1 or arr.size != n:
        raise ValueError(f"Se esperaban {n} sentidos de criterio y se recibieron {arr.size}.")
    if arr.dtype != bool:
        if not np.all(np.isin(arr, [0, 1, True, False])):
            raise ValueError("Los sentidos deben ser booleanos (True = beneficio, False = costo).")
        arr = arr.astype(bool)
    return arr


def _check_weights(weights, n: int) -> np.ndarray:
    w = normalize_weights(weights)
    if w.size != n:
        raise ValueError(f"Se esperaban {n} pesos y se recibieron {w.size}.")
    return w


def _labels(labels, count: int, prefix: str) -> list[str]:
    if labels is None:
        return [f"{prefix}{i + 1}" for i in range(count)]
    labels = [str(v) for v in labels]
    if len(labels) != count:
        raise ValueError(f"Se esperaban {count} nombres y se recibieron {len(labels)}.")
    return labels


# ---------------------------------------------------------------------------
# Pasos del método
# ---------------------------------------------------------------------------

def column_norms(matrix) -> np.ndarray:
    """Norma euclídea de cada columna: ``sqrt(sum_i x_ij^2)``."""
    x = as_decision_matrix(matrix)
    return np.sqrt((x ** 2).sum(axis=0))


def vector_normalize(matrix) -> np.ndarray:
    """Normalización vectorial ``x*_ij = x_ij / sqrt(sum_i x_ij^2)``.

    Raises:
        ZeroNormColumnError: si alguna columna tiene suma de cuadrados igual a 0.
    """
    x = as_decision_matrix(matrix)
    norms = np.sqrt((x ** 2).sum(axis=0))
    zero = np.flatnonzero(norms == 0)
    if zero.size:
        raise ZeroNormColumnError(zero.tolist())
    return x / norms


def weighted_normalized(normalized, weights) -> np.ndarray:
    """Matriz normalizada ponderada ``w_j · x*_ij``."""
    x = as_decision_matrix(normalized)
    return x * _check_weights(weights, x.shape[1])


def ratio_system(normalized, weights, is_benefit) -> np.ndarray:
    """Valor global del Sistema de Razones ``y_i``."""
    x = as_decision_matrix(normalized)
    w = _check_weights(weights, x.shape[1])
    sign = np.where(as_direction_vector(is_benefit, x.shape[1]), 1.0, -1.0)
    return (x * w * sign).sum(axis=1)


def reference_point(normalized, is_benefit) -> np.ndarray:
    """Punto de referencia ``r_j`` (máximo si es beneficio, mínimo si es costo)."""
    x = as_decision_matrix(normalized)
    benefit = as_direction_vector(is_benefit, x.shape[1])
    return np.where(benefit, x.max(axis=0), x.min(axis=0))


def reference_deviations(normalized, reference) -> np.ndarray:
    """Matriz de desviaciones ``|r_j - x*_ij|``."""
    x = as_decision_matrix(normalized)
    r = np.asarray(reference, dtype=float)
    if r.shape != (x.shape[1],):
        raise ValueError("El punto de referencia debe tener un valor por criterio.")
    return np.abs(r - x)


def reference_point_scores(normalized, weights, is_benefit) -> np.ndarray:
    """Desviación máxima ponderada (Tchebycheff) ``d_i = max_j w_j |r_j - x*_ij|``."""
    x = as_decision_matrix(normalized)
    w = _check_weights(weights, x.shape[1])
    dev = reference_deviations(x, reference_point(x, is_benefit))
    return (w * dev).max(axis=1)


def rank(scores, higher_is_better: bool = True, tol: float = TIE_TOLERANCE) -> np.ndarray:
    """Posiciones 1..m con empates "de competición" (1, 2, 2, 4).

    Dos puntajes que difieren en menos de ``tol`` comparten posición.
    """
    s = np.asarray(scores, dtype=float)
    if s.ndim != 1:
        raise ValueError("Los puntajes deben ser un vector.")
    if higher_is_better:
        better = s[None, :] > s[:, None] + tol
    else:
        better = s[None, :] < s[:, None] - tol
    return 1 + better.sum(axis=1)


def spearman_rho(ranks_a, ranks_b) -> float:
    """Coeficiente de correlación de rangos de Spearman.

    Se calcula como la correlación de Pearson entre rangos promedio, lo que
    equivale a ``1 - 6 Σd² / (m(m²-1))`` cuando no hay empates y además trata
    correctamente los empates. Devuelve ``nan`` si hay menos de 2 alternativas
    o si alguno de los rankings es constante.
    """
    a = pd.Series(np.asarray(ranks_a, dtype=float)).rank(method="average").to_numpy()
    b = pd.Series(np.asarray(ranks_b, dtype=float)).rank(method="average").to_numpy()
    if a.size != b.size:
        raise ValueError("Los rankings deben tener la misma cantidad de alternativas.")
    if a.size < 2:
        return float("nan")
    a = a - a.mean()
    b = b - b.mean()
    denom = np.sqrt((a ** 2).sum() * (b ** 2).sum())
    if denom == 0:
        return float("nan")
    return float((a * b).sum() / denom)


# ---------------------------------------------------------------------------
# Resolución completa
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MooraResult:
    """Resultado completo de MOORA con todos los pasos intermedios."""

    alternatives: list[str]
    criteria: list[str]
    matrix: np.ndarray
    weights: np.ndarray
    is_benefit: np.ndarray
    norms: np.ndarray
    normalized: np.ndarray
    weighted: np.ndarray
    ratio_scores: np.ndarray
    ratio_ranks: np.ndarray
    reference: np.ndarray
    deviations: np.ndarray
    weighted_deviations: np.ndarray
    reference_scores: np.ndarray
    reference_ranks: np.ndarray

    @property
    def m(self) -> int:
        return self.matrix.shape[0]

    @property
    def n(self) -> int:
        return self.matrix.shape[1]

    @property
    def directions(self) -> list[str]:
        return ["Beneficio" if b else "Costo" for b in self.is_benefit]

    @cached_property
    def signed_weighted(self) -> np.ndarray:
        """Aporte de cada criterio a ``y_i`` (positivo si beneficio, negativo si costo)."""
        return self.weighted * np.where(self.is_benefit, 1.0, -1.0)

    @cached_property
    def critical_criteria(self) -> np.ndarray:
        """Índice del criterio que determina ``d_i`` (peor desvío ponderado) por alternativa."""
        return self.weighted_deviations.argmax(axis=1)

    @property
    def ratio_winners(self) -> list[int]:
        return np.flatnonzero(self.ratio_ranks == 1).tolist()

    @property
    def reference_winners(self) -> list[int]:
        return np.flatnonzero(self.reference_ranks == 1).tolist()

    # -- Tablas para mostrar o exportar -------------------------------------

    def _frame(self, values: np.ndarray) -> pd.DataFrame:
        df = pd.DataFrame(values, index=self.alternatives, columns=self.criteria)
        df.index.name = "Alternativa"
        return df

    def criteria_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "Sentido": self.directions,
                "Peso": self.weights,
                "Norma √Σx²": self.norms,
            },
            index=pd.Index(self.criteria, name="Criterio"),
        )

    def decision_frame(self) -> pd.DataFrame:
        return self._frame(self.matrix)

    def normalized_frame(self) -> pd.DataFrame:
        return self._frame(self.normalized)

    def weighted_frame(self) -> pd.DataFrame:
        return self._frame(self.weighted)

    def ratio_frame(self) -> pd.DataFrame:
        df = self._frame(self.signed_weighted)
        benefit = self.weighted[:, self.is_benefit].sum(axis=1)
        cost = self.weighted[:, ~self.is_benefit].sum(axis=1)
        df["Σ Beneficio"] = benefit
        df["Σ Costo"] = cost
        df["y_i"] = self.ratio_scores
        df["Posición"] = self.ratio_ranks
        return df

    def reference_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            [self.reference, self.weights * self.reference],
            index=pd.Index(["r_j (normalizado)", "w_j · r_j (ponderado)"], name="Punto de referencia"),
            columns=self.criteria,
        )

    def deviations_frame(self) -> pd.DataFrame:
        return self._frame(self.deviations)

    def weighted_deviations_frame(self) -> pd.DataFrame:
        df = self._frame(self.weighted_deviations)
        df["d_i"] = self.reference_scores
        df["Posición"] = self.reference_ranks
        df["Criterio crítico"] = [self.criteria[j] for j in self.critical_criteria]
        return df

    def results_frame(self) -> pd.DataFrame:
        df = pd.DataFrame(
            {
                "y_i": self.ratio_scores,
                "Posición SR": self.ratio_ranks,
                "d_i": self.reference_scores,
                "Posición PR": self.reference_ranks,
            },
            index=pd.Index(self.alternatives, name="Alternativa"),
        )
        return df


def solve(matrix, weights, is_benefit, alternatives=None, criteria=None) -> MooraResult:
    """Resuelve MOORA (Sistema de Razones y Punto de Referencia).

    Args:
        matrix: matriz de decisión m×n.
        weights: pesos de los n criterios (se normalizan si no suman 1).
        is_benefit: ``True`` para criterios de beneficio (Max), ``False`` para costo (Min).
        alternatives: nombres de las alternativas (opcional).
        criteria: nombres de los criterios (opcional).
    """
    x = as_decision_matrix(matrix)
    m, n = x.shape
    benefit = as_direction_vector(is_benefit, n)
    w = _check_weights(weights, n)
    alts = _labels(alternatives, m, "A")
    crits = _labels(criteria, n, "C")

    norms = np.sqrt((x ** 2).sum(axis=0))
    normalized = vector_normalize(x)
    weighted = normalized * w
    y = (weighted * np.where(benefit, 1.0, -1.0)).sum(axis=1)
    r = reference_point(normalized, benefit)
    dev = reference_deviations(normalized, r)
    wdev = dev * w
    d = wdev.max(axis=1)

    return MooraResult(
        alternatives=alts,
        criteria=crits,
        matrix=x,
        weights=w,
        is_benefit=benefit,
        norms=norms,
        normalized=normalized,
        weighted=weighted,
        ratio_scores=y,
        ratio_ranks=rank(y, higher_is_better=True),
        reference=r,
        deviations=dev,
        weighted_deviations=wdev,
        reference_scores=d,
        reference_ranks=rank(d, higher_is_better=False),
    )


# ---------------------------------------------------------------------------
# Comparación de rankings
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RankingComparison:
    table: pd.DataFrame
    spearman: float
    ratio_winners: list[str]
    reference_winners: list[str]
    winners_match: bool
    position_matches: int
    notes: list[str]


def spearman_label(rho: float) -> str:
    """Interpretación cualitativa del coeficiente de Spearman."""
    if not np.isfinite(rho):
        return "no definido (se necesitan al menos 2 alternativas y rankings no constantes)"
    if rho >= 0.9:
        return "concordancia muy alta"
    if rho >= 0.7:
        return "concordancia alta"
    if rho >= 0.4:
        return "concordancia moderada"
    if rho >= 0:
        return "concordancia baja"
    return "los rankings tienden a ser opuestos"


def _join(names: list[str]) -> str:
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " y " + names[-1]


def compare_rankings(result: MooraResult) -> RankingComparison:
    """Compara los rankings de ambos métodos y genera notas interpretativas."""
    alts = result.alternatives
    diff = result.reference_ranks - result.ratio_ranks
    table = pd.DataFrame(
        {
            "y_i (SR)": result.ratio_scores,
            "Posición SR": result.ratio_ranks,
            "d_i (PR)": result.reference_scores,
            "Posición PR": result.reference_ranks,
            "Diferencia (PR − SR)": diff,
            "Coincide": diff == 0,
        },
        index=pd.Index(alts, name="Alternativa"),
    )
    rho = spearman_rho(result.ratio_ranks, result.reference_ranks)
    rw = [alts[i] for i in result.ratio_winners]
    pw = [alts[i] for i in result.reference_winners]
    match = bool(set(rw) & set(pw))
    return RankingComparison(
        table=table,
        spearman=rho,
        ratio_winners=rw,
        reference_winners=pw,
        winners_match=match,
        position_matches=int((diff == 0).sum()),
        notes=explain_comparison(result, rho),
    )


def explain_comparison(result: MooraResult, rho: float | None = None) -> list[str]:
    """Notas explicativas (en Markdown) sobre coincidencias y discrepancias."""
    alts, crits = result.alternatives, result.criteria
    if rho is None:
        rho = spearman_rho(result.ratio_ranks, result.reference_ranks)
    notes: list[str] = []

    rw, pw = result.ratio_winners, result.reference_winners
    if len(rw) > 1:
        notes.append(f"En el Sistema de Razones hay empate en el primer lugar entre {_join([alts[i] for i in rw])}.")
    if len(pw) > 1:
        notes.append(f"En el Punto de Referencia hay empate en el primer lugar entre {_join([alts[i] for i in pw])}.")

    a, b = rw[0], pw[0]
    if set(rw) & set(pw):
        common = sorted(set(rw) & set(pw))[0]
        notes.append(
            f"Ambos métodos eligen a **{alts[common]}**: es la mejor tanto en la agregación "
            "compensatoria (Sistema de Razones) como en la no compensatoria (Punto de Referencia), "
            "por lo que la recomendación es robusta frente al enfoque utilizado."
        )
    else:
        wd = result.weighted_deviations
        ca, cb = result.critical_criteria[a], result.critical_criteria[b]
        better = [crits[j] for j in range(result.n) if wd[a, j] < wd[b, j] - TIE_TOLERANCE]
        worse = [crits[j] for j in range(result.n) if wd[a, j] > wd[b, j] + TIE_TOLERANCE]
        notes.append(
            f"Los métodos **no coinciden**: el Sistema de Razones prefiere a **{alts[a]}** "
            f"(y = {result.ratio_scores[a]:.4f}) y el Punto de Referencia prefiere a **{alts[b]}** "
            f"(d = {result.reference_scores[b]:.4f})."
        )
        if better or worse:
            parts = []
            if better:
                parts.append(f"supera a {alts[b]} en {_join(better)}")
            if worse:
                parts.append(f"queda por detrás en {_join(worse)}")
            notes.append(
                f"El Sistema de Razones es **compensatorio**: suma los aportes de todos los criterios. "
                f"{alts[a]} {' y '.join(parts)}; sus fortalezas compensan su debilidad y obtiene el mayor y_i."
            )
        notes.append(
            "El Punto de Referencia es **no compensatorio** (métrica min-max de Tchebycheff): juzga a cada "
            f"alternativa por su peor desvío ponderado respecto del ideal. El peor desvío de {alts[a]} está en "
            f"**{crits[ca]}** ({wd[a, ca]:.4f}), mientras que el de {alts[b]} está en **{crits[cb]}** "
            f"({wd[b, cb]:.4f}); al ser menor, {alts[b]} presenta un perfil más equilibrado."
        )
        notes.append(
            f"Si el decisor acepta compensar debilidades con fortalezas, la recomendación es {alts[a]}; si prefiere "
            f"evitar desempeños pobres en algún criterio, es {alts[b]}. Conviene revisar la sensibilidad respecto "
            f"del peso de {crits[ca]}."
        )

    moved = [
        f"{alts[i]} ({result.ratio_ranks[i]}° → {result.reference_ranks[i]}°)"
        for i in range(result.m)
        if result.ratio_ranks[i] != result.reference_ranks[i]
    ]
    if moved:
        notes.append(f"Cambios de posición (SR → PR): {', '.join(moved)}.")
    elif result.m > 1:
        notes.append("Los dos rankings son idénticos en todas las posiciones.")

    if np.isfinite(rho):
        notes.append(f"Correlación de rangos de Spearman ρ = {rho:.4f}: {spearman_label(rho)}.")
    else:
        notes.append(f"Correlación de rangos de Spearman: {spearman_label(rho)}.")
    return notes

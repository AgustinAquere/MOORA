"""Obtención y normalización de pesos de los criterios.

Cuatro formas de asignar pesos:

* **Directa**: el decisor ingresa los pesos; si no suman 1 se normalizan.
* **Iguales**: ``w_j = 1/n``.
* **Entropía (Shannon)**: método objetivo; un criterio pesa más cuanto más
  dispersos (más informativos) son sus valores entre las alternativas.
* **CRITIC** (Diakoulaki et al., 1995): método objetivo; combina el contraste
  (desvío estándar) de cada criterio con su conflicto (baja correlación) con
  los demás.

Todas las funciones son puras y lanzan ``ValueError`` con un mensaje en español
cuando la entrada no es válida.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: Tolerancia para considerar que los pesos "suman 1".
SUM_TOLERANCE = 1e-4


def _as_float_vector(values, name: str = "pesos") -> np.ndarray:
    try:
        arr = np.asarray(values, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Los {name} deben ser numéricos.") from exc
    if arr.ndim != 1:
        raise ValueError(f"Los {name} deben ser un vector unidimensional.")
    if arr.size == 0:
        raise ValueError(f"Debe haber al menos un valor de {name}.")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"Hay {name} vacíos o no numéricos.")
    return arr


def weights_sum_to_one(weights, tol: float = SUM_TOLERANCE) -> bool:
    """Indica si los pesos suman 1 dentro de la tolerancia ``tol``."""
    arr = _as_float_vector(weights)
    return bool(abs(arr.sum() - 1.0) <= tol)


def normalize_weights(weights) -> np.ndarray:
    """Devuelve ``w / sum(w)``.

    Raises:
        ValueError: si hay pesos negativos, no numéricos o si la suma es 0.
    """
    arr = _as_float_vector(weights)
    if np.any(arr < 0):
        raise ValueError("Los pesos no pueden ser negativos.")
    total = arr.sum()
    if total <= 0:
        raise ValueError("La suma de los pesos debe ser mayor que 0.")
    return arr / total


def equal_weights(n: int) -> np.ndarray:
    """Pesos iguales ``1/n`` para ``n`` criterios."""
    if int(n) != n or n < 1:
        raise ValueError("La cantidad de criterios debe ser un entero mayor o igual a 1.")
    return np.full(int(n), 1.0 / n)


@dataclass(frozen=True)
class EntropyResult:
    """Pasos intermedios del método de entropía.

    Attributes:
        proportions: ``p_ij = x_ij / sum_i x_ij``.
        entropy: ``E_j = -k * sum_i p_ij ln p_ij`` con ``k = 1/ln(m)``.
        divergence: grado de diversificación ``d_j = 1 - E_j``.
        weights: ``w_j = d_j / sum_j d_j``.
    """

    proportions: np.ndarray
    entropy: np.ndarray
    divergence: np.ndarray
    weights: np.ndarray


def entropy_analysis(matrix) -> EntropyResult:
    """Calcula los pesos objetivos por entropía de Shannon.

    El método no depende del sentido del criterio (beneficio o costo): mide la
    dispersión de los valores. Requiere valores no negativos y al menos dos
    alternativas.

    Raises:
        ValueError: si la matriz no es válida para el método.
    """
    try:
        x = np.asarray(matrix, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("La matriz debe contener solo valores numéricos.") from exc
    if x.ndim != 2 or x.shape[0] < 1 or x.shape[1] < 1:
        raise ValueError("La matriz debe tener al menos una fila y una columna.")
    if not np.all(np.isfinite(x)):
        raise ValueError("La matriz tiene celdas vacías o no numéricas.")
    m, _ = x.shape
    if m < 2:
        raise ValueError("El método de entropía requiere al menos 2 alternativas.")
    if np.any(x < 0):
        raise ValueError("El método de entropía requiere valores no negativos en la matriz.")
    col_sums = x.sum(axis=0)
    zero_cols = np.flatnonzero(col_sums <= 0)
    if zero_cols.size:
        raise ValueError(
            "El método de entropía no admite columnas cuya suma sea 0 "
            f"(columnas {', '.join(str(j + 1) for j in zero_cols)})."
        )

    p = x / col_sums
    with np.errstate(divide="ignore", invalid="ignore"):
        plogp = np.where(p > 0, p * np.log(p), 0.0)
    k = 1.0 / np.log(m)
    entropy = -k * plogp.sum(axis=0)
    # Errores de redondeo pueden dar E_j apenas mayor que 1.
    divergence = np.clip(1.0 - entropy, 0.0, None)
    total = divergence.sum()
    if total <= 0:
        raise ValueError(
            "Todos los criterios tienen valores idénticos entre alternativas: "
            "la entropía no aporta información para asignar pesos."
        )
    return EntropyResult(
        proportions=p,
        entropy=entropy,
        divergence=divergence,
        weights=divergence / total,
    )


def entropy_weights(matrix) -> np.ndarray:
    """Atajo que devuelve solo los pesos de :func:`entropy_analysis`."""
    return entropy_analysis(matrix).weights


@dataclass(frozen=True)
class CriticResult:
    """Pasos intermedios del método CRITIC.

    Attributes:
        normalized: ``r_ij`` normalizada min-max según el sentido del criterio
            (beneficio: ``(x - min)/(max - min)``; costo: ``(max - x)/(max - min)``).
        std: desvío estándar muestral ``σ_j`` de cada columna de ``r``.
        correlation: matriz de correlación de Pearson ``ρ_jk`` entre criterios.
        conflict: ``sum_k (1 - ρ_jk)``.
        information: cantidad de información ``C_j = σ_j * sum_k (1 - ρ_jk)``.
        weights: ``w_j = C_j / sum_k C_k``.
    """

    normalized: np.ndarray
    std: np.ndarray
    correlation: np.ndarray
    conflict: np.ndarray
    information: np.ndarray
    weights: np.ndarray


def critic_analysis(matrix, is_benefit) -> CriticResult:
    """Calcula los pesos objetivos por el método CRITIC.

    Un criterio con valores constantes no aporta contraste: su ``σ_j`` es 0, su
    correlación con los demás se toma como 0 y recibe peso 0.

    Raises:
        ValueError: si la matriz o los sentidos no son válidos para el método.
    """
    try:
        x = np.asarray(matrix, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("La matriz debe contener solo valores numéricos.") from exc
    if x.ndim != 2 or x.shape[0] < 1 or x.shape[1] < 1:
        raise ValueError("La matriz debe tener al menos una fila y una columna.")
    if not np.all(np.isfinite(x)):
        raise ValueError("La matriz tiene celdas vacías o no numéricas.")
    m, n = x.shape
    if m < 2:
        raise ValueError("El método CRITIC requiere al menos 2 alternativas.")
    benefit = np.asarray(is_benefit, dtype=bool)
    if benefit.shape != (n,):
        raise ValueError(f"Se esperaban {n} sentidos y se recibieron {benefit.size}.")

    lo, hi = x.min(axis=0), x.max(axis=0)
    spread = hi - lo
    constant = spread == 0
    safe = np.where(constant, 1.0, spread)
    r = np.where(benefit, (x - lo) / safe, (hi - x) / safe)
    r[:, constant] = 0.0

    std = r.std(axis=0, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        corr = np.corrcoef(r, rowvar=False) if n > 1 else np.ones((1, 1))
    corr = np.atleast_2d(corr)
    corr = np.where(np.isfinite(corr), corr, 0.0)
    np.fill_diagonal(corr, 1.0)
    conflict = (1.0 - corr).sum(axis=1)
    information = std * conflict
    total = information.sum()
    if n == 1 and std[0] > 0:
        # Con un solo criterio no hay conflicto posible: recibe todo el peso.
        information = std.copy()
        total = information.sum()
    if total <= 0:
        raise ValueError(
            "Los criterios no aportan contraste ni conflicto (valores idénticos entre alternativas "
            "o criterios perfectamente correlacionados): CRITIC no puede asignar pesos."
        )
    return CriticResult(
        normalized=r,
        std=std,
        correlation=corr,
        conflict=conflict,
        information=information,
        weights=information / total,
    )


def critic_weights(matrix, is_benefit) -> np.ndarray:
    """Atajo que devuelve solo los pesos de :func:`critic_analysis`."""
    return critic_analysis(matrix, is_benefit).weights

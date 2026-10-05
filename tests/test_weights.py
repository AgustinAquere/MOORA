import numpy as np
import pytest

from engine import entropy_analysis, entropy_weights, equal_weights, normalize_weights, weights_sum_to_one


def test_normalize_weights_divides_by_sum():
    np.testing.assert_allclose(normalize_weights([2, 1, 1]), [0.5, 0.25, 0.25])


def test_normalize_weights_keeps_valid_weights():
    w = [0.35, 0.30, 0.15, 0.20]
    np.testing.assert_allclose(normalize_weights(w), w)


@pytest.mark.parametrize("weights", [[-0.1, 1.1], [0, 0], [], [np.nan, 1], ["a", 1]])
def test_normalize_weights_rejects_invalid(weights):
    with pytest.raises(ValueError):
        normalize_weights(weights)


def test_weights_sum_to_one_tolerance():
    assert weights_sum_to_one([0.35, 0.30, 0.15, 0.20])
    assert weights_sum_to_one([0.17051, 0.17512, 0.15668, 0.16590, 0.15668, 0.17512])  # suma 1,00001
    assert not weights_sum_to_one([0.3, 0.3, 0.3])


def test_equal_weights():
    np.testing.assert_allclose(equal_weights(4), [0.25] * 4)
    with pytest.raises(ValueError):
        equal_weights(0)


def test_entropy_hand_computed():
    # C1 constante -> E = 1, d = 0 -> peso 0.  C2: p = (0.25, 0.75).
    res = entropy_analysis([[1, 1], [1, 3]])
    e2 = -(0.25 * np.log(0.25) + 0.75 * np.log(0.75)) / np.log(2)
    np.testing.assert_allclose(res.entropy, [1.0, e2])
    np.testing.assert_allclose(res.divergence, [0.0, 1 - e2], atol=1e-15)
    np.testing.assert_allclose(res.weights, [0.0, 1.0])
    np.testing.assert_allclose(res.proportions[:, 1], [0.25, 0.75])


def test_entropy_weights_properties(robots):
    w = entropy_weights(robots["matrix"])
    assert w.sum() == pytest.approx(1.0)
    assert np.all(w >= 0)
    # Escalar una columna (cambio de unidades) no altera los pesos.
    scaled = robots["matrix"].copy()
    scaled[:, 0] *= 1000
    np.testing.assert_allclose(entropy_weights(scaled), w)


def test_entropy_gives_more_weight_to_more_dispersed_criterion():
    w = entropy_weights([[10, 10], [11, 1], [9, 30]])
    assert w[1] > w[0]


def test_entropy_handles_zero_cells():
    w = entropy_weights([[0, 1], [5, 2], [5, 3]])
    assert np.all(np.isfinite(w))


@pytest.mark.parametrize(
    "matrix",
    [
        [[1, 2]],  # una sola alternativa
        [[1, -2], [3, 4]],  # valores negativos
        [[0, 2], [0, 4]],  # columna de ceros
        [[1, 2], [1, 2]],  # todas las columnas constantes
        [[1, np.nan], [2, 3]],  # celda vacía
    ],
)
def test_entropy_rejects_invalid_matrices(matrix):
    with pytest.raises(ValueError):
        entropy_weights(matrix)

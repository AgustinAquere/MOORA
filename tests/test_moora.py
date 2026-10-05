import numpy as np
import pytest

from engine import (
    ZeroNormColumnError,
    column_norms,
    compare_rankings,
    rank,
    ratio_system,
    reference_point,
    reference_point_scores,
    solve,
    spearman_rho,
    vector_normalize,
)


# ---------------------------------------------------------------------------
# Normalización vectorial
# ---------------------------------------------------------------------------

def test_vector_normalization_hand_computed():
    # Columnas (3, 4) y (4, 3): norma 5 en ambas.
    x = [[3, 4], [4, 3]]
    np.testing.assert_allclose(column_norms(x), [5, 5])
    np.testing.assert_allclose(vector_normalize(x), [[0.6, 0.8], [0.8, 0.6]])


def test_normalized_columns_have_unit_norm(proveedores):
    n = vector_normalize(proveedores["matrix"])
    np.testing.assert_allclose(np.sqrt((n ** 2).sum(axis=0)), np.ones(4))


def test_zero_column_raises_clear_error():
    with pytest.raises(ZeroNormColumnError) as info:
        vector_normalize([[1, 0, 2], [3, 0, 4]])
    assert info.value.columns == [1]
    assert "columna(s) 2" in str(info.value)


def test_matches_course_spreadsheet_intermediate_steps(robots):
    np.testing.assert_allclose(
        column_norms(robots["matrix"]),
        [17255.2166, 231.5772, 3.50999, 15.30882, 14.41527, 15.35839],
        atol=5e-5,
    )
    n = vector_normalize(robots["matrix"])
    np.testing.assert_allclose(n[0], [0.4926, 0.38864, 0.39886, 0.33967, 0.4856, 0.40369], atol=5e-6)


# ---------------------------------------------------------------------------
# Sistema de Razones y Punto de Referencia: casos calculados a mano
# ---------------------------------------------------------------------------

def test_two_by_two_hand_computed():
    # x* = [[0.6, 0.8], [0.8, 0.6]], w = (0.5, 0.5), C1 beneficio, C2 costo.
    x = [[3, 4], [4, 3]]
    w = [0.5, 0.5]
    benefit = [True, False]
    n = vector_normalize(x)
    np.testing.assert_allclose(ratio_system(n, w, benefit), [-0.1, 0.1])
    np.testing.assert_allclose(reference_point(n, benefit), [0.8, 0.6])
    np.testing.assert_allclose(reference_point_scores(n, w, benefit), [0.1, 0.0], atol=1e-15)

    res = solve(x, w, benefit)
    assert res.ratio_ranks.tolist() == [2, 1]
    assert res.reference_ranks.tolist() == [2, 1]


def test_tp_supplier_example_matches_report(proveedores):
    p = proveedores
    res = solve(p["matrix"], p["weights"], p["is_benefit"], p["alternatives"], p["criteria"])
    np.testing.assert_allclose(res.ratio_scores, p["y"], atol=5e-5)
    np.testing.assert_allclose(res.reference_scores, p["d"], atol=5e-5)
    assert res.ratio_ranks.tolist() == p["y_rank"]
    assert res.reference_ranks.tolist() == p["d_rank"]


def test_course_activity_matches_spreadsheet(robots):
    r = robots
    res = solve(r["matrix"], r["weights"], r["is_benefit"])
    np.testing.assert_allclose(res.ratio_scores, r["y"], atol=5e-6)
    np.testing.assert_allclose(res.reference_scores, r["d"], atol=5e-6)
    assert res.ratio_ranks.tolist() == r["y_rank"]
    assert res.reference_ranks.tolist() == r["d_rank"]


def test_reference_point_uses_max_for_benefit_and_min_for_cost(proveedores):
    p = proveedores
    res = solve(p["matrix"], p["weights"], p["is_benefit"])
    n = res.normalized
    expected = [n[:, 0].min(), n[:, 1].max(), n[:, 2].min(), n[:, 3].max()]
    np.testing.assert_allclose(res.reference, expected)
    np.testing.assert_allclose(res.deviations, np.abs(res.reference - n))
    np.testing.assert_allclose(res.weighted_deviations, res.deviations * res.weights)
    np.testing.assert_allclose(res.reference_scores, res.weighted_deviations.max(axis=1))


def test_ratio_score_is_benefits_minus_costs(proveedores):
    p = proveedores
    res = solve(p["matrix"], p["weights"], p["is_benefit"])
    frame = res.ratio_frame()
    np.testing.assert_allclose(frame["Σ Beneficio"] - frame["Σ Costo"], res.ratio_scores)
    np.testing.assert_allclose(res.signed_weighted.sum(axis=1), res.ratio_scores)


def test_critical_criterion_is_the_argmax_of_weighted_deviations(proveedores):
    p = proveedores
    res = solve(p["matrix"], p["weights"], p["is_benefit"], p["alternatives"], p["criteria"])
    # El precio es la peor dimensión tanto de A como de C.
    assert res.critical_criteria[0] == 0
    assert res.critical_criteria[2] == 0


# ---------------------------------------------------------------------------
# Casos límite (plan de validación, prueba 3)
# ---------------------------------------------------------------------------

def test_weights_not_summing_to_one_are_normalized(proveedores):
    p = proveedores
    a = solve(p["matrix"], p["weights"], p["is_benefit"])
    b = solve(p["matrix"], p["weights"] * 7, p["is_benefit"])
    np.testing.assert_allclose(a.ratio_scores, b.ratio_scores)
    np.testing.assert_allclose(a.reference_scores, b.reference_scores)
    np.testing.assert_allclose(b.weights.sum(), 1.0)


def test_all_benefit_criteria():
    res = solve([[1, 2], [2, 4], [3, 1]], [0.5, 0.5], [True, True])
    assert np.all(res.ratio_scores > 0)
    assert res.ratio_ranks.tolist() == [3, 1, 2]


def test_all_cost_criteria():
    res = solve([[1, 2], [2, 4], [3, 1]], [0.5, 0.5], [False, False])
    assert np.all(res.ratio_scores < 0)
    assert res.ratio_ranks.tolist() == [1, 3, 2]


def test_single_alternative():
    res = solve([[5, 3]], [0.6, 0.4], [True, False])
    assert res.ratio_ranks.tolist() == [1]
    assert res.reference_ranks.tolist() == [1]
    assert res.reference_scores.tolist() == [0.0]
    assert np.isnan(compare_rankings(res).spearman)


def test_single_criterion():
    res = solve([[3], [4]], [1.0], [True])
    np.testing.assert_allclose(res.ratio_scores, [0.6, 0.8])
    assert res.ratio_ranks.tolist() == [2, 1]
    assert res.reference_ranks.tolist() == [2, 1]


def test_negative_values_do_not_break_the_calculation():
    res = solve([[-2, 1], [1, 2], [3, -1]], [0.5, 0.5], [True, False])
    assert np.all(np.isfinite(res.ratio_scores))
    assert np.all(np.isfinite(res.reference_scores))


@pytest.mark.parametrize(
    "matrix, weights, benefit",
    [
        (np.empty((0, 2)), [0.5, 0.5], [True, True]),  # m < 1
        (np.empty((2, 0)), [], []),  # n < 1
        ([[1, np.nan], [2, 3]], [0.5, 0.5], [True, True]),  # celda vacía
        ([[1, "a"], [2, 3]], [0.5, 0.5], [True, True]),  # no numérico
        ([[1, 2], [3, 4]], [0.5], [True, True]),  # cantidad de pesos
        ([[1, 2], [3, 4]], [-0.5, 1.5], [True, True]),  # peso negativo
        ([[1, 2], [3, 4]], [0, 0], [True, True]),  # suma de pesos 0
        ([[1, 2], [3, 4]], [0.5, 0.5], [True]),  # cantidad de sentidos
        ([[1, 0], [3, 0]], [0.5, 0.5], [True, True]),  # columna de ceros
    ],
)
def test_invalid_inputs_raise_value_error(matrix, weights, benefit):
    with pytest.raises(ValueError):
        solve(matrix, weights, benefit)


# ---------------------------------------------------------------------------
# Rankings y Spearman
# ---------------------------------------------------------------------------

def test_rank_with_ties_uses_competition_ranking():
    assert rank([0.5, 0.5, 0.1]).tolist() == [1, 1, 3]
    assert rank([0.5, 0.5, 0.1], higher_is_better=False).tolist() == [2, 2, 1]
    assert rank([0.3, 0.3 + 1e-15]).tolist() == [1, 1]  # diferencia numérica despreciable


def test_spearman_known_values():
    assert spearman_rho([1, 2, 3, 4], [1, 2, 3, 4]) == pytest.approx(1.0)
    assert spearman_rho([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    # Sin empates coincide con 1 - 6Σd² / (m(m²-1)).
    a, b = np.array([2, 3, 1, 4, 5]), np.array([1, 3, 2, 5, 4])
    m = a.size
    expected = 1 - 6 * ((a - b) ** 2).sum() / (m * (m ** 2 - 1))
    assert spearman_rho(a, b) == pytest.approx(expected)


def test_spearman_with_ties_uses_average_ranks():
    # Rangos promedio: a = (1.5, 1.5, 3), b = (1, 2, 3) -> Pearson = sqrt(3)/2.
    assert spearman_rho([1, 1, 3], [1, 2, 3]) == pytest.approx(np.sqrt(3) / 2)


def test_spearman_undefined_cases():
    assert np.isnan(spearman_rho([1], [1]))
    assert np.isnan(spearman_rho([1, 1, 1], [1, 2, 3]))


# ---------------------------------------------------------------------------
# Comparación de métodos
# ---------------------------------------------------------------------------

def test_tp_comparison_detects_discrepancy(proveedores):
    p = proveedores
    res = solve(p["matrix"], p["weights"], p["is_benefit"], p["alternatives"], p["criteria"])
    cmp = compare_rankings(res)
    assert cmp.ratio_winners == ["Proveedor C"]
    assert cmp.reference_winners == ["Proveedor A"]
    assert not cmp.winners_match
    assert cmp.spearman == pytest.approx(0.8)
    assert cmp.position_matches == 2
    assert cmp.table["Coincide"].tolist() == [False, True, False, True]
    text = " ".join(cmp.notes)
    assert "compensatorio" in text and "no compensatorio" in text
    assert "Precio" in text


def test_compensatory_vs_balanced_profile():
    # B es excelente en C1 y muy malo en C2; A es equilibrada.
    res = solve([[5, 5], [9, 2], [2, 8]], [0.5, 0.5], [True, True], ["A", "B", "C"])
    cmp = compare_rankings(res)
    assert cmp.ratio_winners == ["B"]
    assert cmp.reference_winners == ["A"]


def test_comparison_when_methods_agree():
    res = solve([[10, 1], [5, 5], [1, 10]], [0.5, 0.5], [True, False], ["X", "Y", "Z"])
    cmp = compare_rankings(res)
    assert cmp.winners_match
    assert cmp.ratio_winners == cmp.reference_winners == ["X"]
    assert any("Ambos métodos eligen" in note for note in cmp.notes)

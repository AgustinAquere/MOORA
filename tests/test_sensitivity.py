import numpy as np
import pytest

from engine import (
    RATIO_SYSTEM,
    REFERENCE_POINT,
    redistribute_weights,
    sensitivity_analysis,
    solve,
    stability_table,
    vector_normalize,
)


def test_redistribute_formula():
    # w_j' = w_j (1 - w_k') / (1 - w_k)
    np.testing.assert_allclose(redistribute_weights([0.5, 0.3, 0.2], 0, 0.2), [0.2, 0.48, 0.32])


def test_redistribute_keeps_sum_and_proportions():
    w = np.array([0.35, 0.30, 0.15, 0.20])
    for t in np.linspace(0, 1, 11):
        out = redistribute_weights(w, 2, t)
        assert out.sum() == pytest.approx(1.0)
        assert out[2] == pytest.approx(t)
        if t < 1:
            others = np.delete(out, 2)
            np.testing.assert_allclose(others / others.sum(), np.delete(w, 2) / np.delete(w, 2).sum())


def test_redistribute_when_criterion_had_all_the_weight():
    np.testing.assert_allclose(redistribute_weights([1, 0, 0], 0, 0.4), [0.4, 0.3, 0.3])


def test_redistribute_invalid_arguments():
    with pytest.raises(ValueError):
        redistribute_weights([0.5, 0.5], 0, 1.5)
    with pytest.raises(ValueError):
        redistribute_weights([0.5, 0.5], 3, 0.5)
    with pytest.raises(ValueError):
        redistribute_weights([1.0], 0, 0.5)


def test_base_weight_reproduces_solve(proveedores):
    p = proveedores
    s = sensitivity_analysis(p["matrix"], p["weights"], p["is_benefit"], 1, steps=21)
    g = int(np.flatnonzero(np.isclose(s.grid, 0.30))[0])
    base = solve(p["matrix"], p["weights"], p["is_benefit"])
    np.testing.assert_allclose(s.ratio_scores[g], base.ratio_scores)
    np.testing.assert_allclose(s.reference_scores[g], base.reference_scores)
    np.testing.assert_array_equal(s.ratio_ranks[g], base.ratio_ranks)
    np.testing.assert_array_equal(s.reference_ranks[g], base.reference_ranks)


def test_change_point_two_criteria_hand_computed():
    # x* = [[0.6, 0.8], [0.8, 0.6]]; y_A = 0.8 - 0.2t, y_B = 0.6 + 0.2t -> cruce en t = 0.5.
    # d_A = 0.2t, d_B = 0.2(1 - t) -> cruce en t = 0.5.
    s = sensitivity_analysis([[3, 4], [4, 3]], [0.3, 0.7], [True, True], 0, steps=8, alternatives=["A", "B"])
    cps = s.change_points
    assert len(cps) == 2
    for method in (RATIO_SYSTEM, REFERENCE_POINT):
        row = cps[cps["Método"] == method].iloc[0]
        assert row["Peso"] == pytest.approx(0.5, abs=1e-9)
        assert row["Mejor antes"] == "A"
        assert row["Mejor después"] == "B"
    assert s.stability_interval(RATIO_SYSTEM) == pytest.approx((0.0, 0.5), abs=1e-9)


def test_tp_change_point_matches_linear_crossing(proveedores):
    """El y_i es lineal en el peso del precio: el cruce C/B puede calcularse en forma cerrada."""
    p = proveedores
    s = sensitivity_analysis(
        p["matrix"], p["weights"], p["is_benefit"], 0, alternatives=p["alternatives"], criteria=p["criteria"]
    )
    sr = s.change_points[s.change_points["Método"] == RATIO_SYSTEM]
    assert sr["Mejor antes"].tolist() == ["Proveedor C"]
    assert sr["Mejor después"].tolist() == ["Proveedor B"]

    n = vector_normalize(p["matrix"])
    sign = np.where(p["is_benefit"], 1.0, -1.0)
    w = p["weights"]
    # y_i(t) = a_i t + b_i (1 - t)
    a = sign[0] * n[:, 0]
    b = (n[:, 1:] * sign[1:] * w[1:]).sum(axis=1) / (1 - w[0])
    i_b, i_c = 1, 2
    t_star = (b[i_b] - b[i_c]) / ((a[i_c] - b[i_c]) - (a[i_b] - b[i_b]))
    assert sr["Peso"].iloc[0] == pytest.approx(t_star, abs=1e-9)


def test_stability_interval_contains_base_weight(proveedores):
    p = proveedores
    s = sensitivity_analysis(p["matrix"], p["weights"], p["is_benefit"], 0)
    for method in (RATIO_SYSTEM, REFERENCE_POINT):
        lo, hi = s.stability_interval(method)
        assert lo <= 0.35 <= hi


def test_stability_interval_none_when_base_outside_range(proveedores):
    p = proveedores
    s = sensitivity_analysis(p["matrix"], p["weights"], p["is_benefit"], 0, w_min=0.5, w_max=0.9)
    assert s.stability_interval(RATIO_SYSTEM) is None


def test_frames_shapes(proveedores):
    p = proveedores
    s = sensitivity_analysis(p["matrix"], p["weights"], p["is_benefit"], 3, steps=11, alternatives=p["alternatives"])
    g = len(s.grid)
    assert len(s.long_frame()) == 2 * g * 4
    wf = s.winners_frame()
    assert len(wf) == g
    np.testing.assert_allclose(wf.filter(like="w ").sum(axis=1), np.ones(g))


def test_stability_table(proveedores):
    p = proveedores
    t = stability_table(p["matrix"], p["weights"], p["is_benefit"], criteria=p["criteria"], steps=51)
    assert list(t.index) == p["criteria"]
    assert np.all(t["SR: desde"] <= t["Peso actual"]) and np.all(t["Peso actual"] <= t["SR: hasta"])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"criterion_index": 5},
        {"criterion_index": 0, "w_min": 0.6, "w_max": 0.4},
        {"criterion_index": 0, "steps": 1},
    ],
)
def test_sensitivity_invalid_arguments(proveedores, kwargs):
    p = proveedores
    with pytest.raises(ValueError):
        sensitivity_analysis(p["matrix"], p["weights"], p["is_benefit"], **kwargs)


def test_sensitivity_requires_two_criteria():
    with pytest.raises(ValueError):
        sensitivity_analysis([[1], [2]], [1.0], [True], 0)

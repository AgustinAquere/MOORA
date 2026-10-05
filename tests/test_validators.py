import numpy as np
import pandas as pd
import pytest

from data_io.validators import (
    parse_direction,
    parse_number,
    unique_labels,
    validate_matrix,
    validate_problem,
    validate_weights,
)

ALTS = ["A", "B"]
CRITS = ["C1", "C2"]


@pytest.mark.parametrize(
    "value, expected",
    [
        (3, 3.0),
        (2.5, 2.5),
        ("2,5", 2.5),
        (" 2.5 ", 2.5),
        ("1.234,5", 1234.5),
        ("1,234.5", 1234.5),
        ("35%", 0.35),
        ("-4", -4.0),
        ("", None),
        (None, None),
        (np.nan, None),
    ],
)
def test_parse_number(value, expected):
    assert parse_number(value) == (pytest.approx(expected) if expected is not None else None)


@pytest.mark.parametrize("value", ["abc", "1,2,3", True, float("inf")])
def test_parse_number_rejects_non_numeric(value):
    with pytest.raises(ValueError):
        parse_number(value)


def test_parse_direction():
    assert parse_direction("MAX") is True
    assert parse_direction("Beneficio") is True
    assert parse_direction("min") is False
    assert parse_direction(" Costo ") is False
    assert parse_direction("otro") is None
    assert parse_direction(None) is None


def test_unique_labels():
    assert unique_labels(["Precio", "", "Precio", None], "C") == ["Precio", "C2", "Precio (2)", "C4"]


def test_validate_matrix_ok():
    report, x = validate_matrix([[1, 2], [3, 4]], ALTS, CRITS)
    assert report.ok and not report.warnings
    np.testing.assert_allclose(x, [[1, 2], [3, 4]])


def test_validate_matrix_empty_and_non_numeric_cells():
    report, x = validate_matrix(pd.DataFrame([[1, None], ["x", 4]]), ALTS, CRITS)
    assert x is None
    text = " ".join(report.errors)
    assert "vacía" in text and "A / C2" in text
    assert "no numérico" in text and "B / C1" in text and "«x»" in text


def test_validate_matrix_zero_column():
    report, x = validate_matrix([[1, 0], [3, 0]], ALTS, CRITS)
    assert x is None
    assert any("suma de cuadrados es 0" in e and "C2" in e for e in report.errors)


def test_validate_matrix_negative_values_is_a_warning():
    report, x = validate_matrix([[-1, 2], [3, 4]], ALTS, CRITS)
    assert report.ok and x is not None
    assert any("negativos" in w for w in report.warnings)


def test_validate_matrix_constant_column_warning():
    report, _ = validate_matrix([[5, 2], [5, 4]], ALTS, CRITS)
    assert any("no discrimina" in w for w in report.warnings)


def test_validate_matrix_dimensions():
    report, x = validate_matrix(np.empty((0, 0)), [], [])
    assert x is None
    assert len(report.errors) == 2
    report, _ = validate_matrix([[1, 2]], ["A"], CRITS)
    assert report.ok and any("una sola alternativa" in w for w in report.warnings)


def test_validate_weights_normalizes_and_warns():
    report, w = validate_weights([2, 2], CRITS)
    assert report.ok
    np.testing.assert_allclose(w, [0.5, 0.5])
    assert any("suman 4.0000" in m for m in report.warnings)


def test_validate_weights_accepts_comma_decimals():
    report, w = validate_weights(["0,4", "0,6"], CRITS)
    assert report.ok and not report.warnings
    np.testing.assert_allclose(w, [0.4, 0.6])


@pytest.mark.parametrize(
    "weights, fragment",
    [
        ([-0.2, 1.2], "negativos"),
        ([0, 0], "suma de los pesos es 0"),
        ([None, 1], "Falta el peso"),
        (["x", 1], "no numérico"),
        ([1], "Se esperaban 2 pesos"),
    ],
)
def test_validate_weights_errors(weights, fragment):
    report, w = validate_weights(weights, CRITS)
    assert w is None
    assert any(fragment in e for e in report.errors)


def test_validate_problem_ok():
    report, inputs = validate_problem(ALTS, CRITS, [[1, 2], [3, 4]], ["Beneficio", "Costo"], [0.5, 0.5])
    assert report.ok
    assert inputs.is_benefit.tolist() == [True, False]
    assert inputs.alternatives == ALTS


def test_validate_problem_collects_all_errors():
    report, inputs = validate_problem(
        ["A", "A"], ["C1", ""], [[1, None], [3, 4]], ["Beneficio", None], [-1, 1]
    )
    assert inputs is None
    text = " ".join(report.errors)
    assert "repetidos" in text
    assert "sin nombre" in text
    assert "vacía" in text
    assert "sentido" in text
    assert "negativos" in text

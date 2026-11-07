import io
import zipfile
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
import pytest

from data_io.examples import EXAMPLES
from data_io.serializers import (
    excel_sheet_names,
    problem_to_csv,
    problem_to_excel,
    read_problem,
    results_to_csv,
    results_to_csv_zip,
    results_to_excel,
)
from data_io.validators import validate_problem
from engine import compare_rankings, sensitivity_analysis, solve


def _xlsx(rows, start_row=1, start_col=1) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            if v is not None:
                ws.cell(row=start_row + i, column=start_col + j, value=v)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_read_csv_with_semicolon_and_decimal_comma():
    text = "Alternativa;Precio;Calidad\nA;120,5;8\nB;100;7\nSentido;Costo;Beneficio\nPeso;0,6;0,4\n"
    p = read_problem(text.encode("utf-8"), "datos.csv")
    assert p.alternatives == ["A", "B"]
    assert p.criteria == ["Precio", "Calidad"]
    np.testing.assert_allclose(p.values.to_numpy(), [[120.5, 8], [100, 7]])
    assert p.directions == ["Costo", "Beneficio"]
    assert p.weights == pytest.approx([0.6, 0.4])
    assert p.warnings == []


def test_read_csv_without_metadata_rows():
    p = read_problem(b"Alt,C1,C2\nX,1,2\nY,3,4\n", "datos.csv")
    assert p.directions is None and p.weights is None
    assert p.values.shape == (2, 2)


def test_read_csv_non_numeric_values_become_empty_with_warning():
    p = read_problem(b"Alt,C1,C2\nX,1,abc\nY,3,\n", "datos.csv")
    assert np.isnan(p.values.iloc[0, 1]) and np.isnan(p.values.iloc[1, 1])
    assert any("abc" in w for w in p.warnings)


def test_read_excel_with_offset_and_subheader_row():
    """Formato de «Tabla MOORA.xlsx»: tabla desde B2 y una fila «Alternativas» vacía."""
    rows = [
        ["Variables", "X1", "X2"],
        ["Alternativas", None, None],
        ["A1", 8500, 90],
        ["A2", 4750, 85],
    ]
    p = read_problem(_xlsx(rows, start_row=2, start_col=2), "tabla.xlsx")
    assert p.alternatives == ["A1", "A2"]
    assert p.criteria == ["X1", "X2"]
    assert any("Alternativas" in w for w in p.warnings)


def test_read_excel_with_minmax_row_above_header_and_other_tables_below():
    """Formato de la planilla de la actividad: fila MIN/MAX arriba, fila W abajo y más tablas debajo."""
    rows = [
        [None, "MIN", "MAX"],
        ["Variables", "X1", "X2"],
        ["A1", 8500, 90],
        ["A2", 4750, 85],
        [None, None, None],
        ["W", 0.4, 0.6],
        [None, None, None, "comentario"],
        ["Variables", "X1", "X2"],
        ["A1", 72250000, 8100],
    ]
    p = read_problem(_xlsx(rows), "actividad.xlsx")
    assert p.alternatives == ["A1", "A2"]
    assert p.directions == ["Costo", "Beneficio"]
    assert p.weights == pytest.approx([0.4, 0.6])


@pytest.mark.parametrize(
    "data, name",
    [
        (b"", "vacio.csv"),
        (b"Alt,C1\n", "solo_encabezado.csv"),
        (b"Alt\nA\n", "sin_criterios.csv"),
        (b"\x00\x01", "archivo.pdf"),
    ],
)
def test_read_invalid_files_raise_value_error(data, name):
    with pytest.raises(ValueError):
        read_problem(data, name)


@pytest.mark.parametrize("fmt", ["xlsx", "csv"])
def test_problem_round_trip(fmt):
    ex = EXAMPLES["Selección de proveedores (ejemplo del TP)"]
    args = (ex.alternatives, ex.criteria, ex.values, ex.directions, ex.weights)
    data = problem_to_excel(*args) if fmt == "xlsx" else problem_to_csv(*args, sep=";", decimal=",")
    p = read_problem(data, f"problema.{fmt}")
    assert p.alternatives == ex.alternatives
    assert p.criteria == ex.criteria
    np.testing.assert_allclose(p.values.to_numpy(), ex.values)
    assert p.directions == ex.directions
    assert p.weights == pytest.approx(ex.weights)


def test_problem_csv_uses_the_requested_decimal_separator():
    """La tabla del problema mezcla texto (filas Sentido) y números: todos deben usar la coma pedida."""
    ex = EXAMPLES["Selección de proveedores (ejemplo del TP)"]
    text = problem_to_csv(ex.alternatives, ex.criteria, ex.values, ex.directions, ex.weights,
                          sep=";", decimal=",").decode("utf-8-sig")
    lines = text.splitlines()
    assert lines[1] == "Proveedor A;120;8;10;5000"
    assert lines[-1] == "Peso;0,35;0,3;0,15;0,2"
    assert not any("." in line for line in lines[1:])

    text = problem_to_csv(ex.alternatives, ex.criteria, ex.values, ex.directions, ex.weights,
                          sep=",", decimal=".").decode("utf-8-sig")
    assert text.splitlines()[-1] == "Peso,0.35,0.3,0.15,0.2"


def test_problem_csv_template_with_empty_cells_and_weights():
    """La plantilla del paso 1 puede tener celdas y pesos vacíos: quedan vacíos en el CSV."""
    values = np.array([[1.5, np.nan], [2.0, 3.0]])
    text = problem_to_csv(["A", "B"], ["C1", "C2"], values, ["Beneficio", "Costo"], [0.5, None],
                          sep=";", decimal=",").decode("utf-8-sig")
    assert text.splitlines()[1:] == ["A;1,5;", "B;2;3", "Sentido;Beneficio;Costo", "Peso;0,5;"]


def test_results_csv_zip_problem_sheet_uses_decimal_comma(tp_outputs):
    res, cmp, sens = tp_outputs
    with zipfile.ZipFile(io.BytesIO(results_to_csv_zip(res, cmp, sens, sep=";", decimal=","))) as zf:
        problema = zf.read(next(n for n in zf.namelist() if n.endswith("_problema.csv"))).decode("utf-8-sig")
        resumen = zf.read(next(n for n in zf.namelist() if n.endswith("_resumen.csv"))).decode("utf-8-sig")
    assert "Peso;0,35;0,3;0,15;0,2" in problema
    assert "Spearman rho;0,8" in resumen


def test_read_legacy_xls_file():
    """Libro de Excel 97-2003 (.xls) con dos hojas: el problema está en la segunda."""
    pytest.importorskip("xlrd")
    data = (Path(__file__).parent / "data" / "proveedores.xls").read_bytes()
    assert excel_sheet_names(data) == ["Notas", "Datos"]
    p = read_problem(data, "proveedores.xls", sheet="Datos")
    assert p.alternatives == ["Proveedor A", "Proveedor B", "Proveedor C", "Proveedor D"]
    assert p.criteria == ["Precio", "Calidad", "Plazo", "Capacidad"]
    np.testing.assert_allclose(p.values.to_numpy(), [[120, 8, 10, 5000], [100, 7, 15, 4000],
                                                     [135, 9, 7, 6000], [110, 6, 12, 4500]])
    assert p.directions == ["Costo", "Beneficio", "Costo", "Beneficio"]
    assert p.weights == pytest.approx([0.35, 0.30, 0.15, 0.20])


@pytest.fixture
def tp_outputs():
    ex = EXAMPLES["Selección de proveedores (ejemplo del TP)"]
    benefit = [d == "Beneficio" for d in ex.directions]
    res = solve(ex.values, ex.weights, benefit, ex.alternatives, ex.criteria)
    sens = sensitivity_analysis(ex.values, ex.weights, benefit, 0, steps=11,
                                alternatives=ex.alternatives, criteria=ex.criteria)
    return res, compare_rankings(res), sens


def test_results_excel_has_all_steps(tp_outputs):
    res, cmp, sens = tp_outputs
    data = results_to_excel(res, cmp, sens, problem_name="TP")
    sheets = pd.ExcelFile(io.BytesIO(data)).sheet_names
    for name in ["Resumen", "Problema", "Normalizada", "Ponderada", "Sistema de Razones",
                 "Punto de referencia", "Desviaciones", "Desviaciones ponderadas", "Resultados",
                 "Comparacion", "Sensibilidad", "Puntos de cambio"]:
        assert name in sheets
    resultados = pd.read_excel(io.BytesIO(data), sheet_name="Resultados", index_col=0)
    np.testing.assert_allclose(resultados["y_i"], res.ratio_scores)
    # La hoja «Problema» del libro de resultados se puede volver a importar.
    p = read_problem(data, "resultados.xlsx", sheet="Problema")
    assert p.alternatives == res.alternatives


def test_results_csv_zip_and_single_csv(tp_outputs):
    res, cmp, sens = tp_outputs
    with zipfile.ZipFile(io.BytesIO(results_to_csv_zip(res, cmp, sens))) as zf:
        names = zf.namelist()
    assert any("normalizada" in n for n in names)
    assert any("resultados" in n for n in names)
    csv = results_to_csv(res, cmp, sep=";", decimal=",").decode("utf-8-sig")
    assert "Proveedor C" in csv and ";" in csv


@pytest.mark.parametrize("name", list(EXAMPLES))
def test_examples_are_valid_and_solvable(name):
    ex = EXAMPLES[name]
    report, inputs = validate_problem(ex.alternatives, ex.criteria, ex.values, ex.directions, ex.weights)
    assert report.ok, report.errors
    res = solve(inputs.matrix, inputs.weights, inputs.is_benefit, inputs.alternatives, inputs.criteria)
    assert sorted(res.ratio_ranks.tolist())[0] == 1

"""Paso 6: exportación de datos, pasos intermedios y resultados."""

from __future__ import annotations

import re

import streamlit as st

from data_io.serializers import (
    EXCEL_MIME,
    problem_to_csv,
    problem_to_excel,
    result_sheets,
    results_to_csv,
    results_to_csv_zip,
    results_to_excel,
)

from . import state
from .components import md, nav_buttons, require_results
from .step_sensitivity import run_sensitivity


def _slug(text: str) -> str:
    slug = re.sub(r"[^\w\-]+", "_", text.strip(), flags=re.UNICODE).strip("_").lower()
    return slug or "moora"


def render() -> None:
    p = state.get_problem()
    analysis = state.analyze(p)
    st.header("6 · Exportación y reporte")
    if not require_results(analysis):
        nav_buttons(state.STEPS[5])
        return
    r, cmp = analysis.result, analysis.comparison

    sens = None
    cfg = st.session_state.get("sensitivity_cfg")
    include_sens = False
    if cfg and cfg["criterion"] < r.n:
        include_sens = st.checkbox(
            md(f"Incluir el último análisis de sensibilidad (peso de «{r.criteria[cfg['criterion']]}» "
            f"entre {cfg['w_min']:.2f} y {cfg['w_max']:.2f})"),
            value=True,
        )
    else:
        st.caption("Para incluir un análisis de sensibilidad en la exportación, configúrelo primero en el paso 5.")
    if include_sens:
        try:
            sens = run_sensitivity(analysis, cfg)
        except ValueError:
            sens = None

    c1, c2 = st.columns(2)
    sep_label = c1.radio("Formato CSV", ["Coma (,) y punto decimal", "Punto y coma (;) y coma decimal"], index=1,
                         help="Excel en español suele abrir mejor el formato con punto y coma.")
    sep, dec = (",", ".") if sep_label.startswith("Coma") else (";", ",")
    base = _slug(p.name)

    sheets = result_sheets(r, cmp, sens, analysis.entropy, p.name)
    c2.markdown("**El libro Excel incluye las hojas:**")
    c2.markdown(" · ".join(sheets))

    st.subheader("Resultados completos")
    b1, b2, b3 = st.columns(3)
    b1.download_button(
        "Excel con todos los pasos", results_to_excel(r, cmp, sens, analysis.entropy, p.name),
        f"{base}_resultados.xlsx", EXCEL_MIME, type="primary", icon="📊", on_click="ignore", width="stretch",
    )
    b2.download_button(
        "ZIP con un CSV por tabla", results_to_csv_zip(r, cmp, sens, analysis.entropy, p.name, sep=sep, decimal=dec),
        f"{base}_resultados_csv.zip", "application/zip", icon="🗂️", on_click="ignore", width="stretch",
    )
    b3.download_button(
        "CSV de resultados finales", results_to_csv(r, cmp, sep=sep, decimal=dec),
        f"{base}_ranking.csv", "text/csv", icon="📄", on_click="ignore", width="stretch",
    )

    st.subheader("Matriz de datos del problema")
    st.caption("En el formato de importación del paso 1 (incluye filas Sentido y Peso), para retomar el problema más tarde.")
    args = (r.alternatives, r.criteria, r.matrix, r.directions, r.weights)
    b1, b2, _ = st.columns(3)
    b1.download_button("Problema (Excel)", problem_to_excel(*args), f"{base}_problema.xlsx", EXCEL_MIME,
                       icon="📥", on_click="ignore", width="stretch")
    b2.download_button("Problema (CSV)", problem_to_csv(*args, sep=sep, decimal=dec), f"{base}_problema.csv",
                       "text/csv", icon="📥", on_click="ignore", width="stretch")

    with st.expander("Vista previa de las tablas exportadas"):
        name = st.selectbox("Tabla", list(sheets))
        frame = sheets[name]
        if (frame.dtypes == object).any():  # columnas que mezclan texto y números
            frame = frame.astype(str)
        st.dataframe(frame, width="stretch")

    nav_buttons(state.STEPS[5])

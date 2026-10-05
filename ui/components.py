"""Componentes reutilizables de la interfaz."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from data_io.validators import ValidationReport

from .charts import PLOTLY_CONFIG
from .state import STEPS, Analysis, go_to

HIGHLIGHT = "background-color: rgba(42, 120, 214, 0.20); font-weight: 600;"


def md(text: str) -> str:
    """Escapa «$» para que Streamlit no interprete nombres como «Precio ($/u)» como LaTeX."""
    return str(text).replace("$", r"\$")


def decimals() -> int:
    return int(st.session_state.get("decimals", 4))


def show_report(report: ValidationReport, show_warnings: bool = True) -> None:
    for msg in report.errors:
        st.error(md(msg), icon="⛔")
    if show_warnings:
        for msg in report.warnings:
            st.warning(md(msg), icon="⚠️")


def styled(df: pd.DataFrame, highlight=None):
    """Formatea los números con la cantidad de decimales elegida.

    highlight: función ``Styler -> Styler`` opcional para resaltar celdas.
    """
    sty = df.style.format(precision=decimals(), na_rep="—", thousands="")
    if highlight is not None:
        sty = highlight(sty)
    return sty


def table(df: pd.DataFrame, highlight=None, **kwargs) -> None:
    st.dataframe(styled(df, highlight), **kwargs)


def chart(fig, key: str | None = None) -> None:
    st.plotly_chart(fig, theme=None, config=PLOTLY_CONFIG, key=key)


def nav_buttons(current: str) -> None:
    idx = STEPS.index(current)
    st.divider()
    left, _, right = st.columns([1, 2, 1])
    if idx > 0:
        left.button(f"← {STEPS[idx - 1]}", on_click=go_to, args=(STEPS[idx - 1],), width="stretch")
    if idx < len(STEPS) - 1:
        right.button(f"{STEPS[idx + 1]} →", on_click=go_to, args=(STEPS[idx + 1],), type="primary", width="stretch")


def require_results(analysis: Analysis) -> bool:
    """Muestra por qué no se puede calcular y ofrece volver a corregir los datos."""
    if analysis.ok:
        return True
    st.error("No es posible calcular los resultados hasta corregir los siguientes problemas:", icon="⛔")
    for msg in analysis.report.errors:
        st.markdown(f"- {md(msg)}")
    c1, c2, _ = st.columns([1, 1, 2])
    c1.button("Ir a 1 · Datos", on_click=go_to, args=(STEPS[0],))
    c2.button("Ir a 2 · Criterios y pesos", on_click=go_to, args=(STEPS[1],))
    return False

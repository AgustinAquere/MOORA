"""Paso 4: comparación de rankings y gráficos."""

from __future__ import annotations

import numpy as np
import streamlit as st

from engine import RATIO_SYSTEM, REFERENCE_POINT, spearman_label

from . import state
from .charts import contribution_chart, deviation_heatmap, score_bar, slope_chart
from .components import HIGHLIGHT, chart, md, decimals, nav_buttons, require_results, table


def render() -> None:
    p = state.get_problem()
    analysis = state.analyze(p)
    st.header("4 · Comparación y gráficos")
    if not require_results(analysis):
        nav_buttons(state.STEPS[3])
        return
    r, cmp = analysis.result, analysis.comparison
    d = decimals()

    # -- Indicador de coincidencia ------------------------------------------
    if cmp.winners_match:
        st.success(
            md(f"**Coinciden en la mejor alternativa:** {' / '.join(sorted(set(cmp.ratio_winners) & set(cmp.reference_winners)))}"),
            icon="✅",
        )
    else:
        st.warning(
            md(f"**Los métodos difieren en la mejor alternativa:** Sistema de Razones → **{' / '.join(cmp.ratio_winners)}**, "
               f"Punto de Referencia → **{' / '.join(cmp.reference_winners)}**"),
            icon="⚠️",
        )

    c1, c2, c3 = st.columns(3)
    rho = cmp.spearman
    c1.metric("Correlación de Spearman (ρ)", f"{rho:.4f}" if np.isfinite(rho) else "—", spearman_label(rho),
              delta_color="off", delta_arrow="off", border=True, help="ρ = 1: rankings idénticos; ρ = −1: rankings invertidos.")
    c2.metric("Posiciones coincidentes", f"{cmp.position_matches} de {r.m}", border=True)
    c3.metric("Mayor cambio de posición", f"{int(np.abs(cmp.table['Diferencia (PR − SR)']).max())} lugar(es)", border=True)

    # -- Tabla comparativa ----------------------------------------------------
    st.subheader("Tabla comparativa de rankings")
    view = cmp.table.copy()
    view["Coincide"] = view["Coincide"].map({True: "✔", False: "✘"})

    def _hl(sty):
        return sty.apply(lambda col: [HIGHLIGHT if v == 1 else "" for v in col], subset=["Posición SR", "Posición PR"])

    table(view.sort_values("Posición SR"), highlight=_hl, width="stretch")

    with st.container(border=True):
        st.markdown("**Interpretación**")
        for note in cmp.notes:
            st.markdown(f"- {md(note)}")

    # -- Gráficos ---------------------------------------------------------------
    st.subheader("Puntajes")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Sistema de Razones — y_i** (mayor es mejor)")
        chart(score_bar(r, RATIO_SYSTEM, d), key="bar_y")
    with c2:
        st.markdown("**Punto de Referencia — d_i** (menor es mejor)")
        chart(score_bar(r, REFERENCE_POINT, d), key="bar_d")

    st.subheader("Comparación de posiciones")
    st.caption("Cada línea une la posición de una alternativa en ambos métodos; las líneas cruzadas indican discrepancias.")
    chart(slope_chart(r), key="slope")

    st.subheader("¿Por qué gana cada alternativa?")
    t1, t2 = st.tabs(["Aportes al Sistema de Razones", "Desvíos respecto del punto de referencia"])
    with t1:
        st.caption(
            "Barras apiladas con el aporte ponderado w_j·x*_ij de cada criterio (beneficios a la derecha, costos a la "
            "izquierda). El rombo es el valor neto y_i. Muestra cómo las fortalezas compensan las debilidades."
        )
        chart(contribution_chart(r), key="contrib")
    with t2:
        st.caption(
            "Desvío ponderado w_j·|r_j − x*_ij| de cada alternativa respecto del ideal. El valor marcado en cada fila "
            "es el máximo (d_i): el Punto de Referencia solo mira ese peor desvío."
        )
        chart(deviation_heatmap(r, d), key="heatmap")

    nav_buttons(state.STEPS[3])

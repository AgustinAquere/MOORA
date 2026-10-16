"""Paso 3: resultados y pasos intermedios del cálculo."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from engine import LINEAR, LINEAR_SUM, LOGARITHMIC, VECTOR

from . import state
from .components import HIGHLIGHT, decimals, nav_buttons, require_results, show_report, table

NORMALIZATION_FORMULAS = {
    VECTOR: r"x^*_{ij} = \frac{x_{ij}}{\sqrt{\sum_{i=1}^{m} x_{ij}^2}}",
    LINEAR: r"x^*_{ij} = \frac{x_{ij}}{\max_i x_{ij}}",
    LINEAR_SUM: r"x^*_{ij} = \frac{x_{ij}}{\sum_{i=1}^{m} x_{ij}}",
    LOGARITHMIC: r"x^*_{ij} = \frac{\ln x_{ij}}{\ln \left( \prod_{i=1}^{m} x_{ij} \right)}",
}

DIVISOR_ROW = {
    VECTOR: "√Σ x²ᵢⱼ",
    LINEAR: "max xᵢⱼ",
    LINEAR_SUM: "Σ xᵢⱼ",
    LOGARITHMIC: "ln Π xᵢⱼ",
}


def _normalization_changed() -> None:
    state.get_problem().normalization = st.session_state["normalization_input"]


def _highlight_rank1(sty):
    return sty.apply(
        lambda col: [HIGHLIGHT if v == 1 else "" for v in col], subset=["Posición"]
    )


def render() -> None:
    p = state.get_problem()
    ss = st.session_state
    st.header("3 · Resultados paso a paso")
    # Se sincroniza siempre desde el problema: Streamlit descarta el estado del widget al cambiar de paso.
    ss["normalization_input"] = p.normalization
    st.selectbox("Método de normalización", state.NORMALIZATIONS, key="normalization_input",
                 on_change=_normalization_changed,
                 help="Por defecto se usa la normalización vectorial, la propia de MOORA. El método elegido se "
                      "aplica también a la comparación, la sensibilidad y la exportación.")
    analysis = state.analyze(p)
    if not require_results(analysis):
        nav_buttons(state.STEPS[2])
        return
    r = analysis.result
    show_report(analysis.report)
    d = decimals()

    # -- Resumen ------------------------------------------------------------
    cmp = analysis.comparison
    c1, c2 = st.columns(2)
    c1.metric("Mejor según Sistema de Razones", " / ".join(cmp.ratio_winners),
              f"y = {r.ratio_scores[r.ratio_winners[0]]:.{d}f}", delta_color="off", delta_arrow="off", border=True)
    c2.metric("Mejor según Punto de Referencia", " / ".join(cmp.reference_winners),
              f"d = {r.reference_scores[r.reference_winners[0]]:.{d}f}", delta_color="off", delta_arrow="off", border=True)

    # -- 1. Matriz original -------------------------------------------------
    st.subheader("Paso 1 · Matriz de decisión original")
    st.latex(r"X = [x_{ij}]_{m \times n} \qquad m = %d \text{ alternativas},\; n = %d \text{ criterios}" % (r.m, r.n))
    st.dataframe(r.decision_frame().style.format("{:.10g}"), width="stretch")
    meta = pd.DataFrame(
        [r.directions, [f"{w:.{d}f}" for w in r.weights]],
        index=pd.Index(["Sentido", "Peso w_j"], name=""),
        columns=r.criteria,
    )
    st.dataframe(meta, width="stretch")

    # -- 2. Normalización ---------------------------------------------------
    st.subheader(f"Paso 2 · {r.normalization}")
    st.latex(NORMALIZATION_FORMULAS[r.normalization])
    st.caption("La misma fórmula se aplica a criterios de beneficio y de costo: el sentido se considera al agregar "
               "(los costos restan en el Sistema de Razones y toman el mínimo como referencia).")
    norms = pd.DataFrame([r.norms], index=pd.Index([DIVISOR_ROW[r.normalization]], name=""), columns=r.criteria)
    table(norms, width="stretch")
    table(r.normalized_frame(), width="stretch")

    # -- 3. Ponderación -----------------------------------------------------
    st.subheader("Paso 3 · Matriz normalizada ponderada")
    st.latex(r"v_{ij} = w_j \cdot x^*_{ij}")
    table(r.weighted_frame(), width="stretch")

    # -- 4. Sistema de Razones ----------------------------------------------
    st.subheader("Paso 4 · MOORA – Sistema de Razones")
    st.latex(r"y_i = \sum_{j \in Max} w_j\, x^*_{ij} \;-\; \sum_{j \in Min} w_j\, x^*_{ij}"
             r"\qquad \text{(mayor } y_i \text{ es mejor)}")
    st.caption("Las columnas de criterios muestran el aporte con signo: positivo si es beneficio, negativo si es costo.")
    table(r.ratio_frame(), highlight=_highlight_rank1, width="stretch")

    # -- 5. Punto de referencia ---------------------------------------------
    st.subheader("Paso 5 · Punto de referencia")
    st.latex(r"r_j = \max_i x^*_{ij} \;\;(\text{beneficio}) \qquad r_j = \min_i x^*_{ij} \;\;(\text{costo})")
    table(r.reference_frame(), width="stretch")

    # -- 6. Desviaciones ----------------------------------------------------
    st.subheader("Paso 6 · Matriz de desviaciones")
    st.latex(r"\left| r_j - x^*_{ij} \right|")
    table(r.deviations_frame(), width="stretch")

    st.subheader("Paso 7 · Desviaciones ponderadas y métrica de Tchebycheff")
    st.latex(r"d_i = \max_j \left\{ w_j \left| r_j - x^*_{ij} \right| \right\}"
             r"\qquad \text{(menor } d_i \text{ es mejor)}")
    st.caption("En cada fila se resalta el desvío máximo, que define d_i (criterio crítico de la alternativa).")
    criteria = r.criteria

    def _highlight_dev(sty):
        sty = sty.apply(
            lambda row: [HIGHLIGHT if v == row[criteria].max() else "" for v in row[criteria]],
            axis=1, subset=criteria,
        )
        return _highlight_rank1(sty)

    table(r.weighted_deviations_frame(), highlight=_highlight_dev, width="stretch")

    # -- 8. Resultados finales ----------------------------------------------
    st.subheader("Resultados finales")
    final = r.results_frame()

    def _highlight_final(sty):
        return sty.apply(lambda col: [HIGHLIGHT if v == 1 else "" for v in col], subset=["Posición SR", "Posición PR"])

    table(final, highlight=_highlight_final, width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Ranking – Sistema de Razones** (y_i descendente)")
        st.dataframe(final.sort_values(["Posición SR", "y_i"], ascending=[True, False])[["Posición SR", "y_i"]]
                     .style.format(precision=d), width="stretch")
    with c2:
        st.markdown("**Ranking – Punto de Referencia** (d_i ascendente)")
        st.dataframe(final.sort_values(["Posición PR", "d_i"])[["Posición PR", "d_i"]].style.format(precision=d),
                     width="stretch")

    nav_buttons(state.STEPS[2])

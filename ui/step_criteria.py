"""Paso 2: configuración de criterios (nombre, sentido) y pesos."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from data_io.validators import DIRECTIONS, ValidationReport, unique_labels, validate_directions, validate_names, validate_weights

from . import state
from .charts import weights_bar
from .components import chart, nav_buttons, show_report, table

METHOD_HELP = {
    state.DIRECT: "El decisor asigna los pesos. Si no suman 1, se normalizan automáticamente: "
                  r"$w_j \leftarrow w_j / \sum_k w_k$.",
    state.EQUAL: r"Todos los criterios tienen la misma importancia: $w_j = 1/n$.",
    state.ENTROPY: "Método objetivo: un criterio pesa más cuanto más dispersos son sus valores entre las "
                   r"alternativas. $p_{ij} = x_{ij}/\sum_i x_{ij}$, "
                   r"$E_j = -\frac{1}{\ln m}\sum_i p_{ij}\ln p_{ij}$, "
                   r"$w_j = \frac{1-E_j}{\sum_k (1-E_k)}$.",
}


def _method_changed() -> None:
    state.get_problem().weight_method = st.session_state["weight_method_input"]
    state.refresh_editors()


def render() -> None:
    p = state.get_problem()
    ss = st.session_state
    st.header("2 · Criterios y pesos")
    st.caption("Asigne a cada criterio su nombre, su sentido (Beneficio = maximizar, Costo = minimizar) y su peso.")

    ss.setdefault("weight_method_input", p.weight_method)
    st.radio("Método de asignación de pesos", state.WEIGHT_METHODS, key="weight_method_input",
             horizontal=True, on_change=_method_changed)
    st.markdown(METHOD_HELP[p.weight_method])

    direct = p.weight_method == state.DIRECT
    column_config = {
        "Criterio": st.column_config.TextColumn("Criterio", required=True, width="large"),
        "Sentido": st.column_config.SelectboxColumn("Sentido", options=list(DIRECTIONS), required=True),
        "Peso": st.column_config.NumberColumn("Peso asignado", format="%.4f",
                                              help="Puede ingresar valores que no sumen 1 (p. ej. 35, 30, 15, 20)."),
    }
    edited = st.data_editor(
        ss["criteria_snapshot"],
        key=f"criteria_editor_{ss['nonce']}_{p.weight_method}",
        hide_index=True,
        num_rows="fixed",
        column_config=column_config,
        column_order=["Criterio", "Sentido", "Peso"] if direct else ["Criterio", "Sentido"],
        width="stretch",
    )
    state.apply_criteria_edit(p, edited, include_weights=direct)
    analysis = state.analyze(p)  # después de aplicar la edición, para que los pesos no queden desfasados

    # Validaciones propias de este paso (la matriz se valida en el paso 1).
    report = ValidationReport()
    report.merge(validate_names(p.criteria, "criterio"))
    labels = unique_labels(p.criteria, "C")
    report.merge(validate_directions(p.directions, labels)[0])
    if direct:
        w_report, _ = validate_weights(p.weights, labels)
        report.merge(w_report)
        valid = [w for w in p.weights if w is not None and np.isfinite(w)]
        st.metric("Suma de los pesos ingresados", f"{sum(valid):.4f}")
    for msg in analysis.weight_messages:
        st.info(msg, icon="ℹ️")
    entropy_errors = [e for e in analysis.report.errors if e.startswith("Método de entropía")]
    report.errors.extend(entropy_errors)
    show_report(report)

    if analysis.weights_used is not None:
        st.subheader("Pesos utilizados en el cálculo")
        w = analysis.weights_used
        c1, c2 = st.columns([1, 1.3])
        with c1:
            df = pd.DataFrame(
                {"Sentido": p.directions, "Peso (w_j)": w, "Peso (%)": w * 100},
                index=pd.Index(labels, name="Criterio"),
            )
            table(df, width="stretch")
            st.caption(f"Σ w_j = {w.sum():.6f}")
        with c2:
            chart(weights_bar(labels, w), key="weights_chart")

    if analysis.entropy is not None:
        with st.expander("Pasos intermedios del método de entropía", expanded=p.weight_method == state.ENTROPY):
            ent = analysis.entropy
            st.markdown("**Matriz de proporciones** $p_{ij} = x_{ij} / \\sum_i x_{ij}$")
            table(pd.DataFrame(ent.proportions, index=unique_labels(p.alternatives, "A"), columns=labels), width="stretch")
            st.markdown("**Entropía, diversificación y pesos**")
            table(
                pd.DataFrame(
                    {"E_j (entropía)": ent.entropy, "d_j = 1 − E_j": ent.divergence, "w_j": ent.weights},
                    index=pd.Index(labels, name="Criterio"),
                ),
                width="stretch",
            )

    nav_buttons(state.STEPS[1])

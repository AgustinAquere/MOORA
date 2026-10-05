"""Paso 5: análisis de sensibilidad respecto del peso de un criterio."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from engine import RATIO_SYSTEM, REFERENCE_POINT, redistribute_weights, sensitivity_analysis, solve, stability_table

from . import state
from .charts import sensitivity_chart
from .components import chart, md, nav_buttons, require_results, table
from .theme import mode


def run_sensitivity(analysis: state.Analysis, cfg: dict):
    inp = analysis.inputs
    return sensitivity_analysis(
        inp.matrix, inp.weights, inp.is_benefit, cfg["criterion"], cfg["w_min"], cfg["w_max"], cfg["steps"],
        alternatives=inp.alternatives, criteria=inp.criteria,
    )


def _interval_text(interval) -> str:
    if interval is None:
        return "el peso actual está fuera del rango analizado"
    lo, hi = interval
    return f"w ∈ [{lo:.4f}, {hi:.4f}]"


def render() -> None:
    p = state.get_problem()
    analysis = state.analyze(p)
    st.header("5 · Análisis de sensibilidad")
    if not require_results(analysis):
        nav_buttons(state.STEPS[4])
        return
    r, inp = analysis.result, analysis.inputs
    if r.n < 2:
        st.info("El análisis de sensibilidad de pesos requiere al menos 2 criterios.", icon="ℹ️")
        nav_buttons(state.STEPS[4])
        return
    theme = mode()

    st.markdown(
        "Se varía el peso $w_k$ de un criterio y los demás se renormalizan proporcionalmente "
        r"para que sigan sumando 1: $\;w_j' = w_j \cdot \dfrac{1 - w_k'}{1 - w_k}$."
    )

    # -- Controles --------------------------------------------------------------
    c1, c2, c3 = st.columns([1.4, 1.6, 1])
    k = c1.selectbox("Criterio a variar", range(r.n), format_func=lambda j: f"{r.criteria[j]} (w = {r.weights[j]:.4f})",
                     key="sens_criterion")
    w_min, w_max = c2.slider("Rango del peso", 0.0, 1.0, (0.0, 1.0), step=0.01, key="sens_range")
    steps = c3.number_input("Puntos de la grilla", min_value=11, max_value=1001, value=201, step=10, key="sens_steps")
    if w_max - w_min < 1e-9:
        st.warning("Elija un rango de ancho mayor que 0.", icon="⚠️")
        nav_buttons(state.STEPS[4])
        return
    cfg = {"criterion": int(k), "w_min": float(w_min), "w_max": float(w_max), "steps": int(steps)}
    st.session_state["sensitivity_cfg"] = cfg  # para incluirlo en la exportación

    try:
        sens = run_sensitivity(analysis, cfg)
    except ValueError as exc:
        st.error(md(str(exc)), icon="⛔")
        nav_buttons(state.STEPS[4])
        return

    # -- Resumen de estabilidad --------------------------------------------------
    st.subheader(md(f"Estabilidad frente al peso de «{r.criteria[k]}»"))
    cols = st.columns(2)
    for col, method, winners in ((cols[0], RATIO_SYSTEM, r.ratio_winners), (cols[1], REFERENCE_POINT, r.reference_winners)):
        n_changes = int((sens.change_points["Método"] == method).sum())
        name = " / ".join(r.alternatives[i] for i in winners)
        with col.container(border=True):
            st.markdown(f"**{method}**")
            st.markdown(md(f"Mejor actual: **{name}** — se mantiene para {_interval_text(sens.stability_interval(method))}"))
            if n_changes == 0:
                st.markdown("✅ La mejor alternativa **no cambia** en todo el rango analizado.")
            else:
                st.markdown(f"🔁 La mejor alternativa cambia **{n_changes}** vez/veces en el rango analizado.")

    if not sens.change_points.empty:
        st.markdown("**Puntos de cambio de la mejor alternativa** (refinados por bisección)")
        table(sens.change_points, hide_index=True, width="stretch")

    # -- Gráficos ---------------------------------------------------------------
    metric = st.segmented_control("Mostrar", ["Puntaje", "Posición"], default="Puntaje", key="sens_metric") or "Puntaje"
    key_metric = "score" if metric == "Puntaje" else "rank"
    t1, t2 = st.tabs([RATIO_SYSTEM, REFERENCE_POINT])
    with t1:
        chart(sensitivity_chart(sens, RATIO_SYSTEM, key_metric, theme), key="sens_sr")
    with t2:
        chart(sensitivity_chart(sens, REFERENCE_POINT, key_metric, theme), key="sens_pr")
    st.caption("Línea vertical continua: peso actual. Líneas punteadas: valores de peso donde cambia la mejor alternativa.")

    # -- Verificación puntual ---------------------------------------------------
    with st.expander("Calcular para un peso puntual (verificación manual)"):
        t = st.number_input(md(f"Peso de «{r.criteria[k]}»"), 0.0, 1.0, float(r.weights[k]), step=0.01, format="%.4f",
                            key="sens_point")
        w_new = redistribute_weights(inp.weights, k, t)
        res = solve(inp.matrix, w_new, inp.is_benefit, inp.alternatives, inp.criteria)
        table(pd.DataFrame({"Peso original": inp.weights, "Peso recalculado": w_new},
                           index=pd.Index(inp.criteria, name="Criterio")).T, width="stretch")
        table(res.results_frame(), width="stretch")

    # -- Robustez frente a todos los criterios ------------------------------------
    with st.expander("Robustez de la decisión frente a cada criterio"):
        st.caption(
            "Para cada criterio, intervalo de su peso en [0, 1] en el que la mejor alternativa actual no cambia "
            "(los demás pesos se renormalizan). Un intervalo angosto indica un criterio determinante."
        )
        stab = stability_table(inp.matrix, inp.weights, inp.is_benefit, inp.criteria, inp.alternatives, steps=201)
        table(stab, width="stretch")

    nav_buttons(state.STEPS[4])

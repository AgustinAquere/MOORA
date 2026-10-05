"""Aplicación Streamlit: MOORA y MOORA con Punto de Referencia.

Ejecutar con:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="MOORA · Decisión multicriterio", page_icon="📊", layout="wide")

from ui import state  # noqa: E402  (set_page_config debe ser la primera llamada)
from ui.components import md  # noqa: E402
from ui import step_compare, step_criteria, step_data, step_export, step_results, step_sensitivity  # noqa: E402

PAGES = dict(
    zip(
        state.STEPS,
        [step_data.render, step_criteria.render, step_results.render,
         step_compare.render, step_sensitivity.render, step_export.render],
    )
)


def sidebar_navigation() -> None:
    with st.sidebar:
        st.title("📊 MOORA")
        st.caption("Sistema de Razones y Punto de Referencia")
        st.radio("Pasos", state.STEPS, key="step", on_change=state.refresh_editors, label_visibility="collapsed")


def sidebar_summary() -> None:
    p = state.get_problem()
    analysis = state.analyze(p)
    with st.sidebar:
        st.divider()
        st.markdown(md(f"**{p.name or 'Problema sin nombre'}**"))
        st.caption(f"{p.m} alternativas × {p.n} criterios · pesos: {p.weight_method.lower()}")
        if analysis.ok:
            cmp = analysis.comparison
            st.markdown(md(f"🥇 SR: **{' / '.join(cmp.ratio_winners)}**  \n🥇 PR: **{' / '.join(cmp.reference_winners)}**"))
            if cmp.winners_match:
                st.caption("✅ Ambos métodos coinciden en la mejor alternativa.")
            else:
                st.caption("⚠️ Los métodos difieren en la mejor alternativa.")
        else:
            st.caption(f"⛔ {len(analysis.report.errors)} problema(s) por corregir antes de calcular.")
        st.divider()
        st.number_input("Decimales a mostrar", min_value=2, max_value=10, step=1, key="decimals")
        with st.expander("Acerca de"):
            st.markdown(
                "Herramienta de apoyo a la decisión multicriterio basada en **MOORA** "
                "(Brauers y Zavadskas, 2006): Sistema de Razones (compensatorio) y Punto de Referencia "
                "con métrica min-max de Tchebycheff (no compensatorio).\n\n"
                "Decisiones en Escenarios Complejos — Trabajo Práctico."
            )


def main() -> None:
    state.init_state()
    sidebar_navigation()
    PAGES[st.session_state["step"]]()
    sidebar_summary()


main()

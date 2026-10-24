"""Paso 5: análisis de sensibilidad respecto del peso de un criterio."""

from __future__ import annotations

import streamlit as st

from engine import RATIO_SYSTEM, REFERENCE_POINT, redistribute_weights, sensitivity_analysis, solve

from . import state
from .charts import rank_heatmap, stability_line_chart
from .components import Cell, chart, decimals, live_table, md, nav_buttons, require_results


def run_sensitivity(analysis: state.Analysis, cfg: dict):
    inp = analysis.inputs
    return sensitivity_analysis(
        inp.matrix, inp.weights, inp.is_benefit, cfg["criterion"], cfg["w_min"], cfg["w_max"], cfg["steps"],
        alternatives=inp.alternatives, criteria=inp.criteria, normalization=analysis.result.normalization,
    )


#: Diferencias de peso menores que esto se consideran «sin cambios» (errores de redondeo de punto flotante).
_SAME_WEIGHT = 1e-9
LINE_VIEW = "Estabilidad (líneas)"
HEATMAP_VIEW = "Heatmap"
RELATIVE_SCALE = "Relativa al promedio"
ABSOLUTE_SCALE = "Puntaje absoluto"


def _set_weight(vkey: str, ckey: str, value: float) -> None:
    """Guarda el peso simulado y cambia la versión de los controles.

    El peso vive en una clave propia (no de un widget). Con cada cambio, el deslizador y el campo
    numérico se recrean con claves nuevas: si se hace clic rápido en − / +, el navegador puede
    reenviar el valor viejo de un control que todavía no se actualizó, y eso pisaría el peso
    (redondeado a los 2 decimales del deslizador). Con claves nuevas esos valores viejos se descartan.
    """
    st.session_state[vkey] = min(1.0, max(0.0, round(float(value), 12)))
    st.session_state[ckey] = st.session_state.get(ckey, 0) + 1


def _from_widget(vkey: str, ckey: str, wkey: str) -> None:
    _set_weight(vkey, ckey, st.session_state[wkey])


def _nudge_weight(vkey: str, ckey: str, delta: float) -> None:
    # Suma el paso exacto. Los botones propios de st.number_input redondean antes el valor a los
    # decimales del paso (con paso 0,1: 0,35 → 0,4 + 0,1 = 0,5), por eso se ocultan.
    _set_weight(vkey, ckey, st.session_state[vkey] + delta)


#: Oculta los botones − / + nativos del campo «Valor exacto» (ver ``_nudge_weight``).
_HIDE_NATIVE_STEPS = """
<style>
.st-key-point_exact [data-testid="stNumberInputStepUp"],
.st-key-point_exact [data-testid="stNumberInputStepDown"] { display: none; }
</style>
"""


def _names(alternatives, ranks) -> str:
    return " / ".join(a for a, rk in zip(alternatives, ranks) if rk == 1)


def _delta_cell(delta: float, d: int) -> Cell:
    if abs(delta) < 0.5 * 10 ** -d:
        return Cell("—", "num muted")
    return Cell(f"{'▲' if delta > 0 else '▼'} {delta:+.{d}f}", f"num {'up' if delta > 0 else 'down'}")


def _rank_cell(old: int, new: int) -> Cell:
    best = " best" if new == 1 else ""
    if old == new:
        return Cell(f"{new}°", "num" + best)
    arrow = "▲" if new < old else "▼"
    return Cell(f"{old}° → {new}° {arrow}", f"num {'up' if new < old else 'down'}{best}")


def point_simulation(analysis: state.Analysis) -> None:
    """Simula un peso puntual para el criterio elegido y compara contra los pesos originales."""
    ss = st.session_state
    r, inp = analysis.result, analysis.inputs
    d = decimals()
    st.subheader("Simulación con un peso puntual")
    st.caption("Elija un criterio y asígnele un peso. Los demás se renormalizan proporcionalmente y se recalculan "
               "ambos métodos. Las celdas que cambian se resaltan en verde por un instante.")

    c1, c2, c3, c4, c5, c6 = st.columns([1.3, 1.5, 0.8, 0.5, 0.6, 0.8], vertical_alignment="bottom")
    k = c1.selectbox("Criterio a modificar", range(r.n), key="point_criterion",
                     format_func=lambda j: f"{r.criteria[j]} (w = {r.weights[j]:.4f})")
    cfg = {"criterion": int(k), "w_min": 0.0, "w_max": 1.0, "steps": 201}
    ss["sensitivity_cfg"] = cfg  # para incluirlo en la exportación
    base = float(r.weights[k])
    # Las claves incluyen el peso original: si cambian los pesos del problema, el peso simulado vuelve al nuevo valor.
    # El peso se guarda en «vkey»; el deslizador (paso 0,01) y el campo numérico se recrean en cada cambio (ver _set_weight).
    vkey, ckey = f"point_w_{k}_{base:.8f}", f"point_wv_{k}_{base:.8f}"
    if vkey not in ss:
        ss[vkey] = base
    t = float(ss[vkey])
    version = ss.get(ckey, 0)
    skey, nkey = f"{vkey}_slider_{version}", f"{vkey}_exact_{version}"
    if skey not in ss:
        ss[skey] = round(t, 2)
    if nkey not in ss:
        ss[nkey] = t
    c2.slider(md(f"Peso simulado de «{r.criteria[k]}»"), 0.0, 1.0, step=0.01, format="%.2f", key=skey,
              on_change=_from_widget, args=(vkey, ckey, skey))
    # Paso de los botones − / +: de 0,1 hasta la cantidad de «Decimales a mostrar».
    steps = [round(10.0 ** -i, i) for i in range(1, d + 1)]
    if ss.get("point_step") not in steps:
        ss["point_step"] = 0.01
    step = c5.selectbox("Paso", steps, key="point_step", format_func=lambda v: f"{v:.{len(steps)}f}".rstrip("0"),
                        help="Cuánto suman o restan los botones − / + del valor exacto. Las opciones dependen de "
                             "«Decimales a mostrar».")
    st.html(_HIDE_NATIVE_STEPS)
    with c3.container(key="point_exact"):
        st.number_input("Valor exacto", 0.0, 1.0, step=10.0 ** -d, format=f"%.{d}f", key=nkey,
                        on_change=_from_widget, args=(vkey, ckey, nkey))
    minus, plus = c4.columns(2, gap="small")
    minus.button("−", on_click=_nudge_weight, args=(vkey, ckey, -step), disabled=t <= 0.0, width="stretch",
                 key="point_minus", help="Resta el paso elegido.")
    plus.button("+", on_click=_nudge_weight, args=(vkey, ckey, step), disabled=t >= 1.0, width="stretch",
                key="point_plus", help="Suma el paso elegido.")
    unchanged = abs(t - base) < _SAME_WEIGHT
    c6.button("↺ Restablecer", on_click=_set_weight, args=(vkey, ckey, base), disabled=unchanged,
              width="stretch", help="Vuelve al peso original del criterio.")
    t = base if unchanged else t
    w_new = r.weights.copy() if unchanged else redistribute_weights(r.weights, k, t)
    res = solve(inp.matrix, w_new, inp.is_benefit, inp.alternatives, inp.criteria, normalization=r.normalization)

    # -- Resumen ----------------------------------------------------------------
    m1, m2, m3 = st.columns(3)
    m1.metric(md(f"Peso de «{r.criteria[k]}»"), f"{t:.{d}f}",
              "sin cambios" if unchanged else f"{t - base:+.{d}f} respecto de {base:.{d}f}",
              delta_color="off" if unchanged else "normal", delta_arrow="off" if unchanged else "auto", border=True)
    for col, method, old_ranks, new_ranks in ((m2, RATIO_SYSTEM, r.ratio_ranks, res.ratio_ranks),
                                              (m3, REFERENCE_POINT, r.reference_ranks, res.reference_ranks)):
        old, new = _names(r.alternatives, old_ranks), _names(r.alternatives, new_ranks)
        same = old == new
        col.metric(f"Mejor según {method}", new, "se mantiene" if same else f"antes: {old}",
                   delta_color="off" if same else "inverse", delta_arrow="off", border=True)

    # -- Tablas -----------------------------------------------------------------
    st.markdown("**Pesos de los criterios**")
    rows = [
        [Cell(c), Cell(direction, "muted", track=False), Cell(f"{w0:.{d}f}", "num", track=False),
         Cell(f"{w1:.{d}f}", "num", bar=w1), _delta_cell(w1 - w0, d)]
        for c, direction, w0, w1 in zip(r.criteria, r.directions, r.weights, w_new)
    ]
    rows.append([Cell("Total", "muted"), Cell(""), Cell(f"{r.weights.sum():.{d}f}", "num muted", track=False),
                 Cell(f"{w_new.sum():.{d}f}", "num muted"), Cell("")])
    live_table("point_weights", ["Criterio", "Sentido", "Original", "Simulado", "Variación"], rows,
               edited_rows=(k,))
    if base < 1:
        st.caption(md(f"Fila marcada: criterio modificado. Los demás pesos se multiplican por "
                      f"(1 − {t:.{d}f}) / (1 − {base:.{d}f}) = {(1 - t) / (1 - base):.{d}f}, "
                      f"así que conservan sus proporciones."))
    else:
        st.caption("Fila marcada: criterio modificado. Como tenía todo el peso, el resto se reparte en partes iguales.")

    st.markdown("**Resultados recalculados**")
    rows = []
    for i, alt in enumerate(r.alternatives):
        rows.append([
            Cell(alt),
            Cell(f"{r.ratio_scores[i]:.{d}f}", "num muted", track=False),
            Cell(f"{res.ratio_scores[i]:.{d}f}", "num", title=f"Δ = {res.ratio_scores[i] - r.ratio_scores[i]:+.6f}"),
            _rank_cell(int(r.ratio_ranks[i]), int(res.ratio_ranks[i])),
            Cell(f"{r.reference_scores[i]:.{d}f}", "num muted", track=False),
            Cell(f"{res.reference_scores[i]:.{d}f}", "num",
                 title=f"Δ = {res.reference_scores[i] - r.reference_scores[i]:+.6f}"),
            _rank_cell(int(r.reference_ranks[i]), int(res.reference_ranks[i])),
        ])
    live_table("point_results",
               ["Alternativa", "Original", "Simulado", "Posición", "Original", "Simulado", "Posición"],
               rows, groups=[("", 1), ("Sistema de Razones · yᵢ (mayor es mejor)", 3),
                             ("Punto de Referencia · dᵢ (menor es mejor)", 3)],
               separators=(1, 4))
    st.caption("Posición: «anterior → nueva». ▲ sube en el ranking, ▼ baja. En azul, la mejor de cada método.")

    with st.expander("Matriz normalizada ponderada simulada  v′ᵢⱼ = w′ⱼ · x*ᵢⱼ"):
        rows = [
            [Cell(alt)] + [Cell(f"{res.weighted[i, j]:.{d}f}", "num", title=f"original: {r.weighted[i, j]:.{d}f}")
                           for j in range(r.n)]
            for i, alt in enumerate(r.alternatives)
        ]
        live_table("point_weighted", ["Alternativa", *r.criteria], rows)
        st.caption("Pase el cursor sobre una celda para ver su valor con los pesos originales.")

    # -- Gráficos ---------------------------------------------------------------
    g1, g2, g3 = st.columns(3)
    view = g1.segmented_control("Gráfico", [LINE_VIEW, HEATMAP_VIEW], default=LINE_VIEW, key="point_view") or LINE_VIEW
    method = g2.segmented_control("Método", [RATIO_SYSTEM, REFERENCE_POINT], default=RATIO_SYSTEM,
                                  key="point_method") or RATIO_SYSTEM
    if view == LINE_VIEW:
        scale = g3.segmented_control(
            "Escala", [RELATIVE_SCALE, ABSOLUTE_SCALE], default=RELATIVE_SCALE, key="point_scale",
            help="Relativa: a cada puntaje se le resta el promedio de las alternativas para ese peso. Separa las "
                 "líneas sin cambiar el orden ni la ubicación de los cruces.",
        ) or RELATIVE_SCALE
        relative = scale == RELATIVE_SCALE
        sens = run_sensitivity(analysis, cfg)
        chart(stability_line_chart(sens, method, t, relative=relative), key="point_line")
        st.caption(("Diferencia entre el puntaje de cada alternativa y el promedio de todas, para cada peso del "
                    "criterio. " if relative else "Puntaje de cada alternativa según el peso del criterio. ")
                   + "Los círculos marcan los cruces en los que otra alternativa pasa al 1° lugar. Línea continua: "
                     "peso original; línea verde a trazos: peso simulado.")
    else:
        sens = sensitivity_analysis(inp.matrix, r.weights, inp.is_benefit, k, 0.0, 1.0, 21, include_base=False,
                                    alternatives=inp.alternatives, criteria=inp.criteria,
                                    normalization=r.normalization)
        chart(rank_heatmap(sens, method, t), key="point_heat")
        st.caption("Posición de cada alternativa (filas) para pesos de 0 a 1 en pasos de 0,05 (columnas). "
                   "Cuanto más intenso el color, mejor la posición.")


def render() -> None:
    p = state.get_problem()
    analysis = state.analyze(p)
    st.header("5 · Análisis de sensibilidad")
    if not require_results(analysis):
        nav_buttons(state.STEPS[4])
        return
    r = analysis.result
    if r.n < 2:
        st.info("El análisis de sensibilidad de pesos requiere al menos 2 criterios.", icon="ℹ️")
        nav_buttons(state.STEPS[4])
        return

    point_simulation(analysis)

    nav_buttons(state.STEPS[4])

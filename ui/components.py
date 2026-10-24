"""Componentes reutilizables de la interfaz."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape

import pandas as pd
import streamlit as st

from data_io.validators import ValidationReport

from .charts import PLOTLY_CONFIG
from .state import STEPS, Analysis, go_to

HIGHLIGHT = "background-color: rgba(82, 102, 224, 0.22); font-weight: 600;"


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


@dataclass(frozen=True)
class Cell:
    """Celda de ``live_table``.

    kind: clases separadas por espacio: ``num`` (alineada a la derecha), ``best``
    (resaltada como mejor), ``up`` / ``down`` (variación), ``muted``.
    bar: fracción 0–1 para dibujar una barra de fondo (p. ej. un peso).
    track: si es False la celda nunca destella (valores fijos de referencia).
    """

    text: str
    kind: str = ""
    title: str = ""
    bar: float | None = None
    track: bool = True


_LIVE_TABLE_CSS = """
<style>
.mt-wrap { overflow-x: auto; margin: 0.25rem 0 1rem; }
.mt { border-collapse: separate; border-spacing: 0; width: 100%; font-size: 0.9rem;
      font-variant-numeric: tabular-nums; }
.mt th, .mt td { padding: 0.36rem 0.55rem; border-bottom: 1px solid rgba(128, 128, 128, 0.22);
                 white-space: nowrap; text-align: left; }
.mt thead th { background: rgba(128, 128, 128, 0.12); font-weight: 600; font-size: 0.82rem; }
.mt thead tr.mt-groups th { text-align: center; font-size: 0.78rem; letter-spacing: 0.02em; opacity: 0.85; }
.mt thead tr.mt-groups th.mt-g { border-left: 2px solid rgba(128, 128, 128, 0.3); }
.mt td.mt-sep, .mt th.mt-sep { border-left: 2px solid rgba(128, 128, 128, 0.3); }
.mt td.num, .mt th.num { text-align: right; }
.mt td.best { background-color: rgba(82, 102, 224, 0.22); font-weight: 600; }
.mt td.up { color: #1baf7a; font-weight: 600; }
.mt td.down { color: #e34948; font-weight: 600; }
.mt td.muted { opacity: 0.6; }
.mt tr.mt-edited td { font-weight: 600; }
.mt tr.mt-edited td:first-child { box-shadow: inset 3px 0 0 #5266e0; }
.mt td.flash { animation: mt-flash 1.6s ease-out; }
@keyframes mt-flash {
  from { background-color: rgba(27, 175, 122, 0.6); box-shadow: inset 0 0 0 1px rgba(27, 175, 122, 0.95); }
}
@media (prefers-reduced-motion: reduce) { .mt td.flash { animation-duration: 0.6s; } }
</style>
"""


def live_table(key: str, header: list[str], rows: list[list[Cell]], *, groups=None, separators=(),
               edited_rows=()) -> None:
    """Tabla HTML cuyas celdas destellan en verde cuando su valor cambia respecto de la
    ejecución anterior (``st.dataframe`` dibuja en un canvas y no admite animar celdas).

    groups: lista opcional de ``(etiqueta, cantidad_de_columnas)`` para una fila de encabezado superior.
    separators: índices de columna que llevan una línea divisoria a la izquierda.
    edited_rows: índices de fila a destacar (borde lateral y negrita).
    """
    # Se compara contra la última vista con los mismos decimales: cambiar «Decimales a mostrar» no es un cambio de valor.
    store = f"_live_table_{key}_{decimals()}"
    prev = st.session_state.get(store, {})
    cur = {}
    head = ""
    if groups:
        cells, col = [], 0
        for label, span in groups:
            cls = "mt-g" if col in separators else ""
            cells.append(f'<th colspan="{span}" class="{cls}">{escape(label)}</th>')
            col += span
        head += f'<tr class="mt-groups">{"".join(cells)}</tr>'
    num_cols = {c for c, cell in enumerate(rows[0]) if "num" in cell.kind.split()} if rows else set()
    head += "<tr>" + "".join(
        f'<th class="{"num" if c in num_cols else ""} {"mt-sep" if c in separators else ""}">{escape(h)}</th>'
        for c, h in enumerate(header)
    ) + "</tr>"
    body = []
    for r, row in enumerate(rows):
        row_id = row[0].text
        tds = []
        for c, cell in enumerate(row):
            cid = f"{row_id}\x1f{c}"
            cur[cid] = cell.text
            classes = cell.kind.split()
            if c in separators:
                classes.append("mt-sep")
            if cell.track and cid in prev and prev[cid] != cell.text:
                classes.append("flash")
            style = ""
            if cell.bar is not None:
                pct = 100 * min(max(cell.bar, 0.0), 1.0)
                style = (f' style="background-image: linear-gradient(90deg, rgba(82, 102, 224, 0.28) {pct:.2f}%, '
                         f'transparent {pct:.2f}%)"')
            title = f' title="{escape(cell.title)}"' if cell.title else ""
            tds.append(f'<td class="{" ".join(classes)}"{style}{title}>{escape(cell.text)}</td>')
        row_cls = ' class="mt-edited"' if r in edited_rows else ""
        body.append(f"<tr{row_cls}>{''.join(tds)}</tr>")
    st.session_state[store] = cur
    st.html(f'{_LIVE_TABLE_CSS}<div class="mt-wrap"><table class="mt"><thead>{head}</thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def chart(fig, key: str | None = None) -> None:
    st.plotly_chart(fig, theme="streamlit", config=PLOTLY_CONFIG, key=key)


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

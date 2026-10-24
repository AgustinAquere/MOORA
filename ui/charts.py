"""Construcción de gráficos Plotly (funciones puras: reciben datos y devuelven figuras).

Los gráficos no fijan colores de texto, ejes ni fondo: los toma el tema de Streamlit en
el navegador, por lo que se adaptan solos al modo claro u oscuro (ver ``theme.py``).
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from engine import RATIO_SYSTEM, REFERENCE_POINT, MooraResult, SensitivityResult

from .theme import (
    ACCENT,
    CATEGORICAL,
    FONT_FAMILY,
    LABEL_BG,
    MAX_SERIES,
    MUTED,
    NEUTRAL,
    SEQUENTIAL,
    SUCCESS,
    series_colors,
)

PLOTLY_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
    "toImageButtonOptions": {"format": "png", "scale": 2},
}


def _base(fig: go.Figure, height: int, *, legend: bool = False) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=24, t=40 if legend else 16, b=10),
        font=dict(family=FONT_FAMILY, size=13),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title_text=""),
        barcornerradius=4,
    )
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    return fig


def _bar_height(count: int) -> int:
    # ~46 px por categoría con bargap 0.5 -> barras de ~23 px.
    return max(200, 46 * count + 70)


# ---------------------------------------------------------------------------
# Pesos
# ---------------------------------------------------------------------------

def weights_bar(criteria: list[str], weights: np.ndarray) -> go.Figure:
    w = np.asarray(weights)
    order = np.argsort(w)  # el mayor arriba
    fig = go.Figure(
        go.Bar(
            x=w[order],
            y=[criteria[i] for i in order],
            orientation="h",
            marker_color=ACCENT,
            text=[f"{v:.1%}" for v in w[order]],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}<br>w = %{x:.4f}<extra></extra>",
        )
    )
    fig.update_layout(bargap=0.5)
    fig.update_xaxes(tickformat=".0%", range=[0, w.max() * 1.18 if w.size else 1])
    return _base(fig, _bar_height(len(criteria)))


# ---------------------------------------------------------------------------
# Puntajes y comparación
# ---------------------------------------------------------------------------

def score_bar(result: MooraResult, method: str, decimals: int = 4) -> go.Figure:
    """Barras de y_i (mayor es mejor) o d_i (menor es mejor), con la mejor arriba y destacada."""
    if method == RATIO_SYSTEM:
        scores, ranks, label = result.ratio_scores, result.ratio_ranks, "y_i"
    else:
        scores, ranks, label = result.reference_scores, result.reference_ranks, "d_i"
    order = np.lexsort((np.arange(result.m), ranks))[::-1]  # peor abajo, mejor arriba
    colors = [ACCENT if ranks[i] == 1 else NEUTRAL for i in order]
    fig = go.Figure(
        go.Bar(
            x=scores[order],
            y=[result.alternatives[i] for i in order],
            orientation="h",
            marker_color=colors,
            text=[f"{scores[i]:.{decimals}f}  ({ranks[i]}°)" for i in order],
            textposition="outside",
            cliponaxis=False,
            customdata=ranks[order],
            hovertemplate="%{y}<br>" + label + " = %{x:.6f}<br>Posición: %{customdata}°<extra></extra>",
        )
    )
    lo, hi = float(min(scores.min(), 0)), float(max(scores.max(), 0))
    span = (hi - lo) or 0.1
    # Espacio para las etiquetas fuera de las barras (las negativas van a la izquierda).
    fig.update_xaxes(range=[lo - (0.5 * span if lo < 0 else 0), hi + 0.35 * span], title_text=label, zeroline=True)
    fig.update_layout(bargap=0.5)
    return _base(fig, _bar_height(result.m))


def slope_chart(result: MooraResult) -> go.Figure:
    """Posición de cada alternativa en ambos métodos (1° arriba)."""
    colors = series_colors(result.alternatives)
    x = [RATIO_SYSTEM, REFERENCE_POINT]
    fig = go.Figure()
    for i, name in enumerate(result.alternatives):
        ranks = [int(result.ratio_ranks[i]), int(result.reference_ranks[i])]
        fig.add_trace(
            go.Scatter(
                x=x,
                y=ranks,
                mode="lines+markers",
                name=name,
                line=dict(color=colors[name], width=2),
                marker=dict(size=11, color=colors[name]),
                hovertemplate=f"{name}<br>%{{x}}: %{{y}}°<extra></extra>",
            )
        )
        fig.add_annotation(x=x[1], y=ranks[1], text=f"{name} ({ranks[1]}°)", xanchor="left", xshift=12,
                           showarrow=False, font=dict(size=12))
        fig.add_annotation(x=x[0], y=ranks[0], text=f"({ranks[0]}°) {name}", xanchor="right", xshift=-12,
                           showarrow=False, font=dict(size=12))
    fig.update_yaxes(autorange="reversed", dtick=1, title_text="Posición", showgrid=True)
    fig.update_xaxes(showgrid=False)
    fig = _base(fig, max(300, 52 * result.m + 90), legend=True)
    fig.update_layout(margin=dict(l=150, r=150, t=40, b=10))
    return fig


def contribution_chart(result: MooraResult) -> go.Figure:
    """Aporte de cada criterio a y_i: beneficios suman (derecha), costos restan (izquierda)."""
    order = np.lexsort((np.arange(result.m), result.ratio_ranks))[::-1]
    alts = [result.alternatives[i] for i in order]
    fig = go.Figure()
    contrib = result.signed_weighted[order]
    n = result.n
    groups = [[j] for j in range(min(n, MAX_SERIES - 1 if n > MAX_SERIES else n))]
    if n > MAX_SERIES:
        groups.append(list(range(MAX_SERIES - 1, n)))
    for g, cols in enumerate(groups):
        name = result.criteria[cols[0]] if len(cols) == 1 else "Otros criterios"
        color = CATEGORICAL[g] if len(cols) == 1 else NEUTRAL
        values = contrib[:, cols].sum(axis=1)
        kind = "beneficio" if len(cols) == 1 and result.is_benefit[cols[0]] else ("costo" if len(cols) == 1 else "varios")
        fig.add_trace(
            go.Bar(
                x=values,
                y=alts,
                orientation="h",
                name=name,
                marker=dict(color=color),
                hovertemplate=f"%{{y}}<br>{name} ({kind})<br>aporte = %{{x:.4f}}<extra></extra>",
            )
        )
    fig.add_trace(
        go.Scatter(
            x=result.ratio_scores[order],
            y=alts,
            mode="markers",
            name="y_i (neto)",
            marker=dict(symbol="diamond", size=13, color=MUTED, line=dict(color="#ffffff", width=1.5)),
            hovertemplate="%{y}<br>y_i = %{x:.4f}<extra></extra>",
        )
    )
    fig.update_layout(barmode="relative", bargap=0.45)
    fig.update_xaxes(title_text="Aporte ponderado  (+ beneficio, − costo)", zeroline=True, zerolinewidth=2)
    return _base(fig, _bar_height(result.m) + 40, legend=True)


def deviation_heatmap(result: MooraResult, decimals: int = 4) -> go.Figure:
    """Desvíos ponderados w_j |r_j − x*_ij|; se marca el máximo de cada fila (= d_i)."""
    z = result.weighted_deviations
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=result.criteria,
            y=result.alternatives,
            colorscale=SEQUENTIAL,
            zmin=0,
            xgap=2,
            ygap=2,
            colorbar=dict(title=dict(text="desvío"), outlinewidth=0, thickness=12),
            hovertemplate="%{y} · %{x}<br>w·|r − x*| = %{z:.6f}<extra></extra>",
        )
    )
    zmax = float(z.max()) or 1.0
    for i, j in enumerate(result.critical_criteria):
        # Sobre azul intenso, texto blanco; sobre celdas tenues, el color de texto del tema.
        font = dict(size=12, color="#ffffff") if z[i, j] / zmax > 0.5 else dict(size=12)
        fig.add_annotation(
            x=result.criteria[j], y=result.alternatives[i],
            text=f"<b>{z[i, j]:.{decimals}f}</b>", showarrow=False, font=font,
        )
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(showgrid=False, side="top")
    return _base(fig, max(220, 44 * result.m + 90))


# ---------------------------------------------------------------------------
# Sensibilidad
# ---------------------------------------------------------------------------

def _method_ranks(sens: SensitivityResult, method: str) -> np.ndarray:
    return sens.ratio_ranks if method == RATIO_SYSTEM else sens.reference_ranks


def _weight_markers(fig: go.Figure, base: float, point: float) -> None:
    """Línea del peso original (continua) y del peso simulado (verde, a trazos)."""
    fig.add_vline(x=base, line=dict(color=MUTED, width=1.5))
    fig.add_annotation(x=base, y=1.0, yref="paper", text=f"original {base:.3f}", showarrow=False,
                       yanchor="bottom", xanchor="right" if point >= base else "left",
                       xshift=-4 if point >= base else 4, font=dict(size=11), bgcolor=LABEL_BG)
    fig.add_vline(x=point, line=dict(color=SUCCESS, width=2, dash="dash"))
    fig.add_annotation(x=point, y=1.0, yref="paper", text=f"<b>simulado {point:.3f}</b>", showarrow=False,
                       yanchor="bottom", xanchor="left" if point >= base else "right",
                       xshift=4 if point >= base else -4, font=dict(size=11, color=SUCCESS), bgcolor=LABEL_BG)


def stability_line_chart(sens: SensitivityResult, method: str, point: float, relative: bool = False) -> go.Figure:
    """Puntaje de cada alternativa en función del peso del criterio, con un marcador en cada
    cruce en el que otra alternativa pasa al 1° lugar.

    relative: resta a cada puntaje el promedio de las alternativas para ese mismo peso. Quita la
    tendencia común a todas (que aplasta las líneas) sin mover los cruces: restar el mismo valor
    a todas no cambia el orden, y en SR las líneas siguen siendo rectas.
    """
    colors = series_colors(sens.alternatives)
    if method == RATIO_SYSTEM:
        scores, symbol, sense = sens.ratio_scores, "yᵢ", "mayor es mejor"
        title = "Puntaje MOORA yᵢ"
    else:
        scores, symbol, sense = sens.reference_scores, "dᵢ", "menor es mejor"
        title = "Distancia dᵢ"
    values = scores - scores.mean(axis=1, keepdims=True) if relative else scores
    title = f"{symbol} − promedio ({sense})" if relative else f"{title} ({sense})"
    fig = go.Figure()
    if relative:
        fig.add_hline(y=0, line=dict(color=MUTED, width=1, dash="dot"))
        fig.add_annotation(x=1.0, xref="paper", y=0, text="promedio", showarrow=False, xanchor="right",
                           yanchor="bottom", font=dict(size=11, color=MUTED))
    for i, name in enumerate(sens.alternatives):
        fig.add_trace(
            go.Scatter(
                x=sens.grid, y=values[:, i], mode="lines", name=name,
                line=dict(color=colors[name], width=2.5), customdata=scores[:, i],
                hovertemplate=(f"{name}: %{{y:+.4f}}  ({symbol} = %{{customdata:.4f}})<extra></extra>" if relative
                               else f"{name}: %{{y:.4f}}<extra></extra>"),
            )
        )
    _weight_markers(fig, sens.base_weight, point)
    # Cruces: el puntaje se interpola sobre la grilla (en SR es exacto porque yᵢ es lineal en el peso).
    cps = sens.change_points[sens.change_points["Método"] == method]
    for c, (w, after) in enumerate(zip(cps["Peso"], cps["Mejor después"])):
        i = sens.alternatives.index(after.split(" / ")[0])
        y = float(np.interp(w, sens.grid, values[:, i]))
        fig.add_trace(
            go.Scatter(
                x=[w], y=[y], mode="markers", showlegend=False,
                marker=dict(size=11, color="#ffffff", line=dict(color=MUTED, width=2.5)),
                hovertemplate=f"Cruce en w = {w:.4f}<br>{after} pasa al 1° lugar<extra></extra>",
            )
        )
        # Etiqueta separada del punto con una flecha corta (alternando abajo / arriba si hay varios cruces).
        fig.add_annotation(x=w, y=y, text=f"Cruce en {w:.3f}: {after} pasa al 1° lugar", showarrow=True,
                           arrowhead=0, arrowwidth=1, arrowcolor=MUTED, ax=0, ay=56 if c % 2 == 0 else -56,
                           font=dict(size=11), bgcolor=LABEL_BG, borderpad=3)
    fig.update_xaxes(title_text=f"Peso de «{sens.criterion}» (0 a 1)", range=[sens.grid[0], sens.grid[-1]],
                     dtick=0.1, tickformat=".2f")
    fig.update_yaxes(title_text=title, tickformat="+.2f" if relative else ".2f", zeroline=False)
    fig.update_layout(hovermode="x unified")
    fig = _base(fig, 440, legend=True)
    # Leyenda por encima de las etiquetas «original» / «simulado».
    fig.update_layout(margin=dict(t=80), legend=dict(y=1.13))
    return fig


def rank_heatmap(sens: SensitivityResult, method: str, point: float) -> go.Figure:
    """Mapa de calor de la posición de cada alternativa (filas) para cada peso (columnas).
    Cuanto más intenso el color, mejor la posición."""
    ranks = _method_ranks(sens, method).T
    m = len(sens.alternatives)
    top = max(m, 2)
    # El 1° en índigo pleno; del 2° al último, de tenue a casi transparente (el texto gris se lee en ambos temas).
    cut = 0.5 / (top - 1)
    colorscale = [[0.0, "rgba(82, 102, 224, 1.0)"], [cut, "rgba(82, 102, 224, 1.0)"],
                  [cut + 1e-9, "rgba(82, 102, 224, 0.32)"], [1.0, "rgba(82, 102, 224, 0.05)"]]
    fig = go.Figure(
        go.Heatmap(
            z=ranks, x=sens.grid, y=sens.alternatives, colorscale=colorscale,
            zmin=1, zmax=top, xgap=2, ygap=2, showscale=False,
            hovertemplate="Peso: %{x:.3f}<br>%{y}: %{z}°<extra></extra>",
        )
    )
    # Texto aparte: blanco sobre el 1°, color del tema (claro u oscuro) sobre el resto.
    ii, gg = np.indices(ranks.shape)
    for strong in (True, False):
        mask = (ranks == 1) if strong else (ranks != 1)
        fig.add_trace(
            go.Scatter(
                x=sens.grid[gg[mask]], y=[sens.alternatives[i] for i in ii[mask]], mode="text",
                text=[f"{v}°" for v in ranks[mask]], hoverinfo="skip", showlegend=False,
                textfont=dict(size=12, weight=600, color="#ffffff" if strong else None),
            )
        )
    _weight_markers(fig, sens.base_weight, point)
    step = float(sens.grid[1] - sens.grid[0])
    fig.update_xaxes(title_text=f"Peso de «{sens.criterion}»", showgrid=False, tickformat=".1f", dtick=0.1,
                     range=[sens.grid[0] - step / 2, sens.grid[-1] + step / 2])
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig = _base(fig, max(260, 48 * m + 130))
    fig.update_layout(margin=dict(t=40))
    return fig

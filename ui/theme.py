"""Colores de los gráficos.

Los textos, ejes, cuadrícula y fondos de los gráficos los pone el tema de Streamlit
(``st.plotly_chart(theme="streamlit")``), que se aplica en el navegador: así los gráficos
cambian al instante cuando el usuario elige Light / Dark en el menú ⋮, sin recargar.

Aquí solo se definen los colores de los datos, elegidos en tonos medios que se leen
sobre fondo claro y oscuro.
"""

from __future__ import annotations

# Paleta categórica apta para daltonismo (orden fijo, nunca se cicla).
CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#7a6fd6", "#e34948"]
MAX_SERIES = len(CATEGORICAL)

ACCENT = CATEGORICAL[0]  # barra destacada (mejor alternativa)
NEUTRAL = "#a3a19a"  # barras no destacadas, grupo «Otros»
MUTED = "#898781"  # líneas de referencia y marcadores neutros
LABEL_BG = "rgba(128, 128, 128, 0.18)"  # fondo semitransparente para etiquetas sobre el gráfico

# Escala secuencial por opacidad del azul: cerca de 0 se funde con el fondo (claro u oscuro).
SEQUENTIAL = [[0.0, "rgba(42, 120, 214, 0.04)"], [1.0, "rgba(42, 120, 214, 1.0)"]]

FONT_FAMILY = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'


def series_colors(names: list[str]) -> dict[str, str]:
    """Color por entidad (no por posición en el ranking).

    Las primeras ocho entidades usan la paleta en orden fijo; a partir de la novena
    se agrupan en un gris neutro (no se inventan tonos nuevos).
    """
    return {name: (CATEGORICAL[i] if i < MAX_SERIES else NEUTRAL) for i, name in enumerate(names)}

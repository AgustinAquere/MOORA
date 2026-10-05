"""Paleta de colores y estilo base de los gráficos (modo claro y oscuro)."""

from __future__ import annotations

import streamlit as st

# Paleta categórica validada para daltonismo (orden fijo, nunca se cicla).
CATEGORICAL = {
    "light": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"],
    "dark": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"],
}

INK = {
    "light": {
        "primary": "#0b0b0b",
        "secondary": "#52514e",
        "muted": "#898781",
        "grid": "#e1e0d9",
        "axis": "#c3c2b7",
        "surface": "#fcfcfb",
        "other": "#b5b3ab",
    },
    "dark": {
        "primary": "#ffffff",
        "secondary": "#c3c2b7",
        "muted": "#898781",
        "grid": "#2c2c2a",
        "axis": "#383835",
        "surface": "#1a1a19",
        "other": "#5c5b56",
    },
}

# Rampa secuencial azul (claro → oscuro) para magnitudes.
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
# Paso atenuado para barras que no son la destacada.
SOFT_BLUE = {"light": "#9ec5f4", "dark": "#1c5cab"}

FONT_FAMILY = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
MAX_SERIES = len(CATEGORICAL["light"])


def mode() -> str:
    """Tema activo de Streamlit ("light" o "dark")."""
    try:
        kind = st.context.theme.type
    except Exception:  # versiones antiguas o fuera de una sesión
        kind = None
    return "dark" if kind == "dark" else "light"


def series_colors(names: list[str], theme: str) -> dict[str, str]:
    """Color por entidad (no por posición en el ranking).

    Las primeras ocho entidades usan la paleta categórica en orden fijo; a partir
    de la novena se agrupan en un gris neutro (no se inventan tonos nuevos).
    """
    palette = CATEGORICAL[theme]
    return {name: (palette[i] if i < MAX_SERIES else INK[theme]["other"]) for i, name in enumerate(names)}

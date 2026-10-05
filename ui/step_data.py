"""Paso 1: definición del problema y carga de la matriz de decisión."""

from __future__ import annotations

import streamlit as st

from data_io.examples import EXAMPLES
from data_io.serializers import EXCEL_MIME, excel_sheet_names, problem_to_csv, problem_to_excel, read_problem
from data_io.validators import unique_labels, validate_matrix, validate_names

from . import state
from .components import md, nav_buttons, show_report

MAX_DIM = 50


def _load_example() -> None:
    state.set_problem(state.problem_from_example(st.session_state["example_choice"]))
    st.session_state["flash"] = f"Se cargó el ejemplo «{st.session_state['example_choice']}»."


def _apply_dimensions() -> None:
    p = state.get_problem()
    m, n = int(st.session_state["dim_m"]), int(st.session_state["dim_n"])
    new = state.resized(p, m, n)
    new.name = st.session_state.get("problem_name_input", p.name)
    state.set_problem(new)
    st.session_state["flash"] = f"Matriz redimensionada a {m} × {n} (se conservaron los datos existentes)."


def _new_empty() -> None:
    m, n = int(st.session_state["dim_m"]), int(st.session_state["dim_n"])
    state.set_problem(state.empty_problem(m, n))
    st.session_state["flash"] = f"Se creó una matriz vacía de {m} × {n}."


def _load_import(imported, name: str) -> None:
    state.set_problem(state.problem_from_import(imported, name))
    st.session_state["flash"] = f"Se importaron {len(imported.alternatives)} alternativas y {len(imported.criteria)} criterios."


def _rename_criteria(key: str) -> None:
    delta = st.session_state.get(key) or {}
    if state.rename_criteria(delta.get("edited_rows", {})):
        # Recrea las tablas para que los encabezados de la matriz muestren los nombres nuevos.
        state.refresh_editors()


def render() -> None:
    p = state.get_problem()
    st.header("1 · Datos del problema")
    st.caption(
        "Defina las alternativas, los criterios y la matriz de decisión. El sentido (beneficio o costo) "
        "y el peso de cada criterio se configuran en el paso 2."
    )

    # Streamlit descarta el estado de los widgets que no se dibujan; al volver a este
    # paso se reconstruye desde el problema.
    st.session_state.setdefault("problem_name_input", p.name)
    st.session_state.setdefault("dim_m", max(p.m, 1))
    st.session_state.setdefault("dim_n", max(p.n, 1))

    p.name = st.text_input("Nombre del problema", key="problem_name_input")

    tab_ex, tab_manual, tab_file = st.tabs(
        ["📚 Ejemplos precargados", "✏️ Carga manual", "📂 Importar Excel / CSV"], key="data_source_tabs"
    )

    with tab_ex:
        choice = st.selectbox("Ejemplo", list(EXAMPLES), key="example_choice")
        st.caption(EXAMPLES[choice].description)
        st.button("Cargar ejemplo", on_click=_load_example, type="primary", icon="📥")

    with tab_manual:
        c1, c2 = st.columns(2)
        c1.number_input("Alternativas (m)", min_value=1, max_value=MAX_DIM, step=1, key="dim_m")
        c2.number_input("Criterios (n)", min_value=1, max_value=MAX_DIM, step=1, key="dim_n")
        b1, b2, _ = st.columns([1.2, 1, 1])
        b1.button("Aplicar dimensión (conserva datos)", on_click=_apply_dimensions, width="stretch")
        b2.button("Nueva matriz vacía", on_click=_new_empty, width="stretch")
        st.caption(
            "Luego complete las tablas de abajo: escriba los nombres de los criterios en la fila «Nombres de los "
            "criterios» y los de las alternativas en la primera columna de la matriz."
        )

    with tab_file:
        _import_section(p)

    # El aviso va debajo de las pestañas para no cambiar su posición (y no perder la pestaña activa).
    if msg := st.session_state.pop("flash", None):
        st.success(md(msg), icon="✅")

    ss = st.session_state
    st.subheader("Nombres de los criterios")
    names_key = f"names_editor_{ss['nonce']}"
    st.data_editor(
        ss["names_snapshot"],
        key=names_key,
        hide_index=True,
        num_rows="fixed",
        column_config={
            state.names_column(j): st.column_config.TextColumn(state.names_column(j), required=True)
            for j in range(p.n)
        },
        on_change=_rename_criteria,
        args=(names_key,),
        width="stretch",
    )

    st.subheader(f"Matriz de decisión ({p.m} × {p.n})")
    column_config = {
        state.ALT_COL: st.column_config.TextColumn(state.ALT_COL, required=True, pinned=True, width="medium"),
    }
    for label in unique_labels(p.criteria, "C"):
        column_config[label] = st.column_config.NumberColumn(label, format="%g")
    edited = st.data_editor(
        ss["matrix_snapshot"],
        key=f"matrix_editor_{ss['nonce']}",
        hide_index=True,
        num_rows="fixed",
        column_config=column_config,
        width="stretch",
    )
    state.apply_matrix_edit(p, edited)

    labels_a = unique_labels(p.alternatives, "A")
    report, _ = validate_matrix(p.values, labels_a, unique_labels(p.criteria, "C"))
    report.merge(validate_names(p.alternatives, "alternativa"))
    report.merge(validate_names(p.criteria, "criterio"))
    if report.ok and not report.warnings:
        st.success("La matriz está completa y es válida.", icon="✅")
    show_report(report)

    nav_buttons(state.STEPS[0])


def _import_section(p: state.Problem) -> None:
    st.markdown(
        "Formato esperado: primera fila con los **nombres de los criterios**, primera columna con las "
        "**alternativas**. Opcionalmente, filas **Sentido** (Beneficio/Costo o Max/Min) y **Peso**. "
        "Se aceptan coma o punto decimal y CSV separado por «,» o «;»."
    )
    upload = st.file_uploader("Archivo", type=["xlsx", "xls", "csv"], key="upload")
    if upload is not None:
        data = upload.getvalue()
        sheet = 0
        if upload.name.lower().endswith((".xlsx", ".xls")):
            try:
                sheets = excel_sheet_names(data)
            except Exception as exc:
                st.error(f"No se pudo abrir el libro de Excel: {exc}", icon="⛔")
                return
            if len(sheets) > 1:
                sheet = st.selectbox("Hoja", sheets)
        try:
            imported = read_problem(data, upload.name, sheet)
        except ValueError as exc:
            st.error(md(str(exc)), icon="⛔")
            return
        st.markdown(f"**Vista previa** — {len(imported.alternatives)} alternativas × {len(imported.criteria)} criterios")
        st.dataframe(imported.values, width="stretch")
        info = []
        info.append("sentidos: " + ("✔ incluidos" if imported.directions else "no incluidos (se asume Beneficio)"))
        info.append("pesos: " + ("✔ incluidos" if imported.weights else "no incluidos (se asignan iguales)"))
        st.caption(" · ".join(info))
        for w in imported.warnings:
            st.warning(md(w), icon="⚠️")
        name = upload.name.rsplit(".", 1)[0]
        st.button("Usar estos datos", on_click=_load_import, args=(imported, name), type="primary", icon="📥")

    st.markdown("**Plantillas** (el problema actual en el formato de importación):")
    args = (p.alternatives, p.criteria, p.values, p.directions, p.weights)
    c1, c2 = st.columns(2)
    c1.download_button("Plantilla Excel", problem_to_excel(*args), "plantilla_moora.xlsx", EXCEL_MIME,
                       on_click="ignore", icon="📄", width="stretch")
    c2.download_button("Plantilla CSV (;)", problem_to_csv(*args, sep=";", decimal=","), "plantilla_moora.csv",
                       "text/csv", on_click="ignore", icon="📄", width="stretch")

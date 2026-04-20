# src/components/programacion_form.py
# ─────────────────────────────────────────────────────────────────────────────
# Formulario de programación mensual editable
# Pre-cargado con los datos oficiales de IPEN 2026
#
# CORRECCIONES:
#   - Bug 2: DataFrame siempre con índice=genéricas, columnas=MESES
#   - Bug 3: inicializar_programacion() llamado desde app.py ANTES de los tabs
# ─────────────────────────────────────────────────────────────────────────────

import os
import pandas as pd
import streamlit as st
from config import MESES, CARPETA_DATA, PROGRAMACION_PRECARGADA

_ARCHIVO_PROG = "programacion_actual.json"


def _ruta_prog() -> str:
    os.makedirs(CARPETA_DATA, exist_ok=True)
    return os.path.join(CARPETA_DATA, _ARCHIVO_PROG)


def _asegurar_estructura(df: pd.DataFrame) -> pd.DataFrame:
    """Garantiza columnas=MESES. Corrige si el DF quedó transpuesto."""
    meses_set = set(MESES)
    if meses_set.issubset(set(df.columns.tolist())):
        return df[MESES]
    if meses_set.issubset(set(df.index.tolist())):
        return df.T[MESES]
    return df


def _construir_df_precargado(genericas: list[str]) -> pd.DataFrame:
    """Crea DF desde PROGRAMACION_PRECARGADA. índice=genéricas, columnas=MESES."""
    filas = {}
    for gen in genericas:
        prefijo = gen.split(".")[0].strip()
        fila    = {mes: 0.0 for mes in MESES}
        for key, vals in PROGRAMACION_PRECARGADA.items():
            if key.split(".")[0].strip() == prefijo:
                fila = {mes: float(vals.get(mes, 0.0)) for mes in MESES}
                break
        filas[gen] = fila
    return pd.DataFrame.from_dict(filas, orient="index", columns=MESES)


def guardar_programacion_json(df: pd.DataFrame) -> tuple[bool, str]:
    try:
        _asegurar_estructura(df).to_json(_ruta_prog(), orient="index")
        return True, _ruta_prog()
    except Exception as e:
        return False, str(e)


def cargar_programacion_json() -> tuple[bool, "pd.DataFrame | str"]:
    ruta = _ruta_prog()
    if not os.path.exists(ruta):
        return False, "No hay programación guardada."
    try:
        return True, _asegurar_estructura(pd.read_json(ruta, orient="index"))
    except Exception as e:
        return False, str(e)


def inicializar_programacion(genericas_ordenadas: list[str]) -> pd.DataFrame:
    """
    Debe llamarse desde app.py ANTES de renderizar los tabs.
    Garantiza que session_state.programacion_mensual siempre exista
    con estructura correcta (índice=genéricas, columnas=MESES).
    """
    if "programacion_mensual" not in st.session_state:
        st.session_state.programacion_mensual = _construir_df_precargado(genericas_ordenadas)
        return st.session_state.programacion_mensual

    df = _asegurar_estructura(st.session_state.programacion_mensual)

    # Agregar genéricas nuevas si cambiaron con un nuevo archivo
    for gen in genericas_ordenadas:
        if gen not in df.index:
            prefijo = gen.split(".")[0].strip()
            fila    = {mes: 0.0 for mes in MESES}
            for key, vals in PROGRAMACION_PRECARGADA.items():
                if key.split(".")[0].strip() == prefijo:
                    fila = {mes: float(vals.get(mes, 0.0)) for mes in MESES}
                    break
            df.loc[gen] = fila

    st.session_state.programacion_mensual = df[MESES]
    return st.session_state.programacion_mensual


def obtener_programacion_df() -> "pd.DataFrame | None":
    """Para uso en monthly_chart. Devuelve DF con columnas=MESES o None."""
    df = st.session_state.get("programacion_mensual", None)
    return _asegurar_estructura(df) if df is not None else None


def mostrar_resumen_sidebar():
    df = st.session_state.get("programacion_mensual", None)
    if df is None:
        return
    df = _asegurar_estructura(df)
    fmt = lambda v: f"S/ {round(v):,}".replace(",", ".")
    with st.sidebar.expander("📊 Resumen programación", expanded=False):
        for gen in df.index:
            total = df.loc[gen, MESES].sum()
            if total > 0:
                st.metric(gen[:30], fmt(total))
        st.markdown("---")
        st.metric("Total anual", fmt(df[MESES].sum().sum()))


def mostrar_formulario_programacion(genericas_ordenadas: list[str]):
    """Tab 4: formulario de edición. inicializar_programacion() ya fue llamado."""
    st.subheader("📅 Programación Mensual por Genérica")
    st.caption(
        "Montos en Soles. Datos precargados: programación oficial IPEN 2026. "
        "Abre el expander de cada genérica, edita y presiona **Guardar**."
    )

    df_prog = _asegurar_estructura(st.session_state.programacion_mensual)
    fmt     = lambda v: f"S/ {round(v):,}".replace(",", ".")

    # Controles
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📂 Cargar última guardada", use_container_width=True):
            ok, result = cargar_programacion_json()
            if ok:
                st.session_state.programacion_mensual = result
                st.success("✅ Programación cargada.")
                st.rerun()
            else:
                st.warning(f"⚠️ {result}")
    with c2:
        if st.button("🔄 Restaurar datos 2026", use_container_width=True):
            st.session_state.programacion_mensual = _construir_df_precargado(genericas_ordenadas)
            st.success("✅ Datos precargados restaurados.")
            st.rerun()
    with c3:
        if st.button("🗑️ Poner todo en cero", use_container_width=True):
            st.session_state.programacion_mensual = pd.DataFrame(
                0.0, index=genericas_ordenadas, columns=MESES
            )
            st.success("✅ Programación en cero.")
            st.rerun()

    # Métricas rápidas de totales anuales
    st.markdown("---")
    ncols = min(len(genericas_ordenadas), 3)
    cols_tot = st.columns(ncols)
    for i, gen in enumerate(genericas_ordenadas):
        total = df_prog.loc[gen, MESES].sum() if gen in df_prog.index else 0.0
        lbl   = gen.split(".", 1)[-1][:22] if "." in gen else gen[:22]
        cols_tot[i % ncols].metric(lbl, fmt(total))

    st.markdown("---")

    # Formulario
    with st.form("form_prog_mensual_v2"):
        df_editado = df_prog.copy()

        for gen in genericas_ordenadas:
            with st.expander(f"✏️  {gen}", expanded=False):
                st.caption("Primer semestre")
                cols_s1 = st.columns(6)
                for i, mes in enumerate(MESES[:6]):
                    val = float(df_prog.loc[gen, mes]) if gen in df_prog.index else 0.0
                    df_editado.loc[gen, mes] = cols_s1[i].number_input(
                        mes[:3], value=val, step=1_000.0, format="%.0f",
                        key=f"fpm_{gen[:10]}_{i}",
                    )
                st.caption("Segundo semestre")
                cols_s2 = st.columns(6)
                for i, mes in enumerate(MESES[6:]):
                    val = float(df_prog.loc[gen, mes]) if gen in df_prog.index else 0.0
                    df_editado.loc[gen, mes] = cols_s2[i].number_input(
                        mes[:3], value=val, step=1_000.0, format="%.0f",
                        key=f"fpm_{gen[:10]}_{i+6}",
                    )
                subtotal = df_editado.loc[gen, MESES].sum()
                st.caption(f"Total anual: **{fmt(subtotal)}**")

        if st.form_submit_button("💾 Guardar Programación", type="primary",
                                 use_container_width=True):
            st.session_state.programacion_mensual = df_editado
            ok, ruta = guardar_programacion_json(df_editado)
            if ok:
                st.success(f"✅ Guardado en `{ruta}`")
            else:
                st.error(f"❌ Error: {ruta}")

    # Tabla resumen
    with st.expander("📊 Ver tabla resumen completa", expanded=False):
        df_show             = _asegurar_estructura(st.session_state.programacion_mensual).copy()
        total_row           = df_show[MESES].sum(axis=0).to_frame().T
        total_row.index     = ["TOTAL"]
        df_show             = pd.concat([df_show, total_row])
        df_show["TOTAL AÑO"] = df_show[MESES].sum(axis=1)
        df_fmt              = df_show.applymap(lambda x: fmt(x))
        st.dataframe(df_fmt, use_container_width=True)
        st.download_button("📥 Descargar CSV", df_show.to_csv().encode("utf-8"),
                           "programacion_mensual.csv", "text/csv")

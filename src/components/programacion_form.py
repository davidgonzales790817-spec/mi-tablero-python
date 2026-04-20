# src/components/programacion_form.py
# ─────────────────────────────────────────────────────────────────────────────
# Formulario de programación mensual editable
# Pre-cargado con los datos oficiales de IPEN 2026
# ─────────────────────────────────────────────────────────────────────────────

import os
import pandas as pd
import streamlit as st
from config import MESES, CARPETA_DATA, PROGRAMACION_PRECARGADA


# ── Persistencia ──────────────────────────────────────────────────────────────

_ARCHIVO_PROG = "programacion_actual.json"


def _ruta_prog() -> str:
    os.makedirs(CARPETA_DATA, exist_ok=True)
    return os.path.join(CARPETA_DATA, _ARCHIVO_PROG)


def guardar_programacion_csv(df: pd.DataFrame) -> tuple[bool, str]:
    """Guarda la programación en JSON dentro de Respaldo_Data/."""
    try:
        df.to_json(_ruta_prog(), orient="index")
        return True, _ruta_prog()
    except Exception as e:
        return False, str(e)


def cargar_programacion_csv() -> tuple[bool, pd.DataFrame | str]:
    """Carga la programación guardada desde JSON."""
    ruta = _ruta_prog()
    if os.path.exists(ruta):
        try:
            return True, pd.read_json(ruta, orient="index")
        except Exception as e:
            return False, str(e)
    return False, "No hay programación guardada."


# ── Inicialización ────────────────────────────────────────────────────────────

def inicializar_programacion(genericas_ordenadas: list[str]) -> pd.DataFrame:
    """
    Construye (o recupera de session_state) el DataFrame de programación.
    Los datos precargados vienen de PROGRAMACION_PRECARGADA (config.py).
    """
    if "programacion_mensual" not in st.session_state:
        filas = {}
        for gen in genericas_ordenadas:
            # Coincidencia por número de genérica (clave "1.", "2.", …)
            prefijo = gen.split(".")[0]
            fila    = {mes: 0.0 for mes in MESES}
            for key, valores in PROGRAMACION_PRECARGADA.items():
                if key.split(".")[0] == prefijo:
                    fila = {mes: float(valores.get(mes, 0)) for mes in MESES}
                    break
            filas[gen] = fila

        st.session_state.programacion_mensual = pd.DataFrame(filas, index=MESES).T

    else:
        # Añadir genéricas nuevas que puedan aparecer tras un cambio de archivo
        df_actual = st.session_state.programacion_mensual
        for gen in genericas_ordenadas:
            if gen not in df_actual.index:
                df_actual.loc[gen] = 0.0
        st.session_state.programacion_mensual = df_actual

    return st.session_state.programacion_mensual


# ── Widget de resumen en sidebar ──────────────────────────────────────────────

def mostrar_resumen_sidebar():
    """Muestra un resumen compacto de la programación en el sidebar."""
    if "programacion_mensual" not in st.session_state:
        return
    df = st.session_state.programacion_mensual
    with st.sidebar.expander("📊 Resumen programación", expanded=False):
        for gen in df.index:
            total = df.loc[gen].sum()
            if total > 0:
                st.metric(gen[:30], f"S/ {round(total):,}".replace(",", "."))
        st.markdown("---")
        total_anual = df.sum().sum()
        st.metric("Total anual", f"S/ {round(total_anual):,}".replace(",", "."))


# ── Getter para el gráfico mensual ────────────────────────────────────────────

def obtener_programacion_df() -> pd.DataFrame | None:
    """Devuelve el DataFrame de programación o None si no existe."""
    return st.session_state.get("programacion_mensual", None)


# ── Formulario principal ──────────────────────────────────────────────────────

def mostrar_formulario_programacion(genericas_ordenadas: list[str]):
    """
    Renderiza el formulario editable de programación mensual.
    Incluye controles de carga, guardado y exportación.
    """
    st.subheader("📅 Programación Mensual por Genérica")
    st.caption(
        "Montos en Soles. Los datos precargados corresponden a la programación oficial IPEN 2026. "
        "Edita los valores y presiona **Guardar** para persistirlos."
    )

    df_prog = inicializar_programacion(genericas_ordenadas)

    # ── Controles superiores ──────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📂 Cargar última guardada", use_container_width=True):
            ok, result = cargar_programacion_csv()
            if ok:
                st.session_state.programacion_mensual = result
                st.success("Programación cargada.")
                st.rerun()
            else:
                st.warning(result)
    with c2:
        if st.button("🔄 Restaurar datos precargados", use_container_width=True,
                     help="Vuelve a los valores de la tabla oficial IPEN 2026"):
            st.session_state.pop("programacion_mensual", None)
            st.rerun()
    with c3:
        if st.button("🗑️ Poner todo en cero", use_container_width=True):
            st.session_state.programacion_mensual = pd.DataFrame(
                0.0, index=genericas_ordenadas, columns=MESES
            )
            st.rerun()

    st.markdown("---")

    # ── Formulario de edición ─────────────────────────────────────────────────
    df_editado = df_prog.copy()

    with st.form("form_programacion_mensual"):
        for gen in genericas_ordenadas:
            st.markdown(f"**{gen}**")
            # Primera mitad del año
            cols_h1 = st.columns(6)
            for i, mes in enumerate(MESES[:6]):
                val = float(df_prog.loc[gen, mes]) if gen in df_prog.index else 0.0
                df_editado.loc[gen, mes] = cols_h1[i].number_input(
                    mes[:3], value=val, step=1_000.0, format="%.0f",
                    key=f"prog_{gen[:15]}_{mes[:3]}_1",
                )
            # Segunda mitad del año
            cols_h2 = st.columns(6)
            for i, mes in enumerate(MESES[6:]):
                val = float(df_prog.loc[gen, mes]) if gen in df_prog.index else 0.0
                df_editado.loc[gen, mes] = cols_h2[i].number_input(
                    mes[:3], value=val, step=1_000.0, format="%.0f",
                    key=f"prog_{gen[:15]}_{mes[:3]}_2",
                )
            st.markdown("---")

        if st.form_submit_button("💾 Guardar Programación", type="primary",
                                  use_container_width=True):
            st.session_state.programacion_mensual = df_editado
            ok, ruta = guardar_programacion_csv(df_editado)
            if ok:
                st.success(f"✅ Guardado en `{ruta}`")
            else:
                st.error(f"Error al guardar: {ruta}")
            st.rerun()

    # ── Tabla resumen ─────────────────────────────────────────────────────────
    with st.expander("📊 Ver tabla resumen de programación", expanded=False):
        df_show = st.session_state.programacion_mensual.copy()

        total_row          = df_show.sum(axis=0).to_frame().T
        total_row.index    = ["TOTAL"]
        df_show            = pd.concat([df_show, total_row])
        df_show["TOTAL AÑO"] = df_show.sum(axis=1)

        fmt = lambda x: f"S/ {round(x):,}".replace(",", ".")
        df_fmt = df_show.copy()
        for col in df_fmt.columns:
            df_fmt[col] = df_fmt[col].apply(fmt)

        st.dataframe(df_fmt, use_container_width=True)

        csv_bytes = df_show.to_csv().encode("utf-8")
        st.download_button(
            "📥 Descargar programación (CSV)",
            csv_bytes,
            "programacion_mensual.csv",
            "text/csv",
        )

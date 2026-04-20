# src/components/sidebar.py
# ─────────────────────────────────────────────────────────────────────────────
# Barra lateral: logo + filtros dinámicos
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import streamlit as st
from config import LOGO_URL


def mostrar_logo():
    st.sidebar.image(LOGO_URL, width=220)


def _multiselect(label: str, df_global: pd.DataFrame, df_filtrado: pd.DataFrame,
                  col: str, key: str) -> pd.DataFrame:
    """Genera un multiselect para una columna y aplica el filtro."""
    if col not in df_global.columns:
        return df_filtrado
    st.sidebar.subheader(label)
    opts = sorted(df_global[col].dropna().unique().tolist())
    sel  = st.sidebar.multiselect(
        f"Seleccionar {label}:", opts, default=[], key=key,
        placeholder="(vacío = mostrar todos)",
    )
    if sel:
        return df_filtrado[df_filtrado[col].isin(sel)]
    return df_filtrado


def crear_filtros(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye los filtros de la barra lateral y devuelve el DataFrame
    filtrado según las selecciones del usuario.
    """
    st.sidebar.header("🔍 Filtros")
    df_f = df.copy()

    # 1. Genérica
    df_f = _multiselect("Genérica", df, df_f, "generica", "flt_generica")

    # 2. Unidad Ejecutora
    df_f = _multiselect("Unidad Ejecutora", df, df_f, "unidad_ejecutora", "flt_ue")

    # 3. Rubro / Fuente de financiamiento
    col_rubro = next(
        (c for c in df.columns if any(p in c.lower() for p in ["rubro", "fuente", "financ"])),
        None,
    )
    if col_rubro:
        df_f = _multiselect("Rubro / Fuente", df, df_f, col_rubro, "flt_rubro")

    # 4. Proyecto / Actividad
    col_proy = next(
        (c for c in df.columns if any(p in c.lower() for p in ["producto_proyecto", "actividad", "activ_obra"])),
        None,
    )
    if col_proy:
        st.sidebar.subheader("Proyecto / Actividad")
        opts_p = sorted(df[col_proy].dropna().unique().tolist())
        if len(opts_p) > 100:
            st.sidebar.caption(f"Mostrando top-100 de {len(opts_p)} disponibles.")
            opts_p = df[col_proy].value_counts().head(100).index.tolist()
        sel_p = st.sidebar.multiselect(
            "Seleccionar:", opts_p, default=[], key="flt_proyecto",
            placeholder="(vacío = todos)",
        )
        if sel_p:
            df_f = df_f[df_f[col_proy].isin(sel_p)]

    # 5. Secuencia Funcional
    col_sec = next(
        (c for c in df.columns if any(p in c.lower() for p in ["sec_func", "secuencia", "funcional"])),
        None,
    )
    if col_sec:
        df_f = _multiselect("Secuencia Funcional", df, df_f, col_sec, "flt_sec_func")

    # ── Resumen ───────────────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    c1, c2 = st.sidebar.columns(2)
    c1.metric("Total filas",    f"{len(df):,}")
    c2.metric("Filas visibles", f"{len(df_f):,}")

    if len(df) > 0:
        pct = len(df_f) / len(df)
        st.sidebar.progress(pct)
        st.sidebar.caption(f"{pct * 100:.1f}% del total")

    st.sidebar.markdown("---")

    if st.sidebar.button("🗑️ Limpiar todos los filtros", use_container_width=True):
        for k in ["flt_generica", "flt_ue", "flt_rubro", "flt_proyecto", "flt_sec_func"]:
            st.session_state.pop(k, None)
        st.rerun()

    return df_f

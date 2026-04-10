# components/sidebar.py (versión con expanders)
import streamlit as st
from config import LOGO_URL

def mostrar_logo():
    st.sidebar.image(LOGO_URL, width=250)

def crear_filtros(df):
    """
    Crea los filtros en la barra lateral usando multiselect dentro de expanders
    """
    st.sidebar.header("🔍 Filtros")
    
    df_filtrado = df.copy()
    
    # ============================================
    # 1. FILTRO POR GENÉRICA
    # ============================================
    if "generica" in df.columns:
        with st.sidebar.expander("📂 Genérica", expanded=False):
            opciones = sorted(df["generica"].dropna().unique().tolist())
            seleccion = st.multiselect(
                "Seleccionar Genéricas:",
                options=opciones,
                default=[],
                key="filtro_generica",
                label_visibility="collapsed"
            )
            if seleccion:
                df_filtrado = df_filtrado[df_filtrado["generica"].isin(seleccion)]
    
    # ============================================
    # 2. FILTRO POR UNIDAD EJECUTORA
    # ============================================
    if "unidad_ejecutora" in df.columns:
        with st.sidebar.expander("🏛️ Unidad Ejecutora", expanded=False):
            opciones = sorted(df["unidad_ejecutora"].dropna().unique().tolist())
            seleccion = st.multiselect(
                "Seleccionar Unidades Ejecutoras:",
                options=opciones,
                default=[],
                key="filtro_ue",
                label_visibility="collapsed"
            )
            if seleccion:
                df_filtrado = df_filtrado[df_filtrado["unidad_ejecutora"].isin(seleccion)]
    
    # ============================================
    # 3. FILTRO POR RUBRO DE FINANCIAMIENTO
    # ============================================
    col_rubro = None
    for col in df.columns:
        if any(p in col.lower() for p in ["rubro", "financiamiento", "fuente"]):
            col_rubro = col
            break
    
    if col_rubro:
        with st.sidebar.expander("💰 Rubro de Financiamiento", expanded=False):
            opciones = sorted(df[col_rubro].dropna().unique().tolist())
            seleccion = st.multiselect(
                "Seleccionar Rubros:",
                options=opciones,
                default=[],
                key="filtro_rubro",
                label_visibility="collapsed"
            )
            if seleccion:
                df_filtrado = df_filtrado[df_filtrado[col_rubro].isin(seleccion)]
    
    # ============================================
    # 4. FILTRO POR PROYECTO/ACTIVIDAD
    # ============================================
    col_proyecto = None
    for col in df.columns:
        if any(p in col.lower() for p in ["proyecto", "actividad"]):
            col_proyecto = col
            break
    
    if col_proyecto:
        with st.sidebar.expander("📋 Proyecto / Actividad", expanded=False):
            opciones = sorted(df[col_proyecto].dropna().unique().tolist())
            if len(opciones) > 100:
                conteo = df[col_proyecto].value_counts()
                opciones = conteo.head(100).index.tolist()
                st.caption(f"⚠️ Mostrando 100 de {len(df[col_proyecto].dropna().unique())} proyectos")
            
            seleccion = st.multiselect(
                "Seleccionar Proyectos/Actividades:",
                options=opciones,
                default=[],
                key="filtro_proyecto",
                label_visibility="collapsed"
            )
            if seleccion:
                df_filtrado = df_filtrado[df_filtrado[col_proyecto].isin(seleccion)]
    
    # ============================================
    # 5. FILTRO POR SEC_FUNC
    # ============================================
    col_sec_func = None
    for col in df.columns:
        if any(p in col.lower() for p in ["sec_func", "secfunc", "secuencia", "funcional"]):
            col_sec_func = col
            break
    
    if col_sec_func:
        with st.sidebar.expander("🔢 Secuencia Funcional", expanded=False):
            opciones = sorted(df[col_sec_func].dropna().unique().tolist())
            seleccion = st.multiselect(
                "Seleccionar Secuencias Funcionales:",
                options=opciones,
                default=[],
                key="filtro_sec",
                label_visibility="collapsed"
            )
            if seleccion:
                df_filtrado = df_filtrado[df_filtrado[col_sec_func].isin(seleccion)]
    
    # ============================================
    # MOSTRAR RESUMEN
    # ============================================
    st.sidebar.markdown("---")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("📊 Total", f"{len(df):,}")
    with col2:
        st.metric("✅ Mostrados", f"{len(df_filtrado):,}")
    
    if len(df) > 0:
        porcentaje = (len(df_filtrado) / len(df)) * 100
        st.sidebar.progress(porcentaje / 100)
    
    if st.sidebar.button("🗑️ Limpiar todos los filtros", use_container_width=True):
        st.rerun()
    
    return df_filtrado

# components/sidebar.py
import streamlit as st
from config import LOGO_URL

def mostrar_logo():
    st.sidebar.image(LOGO_URL, width=250)

def crear_filtros(df):
    """
    Crea los filtros en la barra lateral usando multiselect
    """
    st.sidebar.header("🔍 Filtros")
    
    df_filtrado = df.copy()
    
    # ============================================
    # 1. FILTRO POR GENÉRICA
    # ============================================
    if "generica" in df.columns:
        st.sidebar.subheader("📂 Genérica")
        opciones = sorted(df["generica"].dropna().unique().tolist())
        
        # Usar una key fija para que Streamlit maneje el estado
        seleccion = st.sidebar.multiselect(
            "Seleccionar Genéricas:",
            options=opciones,
            default=[],
            key="multiselect_generica",
            placeholder="Ninguna seleccionada = mostrar todas",
            help="Seleccione una o varias genéricas. Si no selecciona ninguna, se muestran todas."
        )
        
        if seleccion:
            df_filtrado = df_filtrado[df_filtrado["generica"].isin(seleccion)]
    
    # ============================================
    # 2. FILTRO POR UNIDAD EJECUTORA
    # ============================================
    if "unidad_ejecutora" in df.columns:
        st.sidebar.subheader("🏛️ Unidad Ejecutora")
        opciones = sorted(df["unidad_ejecutora"].dropna().unique().tolist())
        
        seleccion = st.sidebar.multiselect(
            "Seleccionar Unidades Ejecutoras:",
            options=opciones,
            default=[],
            key="multiselect_ue",
            placeholder="Ninguna seleccionada = mostrar todas"
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
        st.sidebar.subheader("💰 Rubro de Financiamiento")
        opciones = sorted(df[col_rubro].dropna().unique().tolist())
        
        seleccion = st.sidebar.multiselect(
            "Seleccionar Rubros:",
            options=opciones,
            default=[],
            key="multiselect_rubro",
            placeholder="Ninguna seleccionada = mostrar todos"
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
        st.sidebar.subheader("📋 Proyecto / Actividad")
        opciones = sorted(df[col_proyecto].dropna().unique().tolist())
        
        # Limitar para rendimiento
        if len(opciones) > 100:
            st.sidebar.warning(f"Hay {len(opciones)} proyectos. Mostrando los 100 más comunes.")
            conteo = df[col_proyecto].value_counts()
            opciones = conteo.head(100).index.tolist()
        
        seleccion = st.sidebar.multiselect(
            "Seleccionar Proyectos/Actividades:",
            options=opciones,
            default=[],
            key="multiselect_proyecto",
            placeholder="Ninguna seleccionada = mostrar todos"
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
        st.sidebar.subheader("🔢 Secuencia Funcional")
        opciones = sorted(df[col_sec_func].dropna().unique().tolist())
        
        seleccion = st.sidebar.multiselect(
            "Seleccionar Secuencias Funcionales:",
            options=opciones,
            default=[],
            key="multiselect_sec",
            placeholder="Ninguna seleccionada = mostrar todas"
        )
        
        if seleccion:
            df_filtrado = df_filtrado[df_filtrado[col_sec_func].isin(seleccion)]
    
    # ============================================
    # MOSTRAR RESUMEN Y BOTÓN DE LIMPIEZA
    # ============================================
    st.sidebar.markdown("---")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("📊 Total registros", f"{len(df):,}")
    with col2:
        st.metric("✅ Registros mostrados", f"{len(df_filtrado):,}")
    
    if len(df) > 0:
        porcentaje = (len(df_filtrado) / len(df)) * 100
        st.sidebar.progress(porcentaje / 100)
        st.sidebar.caption(f"{porcentaje:.1f}% del total")
    
    st.sidebar.markdown("---")
    
    # Botón de limpieza - usando la forma más simple
    # Al hacer clic, redirige a una URL que fuerza recarga limpia
    if st.sidebar.button("🗑️ Limpiar todos los filtros", use_container_width=True):
        # Limpiar todas las keys de multiselect
        keys_a_limpiar = [
            "multiselect_generica",
            "multiselect_ue", 
            "multiselect_rubro",
            "multiselect_proyecto",
            "multiselect_sec"
        ]
        for key in keys_a_limpiar:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    return df_filtrado

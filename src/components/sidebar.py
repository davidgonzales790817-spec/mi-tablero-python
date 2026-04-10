# components/sidebar.py
import streamlit as st
from config import LOGO_URL

def mostrar_logo():
    st.sidebar.image(LOGO_URL, width=250)

def crear_filtros(df):
    """
    Crea los filtros en la barra lateral usando multiselect con control de estado
    """
    st.sidebar.header("🔍 Filtros")
    
    # Inicializar session_state para controlar el reset
    if "reset_filtros" not in st.session_state:
        st.session_state.reset_filtros = False
    
    df_filtrado = df.copy()
    
    # ============================================
    # FUNCIÓN PARA LIMPIAR FILTROS
    # ============================================
    def limpiar_filtros():
        # Marcar que se necesita reset
        st.session_state.reset_filtros = True
        
        # Limpiar explícitamente cada filtro
        if "filtro_generica" in st.session_state:
            st.session_state.filtro_generica = []
        if "filtro_ue" in st.session_state:
            st.session_state.filtro_ue = []
        if "filtro_rubro" in st.session_state:
            st.session_state.filtro_rubro = []
        if "filtro_proyecto" in st.session_state:
            st.session_state.filtro_proyecto = []
        if "filtro_sec" in st.session_state:
            st.session_state.filtro_sec = []
        
        st.rerun()
    
    # ============================================
    # 1. FILTRO POR GENÉRICA
    # ============================================
    if "generica" in df.columns:
        st.sidebar.subheader("📂 Genérica")
        opciones = sorted(df["generica"].dropna().unique().tolist())
        
        # Usar key con session_state para control
        key = "filtro_generica"
        
        # Si se pidió reset, limpiar el valor
        if st.session_state.reset_filtros:
            st.session_state[key] = []
        
        seleccion = st.sidebar.multiselect(
            "Seleccionar Genéricas:",
            options=opciones,
            default=[],
            key=key,
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
        
        key = "filtro_ue"
        
        if st.session_state.reset_filtros:
            st.session_state[key] = []
        
        seleccion = st.sidebar.multiselect(
            "Seleccionar Unidades Ejecutoras:",
            options=opciones,
            default=[],
            key=key,
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
        
        key = "filtro_rubro"
        
        if st.session_state.reset_filtros:
            st.session_state[key] = []
        
        seleccion = st.sidebar.multiselect(
            "Seleccionar Rubros:",
            options=opciones,
            default=[],
            key=key,
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
        
        key = "filtro_proyecto"
        
        if st.session_state.reset_filtros:
            st.session_state[key] = []
        
        seleccion = st.sidebar.multiselect(
            "Seleccionar Proyectos/Actividades:",
            options=opciones,
            default=[],
            key=key,
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
        
        key = "filtro_sec"
        
        if st.session_state.reset_filtros:
            st.session_state[key] = []
        
        seleccion = st.sidebar.multiselect(
            "Seleccionar Secuencias Funcionales:",
            options=opciones,
            default=[],
            key=key,
            placeholder="Ninguna seleccionada = mostrar todas"
        )
        
        if seleccion:
            df_filtrado = df_filtrado[df_filtrado[col_sec_func].isin(seleccion)]
    
    # ============================================
    # DESPUÉS DE PROCESAR, RESETEAR LA BANDERA
    # ============================================
    if st.session_state.reset_filtros:
        st.session_state.reset_filtros = False
    
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
    
    # Botón de limpieza
    if st.sidebar.button("🗑️ Limpiar todos los filtros", use_container_width=True):
        limpiar_filtros()
    
    return df_filtrado

# components/sidebar.py
import streamlit as st
from config import LOGO_URL

def mostrar_logo():
    st.sidebar.image(LOGO_URL, width=250)

def crear_filtros(df):
    """
    Crea los filtros en la barra lateral con selección múltiple
    Devuelve el dataframe filtrado
    """
    st.sidebar.header("🔍 Filtros")
    
    # Inicializar session_state para los filtros
    if "filtros_aplicados" not in st.session_state:
        st.session_state.filtros_aplicados = False
    
    df_filtrado = df.copy()
    
    # ============================================
    # 1. FILTRO POR GENÉRICA (múltiple)
    # ============================================
    if "generica" in df.columns:
        st.sidebar.subheader("📂 Genérica")
        genericas_opciones = sorted(df["generica"].dropna().unique().tolist())
        
        # Usar session_state para mantener la selección
        key_genericas = "filtro_genericas"
        if key_genericas not in st.session_state:
            st.session_state[key_genericas] = ["TODAS"]
        
        seleccion_genericas = st.sidebar.multiselect(
            "Seleccionar Genéricas:",
            options=["TODAS"] + genericas_opciones,
            default=st.session_state[key_genericas],
            key=key_genericas
        )
        
        if "TODAS" not in seleccion_genericas and seleccion_genericas:
            df_filtrado = df_filtrado[df_filtrado["generica"].isin(seleccion_genericas)]
    
    # ============================================
    # 2. FILTRO POR UNIDAD EJECUTORA (múltiple)
    # ============================================
    if "unidad_ejecutora" in df.columns:
        st.sidebar.subheader("🏛️ Unidad Ejecutora")
        ue_opciones = sorted(df["unidad_ejecutora"].dropna().unique().tolist())
        
        key_ue = "filtro_ue"
        if key_ue not in st.session_state:
            st.session_state[key_ue] = ["TODAS"]
        
        seleccion_ue = st.sidebar.multiselect(
            "Seleccionar Unidades Ejecutoras:",
            options=["TODAS"] + ue_opciones,
            default=st.session_state[key_ue],
            key=key_ue
        )
        
        if "TODAS" not in seleccion_ue and seleccion_ue:
            df_filtrado = df_filtrado[df_filtrado["unidad_ejecutora"].isin(seleccion_ue)]
    
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
        rubro_opciones = sorted(df[col_rubro].dropna().unique().tolist())
        
        key_rubro = "filtro_rubro"
        if key_rubro not in st.session_state:
            st.session_state[key_rubro] = ["TODAS"]
        
        seleccion_rubro = st.sidebar.multiselect(
            "Seleccionar Rubros:",
            options=["TODAS"] + rubro_opciones,
            default=st.session_state[key_rubro],
            key=key_rubro
        )
        
        if "TODAS" not in seleccion_rubro and seleccion_rubro:
            df_filtrado = df_filtrado[df_filtrado[col_rubro].isin(seleccion_rubro)]
    
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
        proyecto_opciones = sorted(df[col_proyecto].dropna().unique().tolist())
        
        if len(proyecto_opciones) > 100:
            proyecto_opciones = proyecto_opciones[:100]
        
        key_proyecto = "filtro_proyecto"
        if key_proyecto not in st.session_state:
            st.session_state[key_proyecto] = ["TODAS"]
        
        seleccion_proyecto = st.sidebar.multiselect(
            "Seleccionar Proyectos:",
            options=["TODAS"] + proyecto_opciones,
            default=st.session_state[key_proyecto],
            key=key_proyecto
        )
        
        if "TODAS" not in seleccion_proyecto and seleccion_proyecto:
            df_filtrado = df_filtrado[df_filtrado[col_proyecto].isin(seleccion_proyecto)]
    
    # ============================================
    # 5. FILTRO POR SEC_FUNC
    # ============================================
    col_sec_func = None
    for col in df.columns:
        if any(p in col.lower() for p in ["sec_func", "secfunc", "secuencia"]):
            col_sec_func = col
            break
    
    if col_sec_func:
        st.sidebar.subheader("🔢 Secuencia Funcional")
        sec_opciones = sorted(df[col_sec_func].dropna().unique().tolist())
        
        key_sec = "filtro_sec"
        if key_sec not in st.session_state:
            st.session_state[key_sec] = ["TODAS"]
        
        seleccion_sec = st.sidebar.multiselect(
            "Seleccionar Secuencias:",
            options=["TODAS"] + sec_opciones,
            default=st.session_state[key_sec],
            key=key_sec
        )
        
        if "TODAS" not in seleccion_sec and seleccion_sec:
            df_filtrado = df_filtrado[df_filtrado[col_sec_func].isin(seleccion_sec)]
    
    # ============================================
    # MOSTRAR RESUMEN Y BOTÓN DE ACTUALIZACIÓN
    # ============================================
    st.sidebar.markdown("---")
    st.sidebar.metric("📊 Registros mostrados", f"{len(df_filtrado):,}")
    
    # Botón para aplicar filtros (fuerza la actualización)
    if st.sidebar.button("🔄 Aplicar Filtros", type="primary", use_container_width=True):
        st.session_state.filtros_aplicados = True
        st.rerun()
    
    # Botón para limpiar todos los filtros
    if st.sidebar.button("🗑️ Limpiar todos los filtros", use_container_width=True):
        # Limpiar session_state de filtros
        for key in list(st.session_state.keys()):
            if key.startswith("filtro_"):
                del st.session_state[key]
        st.session_state.filtros_aplicados = False
        st.rerun()
    
    return df_filtrado

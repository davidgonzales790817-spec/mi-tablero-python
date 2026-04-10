# components/sidebar.py
import streamlit as st
from config import LOGO_URL

def mostrar_logo():
    st.sidebar.image(LOGO_URL, width=250)

def crear_filtros(df):
    """
    Crea los filtros en la barra lateral con selección múltiple intuitiva
    Devuelve el dataframe filtrado
    """
    st.sidebar.header("🔍 Filtros")
    
    # Inicializar session_state para los filtros si no existen
    if "filtros_inicializados" not in st.session_state:
        st.session_state.filtros_inicializados = True
        st.session_state.filtros_aplicados = {}
    
    df_filtrado = df.copy()
    
    # Diccionario para almacenar selecciones
    selecciones = {}
    
    # ============================================
    # 1. FILTRO POR GENÉRICA
    # ============================================
    if "generica" in df.columns:
        st.sidebar.subheader("📂 Genérica")
        genericas_opciones = sorted(df["generica"].dropna().unique().tolist())
        
        # Usar multiselect con checkboxes (sin opción "TODAS" separada)
        seleccion_genericas = st.sidebar.multiselect(
            "Seleccionar Genéricas:",
            options=genericas_opciones,
            default=genericas_opciones,  # Por defecto, todas seleccionadas
            help="Seleccione una o múltiples genéricas. Vacío = Todas"
        )
        
        # Si hay selección, filtrar
        if seleccion_genericas:
            df_filtrado = df_filtrado[df_filtrado["generica"].isin(seleccion_genericas)]
        
        selecciones["generica"] = seleccion_genericas
    
    # ============================================
    # 2. FILTRO POR UNIDAD EJECUTORA
    # ============================================
    if "unidad_ejecutora" in df.columns:
        st.sidebar.subheader("🏛️ Unidad Ejecutora")
        ue_opciones = sorted(df["unidad_ejecutora"].dropna().unique().tolist())
        
        seleccion_ue = st.sidebar.multiselect(
            "Seleccionar Unidades Ejecutoras:",
            options=ue_opciones,
            default=ue_opciones,
            help="Seleccione una o múltiples unidades. Vacío = Todas"
        )
        
        if seleccion_ue:
            df_filtrado = df_filtrado[df_filtrado["unidad_ejecutora"].isin(seleccion_ue)]
        
        selecciones["unidad_ejecutora"] = seleccion_ue
    
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
        
        seleccion_rubro = st.sidebar.multiselect(
            "Seleccionar Rubros:",
            options=rubro_opciones,
            default=rubro_opciones,
            help="Seleccione uno o múltiples rubros. Vacío = Todos"
        )
        
        if seleccion_rubro:
            df_filtrado = df_filtrado[df_filtrado[col_rubro].isin(seleccion_rubro)]
        
        selecciones["rubro"] = seleccion_rubro
    
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
        
        # Limitar a 100 opciones para no saturar
        if len(proyecto_opciones) > 100:
            proyecto_opciones = proyecto_opciones[:100]
            st.sidebar.caption(f"⚠️ Mostrando 100 de {len(df[col_proyecto].dropna().unique())} proyectos")
        
        seleccion_proyecto = st.sidebar.multiselect(
            "Seleccionar Proyectos/Actividades:",
            options=proyecto_opciones,
            default=proyecto_opciones,
            help="Seleccione uno o múltiples proyectos. Vacío = Todos"
        )
        
        if seleccion_proyecto:
            df_filtrado = df_filtrado[df_filtrado[col_proyecto].isin(seleccion_proyecto)]
        
        selecciones["proyecto"] = seleccion_proyecto
    
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
        sec_opciones = sorted(df[col_sec_func].dropna().unique().tolist())
        
        seleccion_sec = st.sidebar.multiselect(
            "Seleccionar Secuencias Funcionales:",
            options=sec_opciones,
            default=sec_opciones,
            help="Seleccione una o múltiples secuencias. Vacío = Todas"
        )
        
        if seleccion_sec:
            df_filtrado = df_filtrado[df_filtrado[col_sec_func].isin(seleccion_sec)]
        
        selecciones["sec_func"] = seleccion_sec
    
    # ============================================
    # RESULTADO Y BOTONES DE ACCIÓN
    # ============================================
    st.sidebar.markdown("---")
    
    # Mostrar resumen
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("📊 Registros totales", f"{len(df):,}")
    with col2:
        st.metric("✅ Registros filtrados", f"{len(df_filtrado):,}")
    
    # Barra de progreso
    if len(df) > 0:
        porcentaje = (len(df_filtrado) / len(df)) * 100
        st.sidebar.progress(porcentaje / 100)
        st.sidebar.caption(f"{porcentaje:.1f}% del total")
    
    st.sidebar.markdown("---")
    
    # Botón para limpiar todos los filtros
    if st.sidebar.button("🗑️ Limpiar todos los filtros", use_container_width=True):
        # Forzar reinicio de la aplicación
        st.cache_data.clear()
        st.rerun()
    
    # Mostrar qué filtros están activos
    filtros_activos = []
    for nombre, seleccion in selecciones.items():
        if seleccion and len(seleccion) < len(df[nombre].unique() if nombre in df.columns else []):
            filtros_activos.append(f"{nombre}: {len(seleccion)} seleccionados")
    
    if filtros_activos:
        with st.sidebar.expander("📋 Filtros activos", expanded=False):
            for f in filtros_activos:
                st.caption(f"• {f}")
    
    return df_filtrado

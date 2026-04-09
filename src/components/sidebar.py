# components/sidebar.py
import streamlit as st
from config import LOGO_URL

def mostrar_logo():
    """Muestra el logo institucional en la barra lateral"""
    st.sidebar.image(LOGO_URL, width=250)

def crear_filtros(df):
    """
    Crea los filtros en la barra lateral con selección múltiple
    Devuelve el dataframe filtrado y los valores seleccionados
    """
    st.sidebar.header("🔍 Filtros")
    
    # Inicializar df_filtrado
    df_filtrado = df.copy()
    
    # ============================================
    # 1. FILTRO POR GENÉRICA (múltiple)
    # ============================================
    if "generica" in df.columns:
        st.sidebar.subheader("📂 Genérica")
        genericas_opciones = sorted(df["generica"].dropna().unique().tolist())
        
        # Selector múltiple con "Todas" como opción especial
        seleccion_genericas = st.sidebar.multiselect(
            "Seleccionar Genéricas:",
            options=["TODAS"] + genericas_opciones,
            default=["TODAS"],
            help="Puede seleccionar una o múltiples genéricas. 'TODAS' selecciona todas."
        )
        
        # Aplicar filtro
        if "TODAS" not in seleccion_genericas and seleccion_genericas:
            df_filtrado = df_filtrado[df_filtrado["generica"].isin(seleccion_genericas)]
    
    # ============================================
    # 2. FILTRO POR UNIDAD EJECUTORA (múltiple)
    # ============================================
    if "unidad_ejecutora" in df.columns:
        st.sidebar.subheader("🏛️ Unidad Ejecutora")
        ue_opciones = sorted(df["unidad_ejecutora"].dropna().unique().tolist())
        
        seleccion_ue = st.sidebar.multiselect(
            "Seleccionar Unidades Ejecutoras:",
            options=["TODAS"] + ue_opciones,
            default=["TODAS"],
            help="Puede seleccionar una o múltiples unidades ejecutoras"
        )
        
        if "TODAS" not in seleccion_ue and seleccion_ue:
            df_filtrado = df_filtrado[df_filtrado["unidad_ejecutora"].isin(seleccion_ue)]
    
    # ============================================
    # 3. FILTRO POR RUBRO DE FINANCIAMIENTO (múltiple)
    # ============================================
    # Posibles nombres de columna: rubro, financiamiento, fuente_financiamiento, rubro_financiamiento
    col_rubro = None
    for col in df.columns:
        if any(palabra in col.lower() for palabra in ["rubro", "financiamiento", "fuente"]):
            col_rubro = col
            break
    
    if col_rubro:
        st.sidebar.subheader("💰 Rubro de Financiamiento")
        rubro_opciones = sorted(df[col_rubro].dropna().unique().tolist())
        
        seleccion_rubro = st.sidebar.multiselect(
            "Seleccionar Rubros:",
            options=["TODAS"] + rubro_opciones,
            default=["TODAS"],
            help="Filtrar por rubro o fuente de financiamiento"
        )
        
        if "TODAS" not in seleccion_rubro and seleccion_rubro:
            df_filtrado = df_filtrado[df_filtrado[col_rubro].isin(seleccion_rubro)]
    
    # ============================================
    # 4. FILTRO POR PROYECTO O ACTIVIDAD (múltiple)
    # ============================================
    # Posibles nombres de columna: proyecto, actividad, proyecto_actividad, descripcion_proyecto
    col_proyecto = None
    for col in df.columns:
        if any(palabra in col.lower() for palabra in ["proyecto", "actividad", "proyecto_actividad"]):
            col_proyecto = col
            break
    
    if col_proyecto:
        st.sidebar.subheader("📋 Proyecto / Actividad")
        proyecto_opciones = sorted(df[col_proyecto].dropna().unique().tolist())
        
        # Limitar a 100 opciones para no saturar (mostrar advertencia si hay muchas)
        if len(proyecto_opciones) > 100:
            st.sidebar.warning(f"Hay {len(proyecto_opciones)} proyectos. Mostrando los 100 más comunes.")
            # Contar frecuencias y tomar los más comunes
            freq = df[col_proyecto].value_counts()
            proyecto_opciones = freq.head(100).index.tolist()
        
        seleccion_proyecto = st.sidebar.multiselect(
            "Seleccionar Proyectos/Actividades:",
            options=["TODAS"] + proyecto_opciones,
            default=["TODAS"],
            help="Puede seleccionar uno o múltiples proyectos/actividades"
        )
        
        if "TODAS" not in seleccion_proyecto and seleccion_proyecto:
            df_filtrado = df_filtrado[df_filtrado[col_proyecto].isin(seleccion_proyecto)]
    
    # ============================================
    # 5. FILTRO POR SEC_FUNC (múltiple)
    # ============================================
    # Posibles nombres de columna: sec_func, sec_funcional, secuencia_funcional
    col_sec_func = None
    for col in df.columns:
        if any(palabra in col.lower() for palabra in ["sec_func", "secfunc", "secuencia_func", "funcional"]):
            col_sec_func = col
            break
    
    if col_sec_func:
        st.sidebar.subheader("🔢 Secuencia Funcional (Sec_Func)")
        sec_opciones = sorted(df[col_sec_func].dropna().unique().tolist())
        
        seleccion_sec = st.sidebar.multiselect(
            "Seleccionar Secuencias Funcionales:",
            options=["TODAS"] + sec_opciones,
            default=["TODAS"],
            help="Filtrar por secuencia funcional"
        )
        
        if "TODAS" not in seleccion_sec and seleccion_sec:
            df_filtrado = df_filtrado[df_filtrado[col_sec_func].isin(seleccion_sec)]
    
    # ============================================
    # MOSTRAR RESUMEN DE FILTROS ACTIVOS
    # ============================================
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Resumen de filtros")
    
    # Contar registros antes y después
    registros_iniciales = len(df)
    registros_filtrados = len(df_filtrado)
    
    st.sidebar.metric(
        "Registros mostrados",
        f"{registros_filtrados:,}",
        delta=f"{registros_filtrados - registros_iniciales:,}",
        delta_color="off"
    )
    
    # Mostrar porcentaje
    if registros_iniciales > 0:
        porcentaje = (registros_filtrados / registros_iniciales) * 100
        st.sidebar.progress(porcentaje / 100)
        st.sidebar.caption(f"{porcentaje:.1f}% del total")
    
    # Botón para limpiar todos los filtros
    if st.sidebar.button("🗑️ Limpiar todos los filtros", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    return df_filtrado

def obtener_columnas_disponibles(df):
    """
    Función auxiliar para mostrar qué columnas están disponibles
    Útil para depuración
    """
    with st.sidebar.expander("📋 Columnas disponibles en el archivo"):
        columnas = df.columns.tolist()
        st.write(columnas)

# components/sidebar.py
import streamlit as st
from config import LOGO_URL

def mostrar_logo():
    st.sidebar.image(LOGO_URL, width=250)

def crear_filtro_con_busqueda(opciones, titulo, key_prefix, df, columna, df_filtrado):
    """
    Crea un filtro con buscador y checkboxes
    Retorna el dataframe filtrado actualizado
    """
    st.sidebar.subheader(titulo)
    
    # Buscador
    busqueda = st.sidebar.text_input(
        "🔍 Buscar",
        placeholder=f"Filtrar {titulo.lower()}...",
        key=f"buscar_{key_prefix}"
    )
    
    # Filtrar opciones por búsqueda
    opciones_filtradas = opciones.copy()
    if busqueda:
        opciones_filtradas = [opt for opt in opciones_filtradas if busqueda.lower() in opt.lower()]
    
    # Estado de selección en session_state
    estado_key = f"sel_{key_prefix}"
    if estado_key not in st.session_state:
        st.session_state[estado_key] = []  # Vacío = mostrar todos
    
    # Botones de selección rápida
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("☑ Seleccionar todo", key=f"select_all_{key_prefix}", use_container_width=True):
            st.session_state[estado_key] = opciones.copy()
            st.rerun()
    with col2:
        if st.button("☐ Limpiar todo", key=f"clear_all_{key_prefix}", use_container_width=True):
            st.session_state[estado_key] = []
            st.rerun()
    
    # Mostrar opciones con checkboxes (usando contenedor con scroll)
    with st.sidebar.container():
        # Scroll para muchas opciones
        st.markdown(f"""
        <style>
        div[data-testid="stVerticalBlock"] div:has(> div.element-container:has(> label)) {{
            max-height: 250px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 10px;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        for opcion in opciones_filtradas:
            esta_seleccionada = opcion in st.session_state[estado_key]
            seleccionada = st.checkbox(
                opcion,
                value=esta_seleccionada,
                key=f"chk_{key_prefix}_{opcion}"
            )
            if seleccionada and opcion not in st.session_state[estado_key]:
                st.session_state[estado_key].append(opcion)
            elif not seleccionada and opcion in st.session_state[estado_key]:
                st.session_state[estado_key].remove(opcion)
    
    # Aplicar filtro SOLO si hay selecciones
    if st.session_state[estado_key]:
        df_filtrado = df_filtrado[df_filtrado[columna].isin(st.session_state[estado_key])]
    
    return df_filtrado

def crear_filtros(df):
    """
    Crea los filtros en la barra lateral con checkboxes y buscador
    """
    st.sidebar.header("🔍 Filtros")
    
    df_filtrado = df.copy()
    
    # ============================================
    # 1. FILTRO POR GENÉRICA
    # ============================================
    if "generica" in df.columns:
        opciones = sorted(df["generica"].dropna().unique().tolist())
        df_filtrado = crear_filtro_con_busqueda(
            opciones, "📂 Genérica", "generica", 
            df, "generica", df_filtrado
        )
    
    # ============================================
    # 2. FILTRO POR UNIDAD EJECUTORA
    # ============================================
    if "unidad_ejecutora" in df.columns:
        opciones = sorted(df["unidad_ejecutora"].dropna().unique().tolist())
        df_filtrado = crear_filtro_con_busqueda(
            opciones, "🏛️ Unidad Ejecutora", "ue",
            df, "unidad_ejecutora", df_filtrado
        )
    
    # ============================================
    # 3. FILTRO POR RUBRO DE FINANCIAMIENTO
    # ============================================
    col_rubro = None
    for col in df.columns:
        if any(p in col.lower() for p in ["rubro", "financiamiento", "fuente"]):
            col_rubro = col
            break
    
    if col_rubro:
        opciones = sorted(df[col_rubro].dropna().unique().tolist())
        df_filtrado = crear_filtro_con_busqueda(
            opciones, "💰 Rubro de Financiamiento", "rubro",
            df, col_rubro, df_filtrado
        )
    
    # ============================================
    # 4. FILTRO POR PROYECTO/ACTIVIDAD
    # ============================================
    col_proyecto = None
    for col in df.columns:
        if any(p in col.lower() for p in ["proyecto", "actividad"]):
            col_proyecto = col
            break
    
    if col_proyecto:
        opciones = sorted(df[col_proyecto].dropna().unique().tolist())
        # Limitar a 200 opciones para rendimiento
        if len(opciones) > 200:
            st.sidebar.warning(f"Hay {len(opciones)} proyectos. Mostrando los 200 más recientes.")
            opciones = opciones[:200]
        
        df_filtrado = crear_filtro_con_busqueda(
            opciones, "📋 Proyecto / Actividad", "proyecto",
            df, col_proyecto, df_filtrado
        )
    
    # ============================================
    # 5. FILTRO POR SEC_FUNC
    # ============================================
    col_sec_func = None
    for col in df.columns:
        if any(p in col.lower() for p in ["sec_func", "secfunc", "secuencia", "funcional"]):
            col_sec_func = col
            break
    
    if col_sec_func:
        opciones = sorted(df[col_sec_func].dropna().unique().tolist())
        df_filtrado = crear_filtro_con_busqueda(
            opciones, "🔢 Secuencia Funcional", "sec_func",
            df, col_sec_func, df_filtrado
        )
    
    # ============================================
    # RESULTADO
    # ============================================
    st.sidebar.markdown("---")
    
    # Mostrar resumen
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("📊 Total", f"{len(df):,}")
    with col2:
        st.metric("✅ Mostrados", f"{len(df_filtrado):,}")
    
    # Barra de progreso
    if len(df) > 0:
        porcentaje = (len(df_filtrado) / len(df)) * 100
        st.sidebar.progress(porcentaje / 100)
    
    # Botón para resetear todos los filtros
    if st.sidebar.button("🗑️ Resetear todos los filtros", use_container_width=True):
        # Limpiar todas las selecciones en session_state
        for key in list(st.session_state.keys()):
            if key.startswith("sel_"):
                st.session_state[key] = []
            if key.startswith("chk_"):
                del st.session_state[key]
            if key.startswith("buscar_"):
                st.session_state[key] = ""
        st.rerun()
    
    return df_filtrado

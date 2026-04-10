# components/sidebar.py
import streamlit as st
from config import LOGO_URL

def mostrar_logo():
    st.sidebar.image(LOGO_URL, width=250)

def crear_filtros(df):
    """
    Crea los filtros en la barra lateral con checkboxes y buscador
    """
    st.sidebar.header("🔍 Filtros")
    
    df_filtrado = df.copy()
    
    # Inicializar session_state para todos los filtros
    if "filtros_estado" not in st.session_state:
        st.session_state.filtros_estado = {}
    
    # ============================================
    # 1. FILTRO POR GENÉRICA
    # ============================================
    if "generica" in df.columns:
        st.sidebar.subheader("📂 Genérica")
        
        opciones = sorted(df["generica"].dropna().unique().tolist())
        key_base = "filtro_generica"
        
        # Buscador
        busqueda = st.sidebar.text_input("🔍 Buscar", key=f"buscar_{key_base}", placeholder="Filtrar genéricas...")
        
        # Filtrar opciones
        opciones_filtradas = [opt for opt in opciones if busqueda.lower() in opt.lower()] if busqueda else opciones
        
        # Botones
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("☑ Seleccionar todo", key=f"select_all_{key_base}"):
                for opt in opciones:
                    st.session_state.filtros_estado[f"chk_{key_base}_{opt}"] = True
                st.rerun()
        with col2:
            if st.button("☐ Limpiar todo", key=f"clear_all_{key_base}"):
                for opt in opciones:
                    st.session_state.filtros_estado[f"chk_{key_base}_{opt}"] = False
                st.rerun()
        
        # Checkboxes
        seleccionados = []
        for opt in opciones_filtradas:
            chk_key = f"chk_{key_base}_{opt}"
            if chk_key not in st.session_state.filtros_estado:
                st.session_state.filtros_estado[chk_key] = False
            
            checked = st.checkbox(opt, value=st.session_state.filtros_estado[chk_key], key=chk_key)
            if checked:
                seleccionados.append(opt)
        
        # Aplicar filtro
        if seleccionados:
            df_filtrado = df_filtrado[df_filtrado["generica"].isin(seleccionados)]
    
    # ============================================
    # 2. FILTRO POR UNIDAD EJECUTORA
    # ============================================
    if "unidad_ejecutora" in df.columns:
        st.sidebar.subheader("🏛️ Unidad Ejecutora")
        
        opciones = sorted(df["unidad_ejecutora"].dropna().unique().tolist())
        key_base = "filtro_ue"
        
        busqueda = st.sidebar.text_input("🔍 Buscar", key=f"buscar_{key_base}", placeholder="Filtrar unidades...")
        opciones_filtradas = [opt for opt in opciones if busqueda.lower() in opt.lower()] if busqueda else opciones
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("☑ Seleccionar todo", key=f"select_all_{key_base}"):
                for opt in opciones:
                    st.session_state.filtros_estado[f"chk_{key_base}_{opt}"] = True
                st.rerun()
        with col2:
            if st.button("☐ Limpiar todo", key=f"clear_all_{key_base}"):
                for opt in opciones:
                    st.session_state.filtros_estado[f"chk_{key_base}_{opt}"] = False
                st.rerun()
        
        seleccionados = []
        for opt in opciones_filtradas:
            chk_key = f"chk_{key_base}_{opt}"
            if chk_key not in st.session_state.filtros_estado:
                st.session_state.filtros_estado[chk_key] = False
            
            checked = st.checkbox(opt, value=st.session_state.filtros_estado[chk_key], key=chk_key)
            if checked:
                seleccionados.append(opt)
        
        if seleccionados:
            df_filtrado = df_filtrado[df_filtrado["unidad_ejecutora"].isin(seleccionados)]
    
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
        key_base = "filtro_rubro"
        
        busqueda = st.sidebar.text_input("🔍 Buscar", key=f"buscar_{key_base}", placeholder="Filtrar rubros...")
        opciones_filtradas = [opt for opt in opciones if busqueda.lower() in opt.lower()] if busqueda else opciones
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("☑ Seleccionar todo", key=f"select_all_{key_base}"):
                for opt in opciones:
                    st.session_state.filtros_estado[f"chk_{key_base}_{opt}"] = True
                st.rerun()
        with col2:
            if st.button("☐ Limpiar todo", key=f"clear_all_{key_base}"):
                for opt in opciones:
                    st.session_state.filtros_estado[f"chk_{key_base}_{opt}"] = False
                st.rerun()
        
        seleccionados = []
        for opt in opciones_filtradas:
            chk_key = f"chk_{key_base}_{opt}"
            if chk_key not in st.session_state.filtros_estado:
                st.session_state.filtros_estado[chk_key] = False
            
            checked = st.checkbox(opt, value=st.session_state.filtros_estado[chk_key], key=chk_key)
            if checked:
                seleccionados.append(opt)
        
        if seleccionados:
            df_filtrado = df_filtrado[df_filtrado[col_rubro].isin(seleccionados)]
    
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
            st.sidebar.warning(f"Hay {len(opciones)} proyectos. Mostrando los 100 primeros.")
            opciones = opciones[:100]
        
        key_base = "filtro_proyecto"
        
        busqueda = st.sidebar.text_input("🔍 Buscar", key=f"buscar_{key_base}", placeholder="Filtrar proyectos...")
        opciones_filtradas = [opt for opt in opciones if busqueda.lower() in opt.lower()] if busqueda else opciones
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("☑ Seleccionar todo", key=f"select_all_{key_base}"):
                for opt in opciones:
                    st.session_state.filtros_estado[f"chk_{key_base}_{opt}"] = True
                st.rerun()
        with col2:
            if st.button("☐ Limpiar todo", key=f"clear_all_{key_base}"):
                for opt in opciones:
                    st.session_state.filtros_estado[f"chk_{key_base}_{opt}"] = False
                st.rerun()
        
        seleccionados = []
        for opt in opciones_filtradas:
            chk_key = f"chk_{key_base}_{opt}"
            if chk_key not in st.session_state.filtros_estado:
                st.session_state.filtros_estado[chk_key] = False
            
            checked = st.checkbox(opt, value=st.session_state.filtros_estado[chk_key], key=chk_key)
            if checked:
                seleccionados.append(opt)
        
        if seleccionados:
            df_filtrado = df_filtrado[df_filtrado[col_proyecto].isin(seleccionados)]
    
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
        key_base = "filtro_sec"
        
        busqueda = st.sidebar.text_input("🔍 Buscar", key=f"buscar_{key_base}", placeholder="Filtrar secuencias...")
        opciones_filtradas = [opt for opt in opciones if busqueda.lower() in opt.lower()] if busqueda else opciones
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("☑ Seleccionar todo", key=f"select_all_{key_base}"):
                for opt in opciones:
                    st.session_state.filtros_estado[f"chk_{key_base}_{opt}"] = True
                st.rerun()
        with col2:
            if st.button("☐ Limpiar todo", key=f"clear_all_{key_base}"):
                for opt in opciones:
                    st.session_state.filtros_estado[f"chk_{key_base}_{opt}"] = False
                st.rerun()
        
        seleccionados = []
        for opt in opciones_filtradas:
            chk_key = f"chk_{key_base}_{opt}"
            if chk_key not in st.session_state.filtros_estado:
                st.session_state.filtros_estado[chk_key] = False
            
            checked = st.checkbox(opt, value=st.session_state.filtros_estado[chk_key], key=chk_key)
            if checked:
                seleccionados.append(opt)
        
        if seleccionados:
            df_filtrado = df_filtrado[df_filtrado[col_sec_func].isin(seleccionados)]
    
    # ============================================
    # RESULTADO Y RESET
    # ============================================
    st.sidebar.markdown("---")
    
    # Mostrar resumen
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("📊 Total", f"{len(df):,}")
    with col2:
        st.metric("✅ Mostrados", f"{len(df_filtrado):,}")
    
    if len(df) > 0:
        porcentaje = (len(df_filtrado) / len(df)) * 100
        st.sidebar.progress(porcentaje / 100)
    
    # Botón reset global
    if st.sidebar.button("🗑️ Resetear todos los filtros", use_container_width=True):
        st.session_state.filtros_estado = {}
        st.rerun()
    
    return df_filtrado

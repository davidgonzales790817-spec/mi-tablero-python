# components/programacion_form.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from config import MESES

def inicializar_programacion(genericas_ordenadas):
    """
    Inicializa la estructura de datos para la programación mensual
    """
    if "programacion_mensual" not in st.session_state:
        # Crear DataFrame con genéricas como índice y meses como columnas
        df_prog = pd.DataFrame(
            0.0,
            index=genericas_ordenadas,
            columns=MESES
        )
        st.session_state.programacion_mensual = df_prog
    
    # Si hay nuevas genéricas, agregarlas
    df_actual = st.session_state.programacion_mensual
    for gen in genericas_ordenadas:
        if gen not in df_actual.index:
            # Agregar nueva fila con ceros
            nueva_fila = pd.DataFrame(0.0, index=[gen], columns=MESES)
            df_actual = pd.concat([df_actual, nueva_fila])
    
    # Limpiar genéricas que ya no existen
    df_actual = df_actual[df_actual.index.isin(genericas_ordenadas + list(df_actual.index))]
    
    st.session_state.programacion_mensual = df_actual
    return st.session_state.programacion_mensual

def guardar_programacion_csv(df_programacion):
    """
    Guarda la programación en un archivo CSV dentro de Respaldo_Data
    """
    try:
        # Crear carpeta si no existe
        os.makedirs("Respaldo_Data", exist_ok=True)
        
        # Guardar como "programacion_actual.csv"
        df_programacion.to_csv("Respaldo_Data/programacion_actual.csv")
        
        return True, "Respaldo_Data/programacion_actual.csv"
    except Exception as e:
        return False, str(e)

def cargar_programacion_csv():
    """
    Carga la última programación guardada
    """
    try:
        ruta = "Respaldo_Data/programacion_actual.csv"
        if os.path.exists(ruta):
            df = pd.read_csv(ruta, index_col=0)
            return True, df
        return False, "No hay programación guardada"
    except Exception as e:
        return False, str(e)

def mostrar_formulario_programacion(genericas_ordenadas):
    """
    Muestra el formulario para ingresar programación mensual por genérica
    """
    # Inicializar programación
    df_programacion = inicializar_programacion(genericas_ordenadas)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 Programación Mensual")
    
    # Botón para abrir el formulario
    with st.sidebar.expander("✏️ Ingresar Programación por Genérica", expanded=False):
        st.markdown("### Programación de Metas Mensuales")
        st.markdown("Ingrese los montos programados (en Soles) para cada genérica y mes:")
        
        # Opciones de carga/guardado
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📂 Cargar última programación"):
                success, result = cargar_programacion_csv()
                if success:
                    st.session_state.programacion_mensual = result
                    st.success("Programación cargada correctamente")
                    st.rerun()
                else:
                    st.warning(result)
        
        with col2:
            if st.button("🔄 Reiniciar todo a cero"):
                df_programacion = pd.DataFrame(0.0, index=genericas_ordenadas, columns=MESES)
                st.session_state.programacion_mensual = df_programacion
                st.success("Programación reiniciada a cero")
                st.rerun()
        
        st.markdown("---")
        
        # Formulario editable
        df_editado = df_programacion.copy()
        
        # Para cada genérica, crear una fila de inputs
        for gen in genericas_ordenadas:
            st.markdown(f"**{gen}**")
            cols = st.columns(len(MESES))
            for i, mes in enumerate(MESES):
                valor_actual = df_programacion.loc[gen, mes] if gen in df_programacion.index else 0
                with cols[i]:
                    nuevo_valor = st.number_input(
                        mes[:3],  # Abreviatura del mes
                        value=float(valor_actual),
                        step=1000.0,
                        format="%.0f",
                        key=f"prog_{gen}_{mes}",
                        label_visibility="collapsed"
                    )
                    df_editado.loc[gen, mes] = nuevo_valor
            st.markdown("---")
        
        # Botones de acción
        col_guardar, col_cancelar = st.columns(2)
        with col_guardar:
            if st.button("💾 Guardar Programación", type="primary", use_container_width=True):
                st.session_state.programacion_mensual = df_editado
                success, result = guardar_programacion_csv(df_editado)
                if success:
                    st.success(f"Programación guardada correctamente")
                else:
                    st.error(f"Error al guardar: {result}")
                st.rerun()
        
        with col_cancelar:
            if st.button("❌ Cancelar", use_container_width=True):
                st.rerun()
    
    # Mostrar resumen de la programación actual
    if "programacion_mensual" in st.session_state:
        with st.sidebar.expander("📊 Resumen de Programación Actual", expanded=False):
            df_prog = st.session_state.programacion_mensual
            
            # Total por genérica
            st.markdown("**Total por Genérica:**")
            for gen in df_prog.index:
                total_gen = df_prog.loc[gen].sum()
                st.metric(gen, f"S/ {total_gen:,.0f}")
            
            st.markdown("---")
            
            # Total mensual (para la línea)
            totales_mensuales = df_prog.sum(axis=0)
            st.markdown("**Meta Total Mensual (Línea):**")
            for mes in MESES:
                st.metric(mes, f"S/ {totales_mensuales[mes]:,.0f}")

def obtener_meta_total_mensual():
    """
    Retorna un diccionario con la meta total mensual (suma de todas las genéricas)
    """
    if "programacion_mensual" in st.session_state:
        df_prog = st.session_state.programacion_mensual
        return df_prog.sum(axis=0).to_dict()
    else:
        # Si no hay programación, retornar ceros
        return {mes: 0 for mes in MESES}

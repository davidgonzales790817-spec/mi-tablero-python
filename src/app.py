# app.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime

from config import PAGE_CONFIG, CARPETA_RESPALDO
from utils.file_handler import cargar_archivo_excel, guardar_archivo_respaldo
from utils.data_processor import DataProcessor
from components.sidebar import mostrar_logo, crear_filtros
from components.gauges import mostrar_indicadores
from components.summary_table import crear_tabla_resumen
from components.monthly_chart import crear_grafico_mensual

# Configuración de la página
st.set_page_config(**PAGE_CONFIG)

# Logo
mostrar_logo()

# Cargar archivo
archivo = cargar_archivo_excel()

# Variable para almacenar el dataframe procesado
if "df_procesado" not in st.session_state:
    st.session_state.df_procesado = None
if "columnas_devengado" not in st.session_state:
    st.session_state.columnas_devengado = []

if archivo:
    # Guardar respaldo
    ruta_archivo = guardar_archivo_respaldo(archivo)

    try:
        # Leer datos
        df = pd.read_excel(ruta_archivo)

        # Procesar datos
        procesador = DataProcessor(df)
        procesador.procesar_completo()
        df_procesado = procesador.obtener_dataframe()
        columnas_devengado = procesador.obtener_columnas_devengado()
        
        # Guardar en session_state
        st.session_state.df_procesado = df_procesado
        st.session_state.columnas_devengado = columnas_devengado

        if df_procesado.empty:
            st.warning("No hay datos válidos después del procesamiento")
            st.stop()

    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        st.exception(e)
        st.stop()

# Si hay datos procesados, mostrar la aplicación
if st.session_state.df_procesado is not None:
    df_procesado = st.session_state.df_procesado
    columnas_devengado = st.session_state.columnas_devengado
    
    # Aplicar filtros
    df_filtrado = crear_filtros(df_procesado)
    
    # Información general
    fecha_formateada = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pliego = df_procesado.get("pliego", pd.Series(["No especificado"])).iloc[0] if "pliego" in df_procesado.columns else "No especificado"
    ano_eje = df_procesado.get("ano_eje", pd.Series(["No disponible"])).iloc[0] if "ano_eje" in df_procesado.columns else "No disponible"
    
    st.title("📊 Tablero Presupuestal Interactivo")
    st.markdown(f"""
    **Entidad:** `{pliego}`  
    **Año Fiscal:** `{ano_eje}`  
    **Última actualización:** `{fecha_formateada}`  
    """)
    
    # Verificar si hay datos filtrados
    if df_filtrado.empty:
        st.warning("⚠️ No hay datos para los filtros seleccionados. Use 'Resetear todos los filtros' para ver todos los datos.")
    else:
        # ============================================
        # INDICADORES GAUGE
        # ============================================
        pim_total = df_filtrado["PIM"].sum()
        certificado_total = df_filtrado["Certificado"].sum()
        compromiso_total = df_filtrado["Compromiso_Anual"].sum()
        devengado_total = df_filtrado["Devengado_Total"].sum()
        
        mostrar_indicadores(pim_total, certificado_total, compromiso_total, devengado_total)
        
        # ============================================
        # TABLA RESUMEN
        # ============================================
        crear_tabla_resumen(df_filtrado)
        
        # ============================================
        # GRÁFICO MENSUAL
        # ============================================
        crear_grafico_mensual(df_filtrado, columnas_devengado)

else:
    st.info("👈 Por favor, cargue un archivo Excel válido para comenzar.")

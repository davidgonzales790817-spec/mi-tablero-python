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

# Cargar archivo (manual)
archivo_subido = cargar_archivo_excel()

# Variable para almacenar la ruta del archivo a procesar
ruta_archivo = None

if archivo_subido:
    # Si el usuario subió un archivo, lo guardamos en Respaldo_Data (si es posible)
    ruta_archivo = guardar_archivo_respaldo(archivo_subido)
    st.success(f"Archivo cargado: {archivo_subido.name}")
else:
    # Si no se subió ningún archivo, buscar en la carpeta de respaldo
    try:
        archivos_respaldo = [f for f in os.listdir(CARPETA_RESPALDO) 
                             if f.endswith(('.xls', '.xlsx')) and f != '.gitkeep']
        if archivos_respaldo:
            # Tomar el más reciente (por fecha de modificación)
            archivo_reciente = max(archivos_respaldo, 
                                   key=lambda f: os.path.getmtime(os.path.join(CARPETA_RESPALDO, f)))
            ruta_archivo = os.path.join(CARPETA_RESPALDO, archivo_reciente)
            st.info(f"Cargando archivo de respaldo: {archivo_reciente}")
    except Exception as e:
        st.warning(f"No se pudo acceder a la carpeta de respaldo: {e}")

# Si hay un archivo disponible, procesarlo
if ruta_archivo:
    try:
        # Leer datos
        df = pd.read_excel(ruta_archivo)

        # Procesar datos
        procesador = DataProcessor(df)
        procesador.procesar_completo()
        df_procesado = procesador.obtener_dataframe()
        columnas_devengado = procesador.obtener_columnas_devengado()

        if df_procesado.empty:
            st.warning("No hay datos válidos después del procesamiento")
            st.stop()

        # Información general
        fecha_formateada = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        pliego = df_procesado.get("pliego", pd.Series(["No especificado"])).iloc[0] if "pliego" in df_procesado.columns else "No especificado"
        ano_eje = df_procesado.get("ano_eje", pd.Series(["No disponible"])).iloc[0] if "ano_eje" in df_procesado.columns else "No disponible"

        st.title("📊 Tablero Presupuestal Interactivo")
        st.markdown(f"""
        **Entidad:** `{pliego}`  
        **Año Fiscal:** `{ano_eje}`  
        **Última actualización:** `{fecha_formateada}`  
        **Registros cargados:** `{len(df_procesado)}`
        """)

        # Aplicar filtros
        df_filtrado, _ = crear_filtros(df_procesado)

        if df_filtrado.empty:
            st.warning("No hay datos para los filtros seleccionados")
            st.stop()

        # Totales para indicadores
        pim_total = df_filtrado["PIM"].sum()
        certificado_total = df_filtrado["Certificado"].sum()
        compromiso_total = df_filtrado["Compromiso_Anual"].sum()
        devengado_total = df_filtrado["Devengado_Total"].sum()

        # Mostrar indicadores (relojes)
        mostrar_indicadores(pim_total, certificado_total, compromiso_total, devengado_total)

        # Tabla resumen
        crear_tabla_resumen(df_filtrado)

        # Gráfico mensual
        crear_grafico_mensual(df_filtrado, columnas_devengado)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        st.exception(e)
else:
    st.info("👈 Por favor, cargue un archivo Excel válido o verifique que exista un archivo de respaldo en la carpeta.")

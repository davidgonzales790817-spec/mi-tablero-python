# src/app.py
# Importa la librería Streamlit para crear interfaces web interactivas
import streamlit as st
# Importa pandas para manejo y análisis de datos en formato tabular (DataFrames)
import pandas as pd
# Importa plotly para crear gráficos interactivos y visualizaciones
import plotly.graph_objects as go
# Importa la clase 'date' del módulo datetime para trabajar con fechas
from datetime import date
# Importa módulos del sistema: sys (variables del sistema), os (operaciones del SO), re (expresiones regulares)
import sys, os, re

# Añade la carpeta actual al inicio de la ruta de búsqueda de módulos Python
sys.path.insert(0, os.path.dirname(__file__))

# Importa variables de configuración: paleta de colores, función de color por avance y meses abreviados
from config import PALETA, color_por_avance, MESES_ABREV
# Importa la clase DataProcessor para procesar datos del archivo Excel
from utils.data_processor import DataProcessor
# Importa función para calcular todos los indicadores presupuestales
from utils.indicadores import calcular_todos_indicadores
# Importa función para mostrar indicadores en formato de medidores (gauges)
from components.gauges import mostrar_indicadores
# Importa función para crear gráficos de evolución mensual
from components.monthly_chart import crear_grafico_mensual
# Importa función para crear tabla de resumen de datos
from components.summary_table import crear_tabla_resumen
# Importa funciones para crear filtros en sidebar y mostrar logo
from components.sidebar import crear_filtros, mostrar_logo
# Importa funciones para gestionar la programación presupuestal mensual
from components.programacion_form import (
    inicializar_programacion, obtener_programacion_df,
    mostrar_resumen_sidebar, mostrar_formulario_programacion,
)
# Importa función para mostrar tarjetas KPI y panel de alertas
from components.kpi_cards import grid_kpis, panel_alertas

# ════════════════════════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN INICIAL DE LA PÁGINA
# ════════════════════════════════════════════════════════════════════════════════════════════════

# Configura el título, ícono, layout y estado inicial del sidebar de la página
st.set_page_config(
    page_title="Tablero SIAF · IPEN",  # Título que aparece en la pestaña del navegador
    page_icon="📊",  # Ícono que aparece en la pestaña del navegador
    layout="wide",  # Usa el ancho completo de la pantalla disponible
    initial_sidebar_state="expanded"  # El sidebar aparece expandido por defecto
)

# ════════════════════════════════════════════════════════════════════════════════════════════════
# INICIALIZACIÓN DEL SESSION STATE
# ════════════════════════════════════════════════════════════════════════════════════════════════

# Define un diccionario con los valores por defecto para las variables de sesión
session_defaults = {
    "df": None,  # DataFrame cargado del archivo (inicialmente vacío)
    "df_procesado": None,  # DataFrame después del procesamiento (inicialmente vacío)
    "columnas": {},  # Diccionario que mapea los nombres de columnas procesadas
    "cols_devengado": [],  # Lista de columnas que contienen devengado por mes
    "col_generica": None,  # Nombre de la columna de genérica presupuestal
    "fecha_corte": date.today()  # Fecha de corte, por defecto hoy
}

# Itera sobre cada clave y valor del diccionario de valores por defecto
for k, v in session_defaults.items():
    # Si la clave no existe en el session_state de Streamlit
    if k not in st.session_state:
        # Inicializa la variable de sesión con el valor por defecto
        st.session_state[k] = v

# ════════════════════════════════════════════════════════════════════════════════════════════════
# SIDEBAR - SECCIÓN DE CARGA DE DATOS
# ════════════════════════════════════════════════════════════════════════════════════════════════

# Abre el contexto del sidebar (barra lateral izquierda)
with st.sidebar:
    # SUBSECCIÓN: Logo y título
    # Intenta mostrar el logo de la institución
    try:
        mostrar_logo()
    # Si hay error al mostrar el logo
    except Exception as e:
        # Muestra un título alternativo como respaldo
        st.markdown("### 📊 IPEN")
        # st.caption(f"(Logo no disponible)")

    # Añade una línea separadora visual en el sidebar
    st.markdown("---")
    # Muestra el título de la sección de carga de archivos
    st.markdown("### 📁 Carga de datos")
    
    # Crea un widget para que el usuario suba archivos Excel
    archivo = st.file_uploader("Subir Excel SIAF", type=["xls", "xlsx"])

    # Si el usuario ha subido un archivo
    if archivo:
        # Muestra un spinner (indicador de carga) mientras se procesa el archivo
        with st.spinner("⏳ Procesando archivo..."):
            # Intenta procesar el archivo subido
            try:
                # Detecta el motor de lectura según la extensión del archivo
                # Los archivos .xls usan 'xlrd', los .xlsx usan 'openpyxl'
                engine = "xlrd" if archivo.name.lower().endswith(".xls") else "openpyxl"
                # Lee el archivo Excel en un DataFrame
                df_raw = pd.read_excel(archivo, engine=engine)

                # Crea una instancia del procesador de datos con el DataFrame cargado
                processor = DataProcessor(df_raw)
                # Ejecuta el procesamiento completo del DataFrame
                processor.procesar_completo()

                # Crea un diccionario que mapea nombres simplificados con nombres reales de columnas
                cols = {
                    "pim": "PIM",  # Presupuesto Institucional Modificado
                    "certificado": "Certificado",  # Certificado presupuestal
                    "compromiso": "Compromiso_Anual",  # Compromiso anual
                    "generica": processor.col_generica,  # Genérica presupuestal (obtenida del procesador)
                    "devengado": processor.columnas_devengado,  # Columnas de devengado por mes
                }

                # Guarda el DataFrame sin procesar en el session_state
                st.session_state.df = processor.obtener_dataframe()
                # Guarda el DataFrame procesado en el session_state
                st.session_state.df_procesado = processor.obtener_dataframe()
                # Guarda el mapeo de columnas en el session_state
                st.session_state.columnas = cols
                # Guarda la lista de columnas de devengado en el session_state
                st.session_state.cols_devengado = processor.obtener_columnas_devengado()
                # Guarda el nombre de la columna genérica en el session_state
                st.session_state.col_generica = processor.col_generica

                # INICIALIZACIÓN DE PROGRAMACIÓN
                # Obtiene el nombre de la columna genérica del procesador
                col_gen = processor.col_generica
                # Obtiene el DataFrame procesado del procesador
                df_proc = processor.obtener_dataframe()
                
                # Si existe una columna genérica y está en el DataFrame procesado
                if col_gen and col_gen in df_proc.columns:
                    # Obtiene los valores únicos de la columna genérica, eliminando valores nulos, y los convierte en lista ordenada
                    gens = sorted(df_proc[col_gen].dropna().unique().tolist())
                    # Inicializa el sistema de programación con la lista de genéricas
                    inicializar_programacion(gens)

                # Muestra un mensaje de éxito con el nombre del archivo cargado
                st.success(f"✅ Archivo cargado: {archivo.name}")
                
            # Si hay un error en el procesamiento
            except Exception as e:
                # Muestra un mensaje de error con la descripción del problema
                st.error(f"❌ Error al procesar: {str(e)}")

    # SUBSECCIÓN: Opciones adicionales (solo si hay datos cargados)
    # Si hay un DataFrame cargado en el session_state
    if st.session_state.df is not None:
        # Añade una línea separadora visual
        st.markdown("---")
        
        # SUBSUBSECCIÓN: Resumen del sidebar
        # Intenta mostrar un resumen de los datos en el sidebar
        try:
            mostrar_resumen_sidebar()
        # Si hay error al mostrar el resumen
        except Exception as e:
            # Muestra un mensaje informativo de que el resumen no está disponible
            st.caption("ℹ️ Resumen no disponible")

        # Añade una línea separadora visual
        st.markdown("---")
        
        # SUBSUBSECCIÓN: Selector de fecha de corte
        # Crea un widget de entrada de fecha para que el usuario seleccione la fecha de corte
        st.session_state.fecha_corte = st.date_input(
            "📅 Fecha de corte",  # Etiqueta del widget
            value=st.session_state.fecha_corte,  # Valor actual (fecha de corte anterior o hoy)
            min_value=date(2026, 1, 1),  # Fecha mínima permitida (1 de enero de 2026)
            max_value=date(2026, 12, 31)  # Fecha máxima permitida (31 de diciembre de 2026)
        )

# ════════════════════════════════════════════════════════════════════════════════════════════════
# HEADER - SECCIÓN SUPERIOR (TÍTULO Y METADATOS)
# ════════════════════════════════════════════════════════════════════════════════════════════════

# Crea dos columnas en la pantalla con proporción 3:1 (la primera es 3 veces más ancha que la segunda)
col_titulo, col_fecha = st.columns([3, 1])

# Abre el contexto de la primera columna (para el título principal)
with col_titulo:
    # Muestra el título principal del tablero con emoji
    st.markdown("# 📊 Tablero Presupuestal SIAF")
    # Muestra subtítulo con institución y año fiscal
    st.markdown("**IPEN · Ejercicio fiscal 2026**")

# Abre el contexto de la segunda columna (para mostrar la fecha de corte)
with col_fecha:
    # Muestra la fecha de corte formateada como DD/MM/YYYY
    st.markdown(
        f"**Corte:**  \n{st.session_state.fecha_corte.strftime('%d/%m/%Y')}"
    )

# Añade una línea separadora visual (divisor)
st.divider()

# ════════════════════════════════════════════════════════════════════════════════════════════════
# VALIDACIÓN DE DATOS CARGADOS
# ════════════════════════════════════════════════════════════════════════════════════════════════

# Si no hay DataFrame cargado en el session_state
if st.session_state.df is None:
    # Muestra un mensaje informativo indicando al usuario que debe cargar un archivo
    st.info("👈 **Sube un archivo Excel SIAF en el sidebar para comenzar**")
    # Detiene la ejecución del script (no muestra nada más)
    st.stop()

# ════════════════════════════════════════════════════════════════════════════════════════════════
# OBTENCIÓN DE DATOS Y CÁLCULO DE INDICADORES
# ════════════════════════════════════════════════════════════════════════════════════════════════

# Obtiene el DataFrame procesado del session_state
df = st.session_state.df_procesado
# Obtiene el mapeo de columnas del session_state
cols = st.session_state.columnas

# SUBSECCIÓN: Cálculo de indicadores presupuestales
# Intenta calcular todos los indicadores con los datos actuales
try:
    # Llama a la función que calcula todos los indicadores presupuestales
    ind = calcular_todos_indicadores(
        df,  # DataFrame con los datos
        cols,  # Mapeo de columnas
        fecha_corte=st.session_state.fecha_corte  # Fecha de corte para los cálculos
    )
# Si hay error en el cálculo de indicadores
except Exception as e:
    # Muestra un mensaje de error con la descripción del problema
    st.error(f"❌ Error calculando indicadores: {str(e)}")
    # Detiene la ejecución del script
    st.stop()

# ════════════════════════════════════════════════════════════════════════════════════════════════
# CREACIÓN DE TABS (PESTAÑAS PRINCIPALES)
# ════════════════════════════════════════════════════════════════════════════════════════════════

# Crea tres pestañas con nombres y emojis específicos
tab_ejecutivo, tab_operacional, tab_analitico = st.tabs(
    ["📊 Ejecutivo", "⚙️ Operacional", "🔬 Analítico"]
)

# ════════════════════════════════════════════════════════════════════════════════════════════════
# TAB 1: VISTA EJECUTIVA - RESUMEN GRÁFICO DEL PRESUPUESTO
# ════════════════════════════════════════════════════════════════════════════════════════════════

# Abre el contexto de la pestaña "Ejecutivo"
with tab_ejecutivo:
    # Muestra el título de la sección
    st.markdown("## Ejecución presupuestal")
    # Añade una línea separadora visual
    st.divider()

    # ════════════════════════════════════════════════════════════════════════════════════════════
    # SECCIÓN 1: TARJETAS KPI (INDICADORES CLAVE DE DESEMPEÑO)
    # ════════════════════════════════════════════════════════════════════════════════════════════

    # Intenta crear y mostrar las tarjetas KPI
    try:
        # Crea una lista de diccionarios con los datos para cada tarjeta KPI
        kpi_data = [
            # KPI 1: Presupuesto Institucional Modificado (PIM)
            {
                "titulo": "PIM",  # Nombre del KPI
                "valor": ind["ejecucion"]["pim_total"],  # Valor total del PIM
                "formato": "soles"  # Formato de visualización (moneda en soles)
            },
            # KPI 2: Certificado presupuestal
            {
                "titulo": "Certificado",  # Nombre del KPI
                "valor": ind["ejecucion"]["certificado_total"],  # Valor total certificado
                "formato": "soles",  # Formato de visualización
                "progreso": ind["ejecucion"]["pct_certificado"],  # Porcentaje de avance
                "target": 33,  # Meta esperada (33% a este punto del año)
                # Color según el avance (rojo, amarillo o verde)
                "estado": color_por_avance(ind["ejecucion"]["pct_certificado"])
            },
            # KPI 3: Devengado (Indicador oficial del MEF)
            {
                "titulo": "Devengado",  # Nombre del KPI
                "valor": ind["ejecucion"]["devengado_total"],  # Valor total devengado
                "formato": "soles",  # Formato de visualización
                "progreso": ind["ejecucion"]["pct_avance_financiero"],  # Porcentaje de ejecución financiera
                "target": 33,  # Meta esperada
                # Color según el avance
                "estado": color_por_avance(ind["ejecucion"]["pct_avance_financiero"]),
                # Etiqueta adicional explicativa
                "subtitulo": "Indicador oficial MEF"
            },
            # KPI 4: Proyección de cierre al final del año fiscal
            {
                "titulo": "Forecast cierre",  # Nombre del KPI
                "valor": ind["proyecciones"]["proyeccion_pct"],  # Porcentaje proyectado de ejecución
                "formato": "porcentaje",  # Formato de visualización (porcentaje)
                # Color según el nivel de proyección
                "estado": color_por_avance(ind["proyecciones"]["proyeccion_pct"]),
                # Información adicional: brecha proyectada en millones de soles
                "subtitulo": f"Brecha S/ {ind['proyecciones']['brecha_proyectada']/1e6:.1f}M"
            },
        ]
        # Llama a la función que renderiza las tarjetas KPI en una cuadrícula de 4 columnas
        grid_kpis(kpi_data, columnas=4)
    # Si hay error en la creación de KPI cards
    except Exception as e:
        # Muestra un mensaje de error
        st.error(f"❌ Error en KPI cards: {str(e)}")

    # Añade una línea separadora visual
    st.divider()
    
    # ════════════════════════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2: GRÁFICO DE CASCADA Y RATIOS DE FLUJO PRESUPUESTAL
    # ════════════════════════════════════════════════════════════════════════════════════════════

    # Muestra el título de esta sección
    st.markdown("### 📊 Ciclo presupuestal (Cascada)")
    # Crea dos columnas: la primera 1.2 veces más ancha que la segunda
    col_cascada, col_flujo = st.columns([1.2, 1])
    
    # SUBSUBSECCIÓN: Gráfico de cascada (flujo del ciclo presupuestal)
    # Abre el contexto de la primera columna
    with col_cascada:
        # Intenta crear el gráfico de cascada
        try:
            # Obtiene el diccionario de ejecución presupuestal
            e = ind["ejecucion"]
            # Define las fases del ciclo presupuestal
            fases = ["PIM", "Certificado", "Compromiso", "Devengado", "Girado", "Pagado"]
            # Obtiene los valores para cada fase del ciclo
            valores = [
                e["pim_total"],  # PIM: Presupuesto total asignado
                e["certificado_total"],  # Certificado: Presupuesto certificado (disponible para gastar)
                e["compromiso_total"],  # Compromiso: Compromisos adquiridos
                e["devengado_total"],  # Devengado: Obligaciones generadas (principal indicador MEF)
                e["girado_total"],  # Girado: Pagos tramitados
                e["pagado_total"]  # Pagado: Pagos realizados efectivamente
            ]
            
            # Crea un gráfico de cascada (waterfall) con Plotly
            fig_cascada = go.Figure(go.Waterfall(
                name="Ejecución",  # Nombre de la serie
                orientation="v",  # Orientación vertical
                x=fases,  # Eje X: fases del ciclo
                y=valores,  # Eje Y: montos en soles
                # Texto que aparece sobre cada barra (valores en millones)
                text=[f"S/ {v/1e6:.1f}M" for v in valores],
                textposition="outside",  # Posición del texto fuera de las barras
                # Línea conectora entre fases
                connector={"line": {"color": PALETA.get("border", "#ccc")}},
                # Color para barras ascendentes (verde)
                increasing={"marker": {"color": PALETA.get("success", "#2ecc71")}},
                # Color para barras descendentes (rojo)
                decreasing={"marker": {"color": PALETA.get("danger", "#e74c3c")}},
                # Color para barras de totales (azul)
                totals={"marker": {"color": PALETA.get("brand", "#1f77b4")}},
            ))
            
            # Configura la apariencia y comportamiento del gráfico
            fig_cascada.update_layout(
                height=400,  # Altura del gráfico en píxeles
                margin=dict(l=10, r=10, t=20, b=10),  # Márgenes (izquierda, derecha, arriba, abajo)
                hovermode="x",  # Al pasar el ratón, muestra información del eje X
                plot_bgcolor="rgba(240,240,240,0.3)"  # Color de fondo del gráfico (gris claro)
            )
            
            # Muestra el gráfico en la aplicación Streamlit
            st.plotly_chart(fig_cascada, use_container_width=True)
        # Si hay error en la creación del gráfico
        except Exception as e:
            # Muestra un mensaje de advertencia con la descripción del error
            st.warning(f"⚠️ Error en cascada: {str(e)}")
    
    # SUBSUBSECCIÓN: Gráfico de ratios de flujo
    # Abre el contexto de la segunda columna
    with col_flujo:
        # Muestra el título de esta subsección
        st.markdown("### 📈 Ratios de flujo")
        # Intenta crear el gráfico de ratios
        try:
            # Obtiene el diccionario de eficiencia (que contiene los ratios)
            ef = ind["eficiencia"]
            
            # Crea una lista de tuplas (nombre de ratio, valor) para mostrar
            ratio_data = [
                ("Comprom/Certif", ef.get("ratio_compro_certif", 0)),  # % de compromiso vs certificado
                ("Deveng/Comprom", ef.get("ratio_deveng_compro", 0)),  # % de devengado vs compromiso
                ("Girado/Deveng", ef.get("ratio_girado_deveng", 0)),  # % de girado vs devengado
                ("Pagado/Girado", ef.get("ratio_pagado_girado", 0)),  # % de pagado vs girado
            ]
            
            # Crea un gráfico de barras horizontal con Plotly
            fig_ratios = go.Figure(go.Bar(
                y=[name for name, _ in ratio_data],  # Eje Y: nombres de los ratios
                x=[val for _, val in ratio_data],  # Eje X: valores de los ratios
                orientation="h",  # Barras horizontales
                marker=dict(
                    color=[val for _, val in ratio_data],  # Color según el valor
                    colorscale="RdYlGn",  # Escala de colores: rojo-amarillo-verde
                    cmin=0,  # Valor mínimo de la escala (0%)
                    cmax=100,  # Valor máximo de la escala (100%)
                    showscale=False  # No mostrar la barra de escala de colores
                ),
                # Texto que aparece al lado de cada barra (valores en %)
                text=[f"{val:.1f}%" for _, val in ratio_data],
                textposition="outside",  # Posición del texto fuera de las barras
            ))
            
            # Configura la apariencia del gráfico
            fig_ratios.update_layout(
                height=400,  # Altura del gráfico
                margin=dict(l=10, r=10, t=20, b=10),  # Márgenes
                xaxis_title="Porcentaje (%)",  # Título del eje X
                yaxis_title="",  # Sin título para el eje Y
                plot_bgcolor="rgba(240,240,240,0.3)"  # Color de fondo del gráfico
            )
            
            # Muestra el gráfico en la aplicación
            st.plotly_chart(fig_ratios, use_container_width=True)
        # Si hay error en la creación del gráfico
        except Exception as e:
            # Muestra un mensaje de advertencia
            st.warning(f"⚠️ Error en ratios: {str(e)}")

    # Añade una línea separadora visual
    st.divider()
    
    # ════════════════════════════════════════════════════════════════════════════════════════════
    # SECCIÓN 3: CURVA S (ACUMULADO MENSUAL) Y PROYECCIÓN DE CIERRE
    # ════════════════════════════════════════════════════════════════════════════════════════════

    # Muestra el título de esta sección
    st.markdown("### 📉 Curva S y Proyección")
    # Crea dos columnas: la primera 1.2 veces más ancha
    col_curva, col_proyeccion = st.columns([1.2, 1])

    # SUBSUBSECCIÓN: Gráfico de curva S (evolución acumulada mensual)
    # Abre el contexto de la primera columna
    with col_curva:
        # Intenta crear la curva S
        try:
            # ─────────────────────────────────────────────────────────────────────────────────
            # Cálculo del devengado acumulado por mes
            # ─────────────────────────────────────────────────────────────────────────────────
            
            # Inicializa una lista vacía para almacenar valores acumulados y acumulador en cero
            meses_dev, acum = [], 0
            # Si existen columnas de devengado en el session_state
            if st.session_state.cols_devengado:
                # Itera sobre cada columna de devengado (una por mes)
                for col in st.session_state.cols_devengado:
                    # Si la columna existe en el DataFrame
                    if col in df.columns:
                        # Suma todos los valores de esa columna al acumulador
                        acum += df[col].sum()
                    # Añade el acumulador actual a la lista
                    meses_dev.append(acum)
            else:
                # Si no hay columnas de devengado, crea una lista de ceros (uno por cada mes)
                meses_dev = [0] * len(MESES_ABREV)

            # ─────────────────────────────────────────────────────────────────────────────────
            # Cálculo del programado acumulado por mes
            # ─────────────────────────────────────────────────────────────────────────────────
            
            # Obtiene el DataFrame con la programación mensual
            df_prog = obtener_programacion_df()
            # Inicializa una lista vacía para valores acumulados y acumulador
            meses_prog, acum_p = [], 0
            
            # Itera sobre cada mes abreviado (Ene, Feb, Mar, etc.)
            for mes in MESES_ABREV:
                # Si existe el DataFrame de programación y la columna del mes
                if df_prog is not None and mes in df_prog.columns:
                    # Suma todos los valores de ese mes al acumulador
                    acum_p += df_prog[mes].sum()
                # Añade el acumulador actual a la lista
                meses_prog.append(acum_p)

            # ─────────────────────────────────────────────────────────────────────────────────
            # Creación del gráfico de líneas (curva S)
            # ─────────────────────────────────────────────────────────────────────────────────
            
            # Crea una figura de Plotly vacía
            fig = go.Figure()
            
            # Añade la línea de devengado acumulado
            fig.add_trace(go.Scatter(
                x=MESES_ABREV,  # Eje X: meses (Ene, Feb, Mar, etc.)
                y=meses_dev,  # Eje Y: valores acumulados de devengado
                name="Devengado",  # Nombre de la serie
                # Línea azul oscura con grosor 3
                line=dict(color=PALETA.get("brand", "#1f77b4"), width=3),
                fill="tozeroy"  # Rellena el área bajo la línea
            ))
            
            # Añade la línea de programado acumulado
            fig.add_trace(go.Scatter(
                x=MESES_ABREV,  # Eje X: meses
                y=meses_prog,  # Eje Y: valores acumulados de programado
                name="Programado",  # Nombre de la serie
                # Línea naranja con grosor 2 y punteos discontinuos
                line=dict(color=PALETA.get("info", "#ff7f0e"), width=2, dash="dot")
            ))
            
            # Configura la apariencia del gráfico
            fig.update_layout(
                height=350,  # Altura del gráfico
                hovermode="x unified",  # Al pasar el ratón, muestra información de todas las series del eje X
                margin=dict(l=10, r=10, t=20, b=10),  # Márgenes
                plot_bgcolor="rgba(240,240,240,0.5)",  # Color de fondo
                yaxis_title="S/ (millones)"  # Título del eje Y
            )
            
            # Muestra el gráfico
            st.plotly_chart(fig, use_container_width=True)
            
        # Si hay error en la creación de la curva S
        except Exception as e:
            # Muestra un mensaje de advertencia
            st.warning(f"⚠️ No se puede mostrar curva S: {str(e)}")

    # SUBSUBSECCIÓN: Proyección de cierre y gauge (medidor)
    # Abre el contexto de la segunda columna
    with col_proyeccion:
        # Muestra el título de esta subsección
        st.markdown("### 🎯 Proyección al cierre")
        # Intenta mostrar los indicadores de proyección
        try:
            # Obtiene el diccionario de proyecciones
            proy = ind["proyecciones"]
            
            # ─────────────────────────────────────────────────────────────────────────────────
            # Indicadores de proyección (métricas)
            # ─────────────────────────────────────────────────────────────────────────────────
            
            # Crea dos sub-columnas para mostrar métricas lado a lado
            col_p1, col_p2 = st.columns(2)
            # Abre el contexto de la primera sub-columna
            with col_p1:
                # Muestra una métrica con porcentaje de proyección de cierre
                st.metric(
                    "Proyección cierre",  # Título de la métrica
                    f"{proy['proyeccion_pct']:.1f}%",  # Valor (porcentaje con 1 decimal)
                    # Diferencia respecto a la meta (50%)
                    delta=f"{proy['proyeccion_pct'] - 50:.1f}pp",
                    # Color inverso (rojo si < 80%, verde si >= 80%)
                    delta_color="inverse" if proy['proyeccion_pct'] < 80 else "normal"
                )
            # Abre el contexto de la segunda sub-columna
            with col_p2:
                # Muestra una métrica con la brecha proyectada y días restantes
                st.metric(
                    "Brecha proyectada",  # Título de la métrica
                    f"S/ {proy['brecha_proyectada']/1e6:.1f}M",  # Brecha en millones de soles
                    delta=f"{proy['dias_restantes_fiscal']} días"  # Días restantes del año fiscal
                )
            
            # ─────────────────────────────────────────────────────────────────────────────────
            # Gauge (medidor) de proyección
            # ─────────────────────────────────────────────────────────────────────────────────
            
            # Crea un indicador tipo medidor con Plotly
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",  # Muestra el medidor, el número y la diferencia respecto a meta
                value=proy['proyeccion_pct'],  # Valor actual (porcentaje de proyección)
                title={"text": "Meta: 100%"},  # Título del medidor con la meta
                # Referencia para calcular la diferencia (100% es la meta)
                delta={"reference": 100, "suffix": "pp"},  # Sufijo "pp" para "puntos porcentuales"
                gauge={
                    # Configuración del eje del medidor (rango 0-100%)
                    "axis": {"range": [0, 100]},
                    # Color de la barra según el avance
                    "bar": {"color": color_por_avance(proy['proyeccion_pct'])},
                    # Zonas de color de fondo
                    "steps": [
                        # Zona roja (0-60%): bajo desempeño
                        {"range": [0, 60], "color": "rgba(255, 0, 0, 0.1)"},
                        # Zona amarilla (60-80%): desempeño medio
                        {"range": [60, 80], "color": "rgba(255, 165, 0, 0.1)"},
                        # Zona verde (80-100%): buen desempeño
                        {"range": [80, 100], "color": "rgba(0, 255, 0, 0.1)"}
                    ],
                    # Línea de alerta en 80% (límite de riesgo)
                    "threshold": {
                        "line": {"color": "red", "width": 4},  # Línea roja
                        "thickness": 0.75,  # Grosor relativo
                        "value": 80  # Posición del umbral
                    }
                }
            ))
            
            # Configura la altura del gráfico
            fig_gauge.update_layout(height=300)
            # Muestra el gráfico
            st.plotly_chart(fig_gauge, use_container_width=True)
            
        # Si hay error en la proyección
        except Exception as e:
            # Muestra un mensaje de advertencia
            st.warning(f"⚠️ Error en proyección: {str(e)}")

    # Añade una línea separadora visual
    st.divider()
    
    # ════════════════════════════════════════════════════════════════════════════════════════════
    # SECCIÓN 4: DISTRIBUCIÓN PRESUPUESTAL POR GENÉRICA
    # ════════════════════════════════════════════════════════════════════════════════════════════

    # Muestra el título de esta sección (Top 8 genéricas)
    st.markdown("### 💰 Distribución por genérica (Top 8)")
    # Intenta crear el gráfico de distribución
    try:
        # Obtiene el nombre de la columna PIM
        col_pim = cols.get("pim")
        # Obtiene el nombre de la columna genérica del session_state
        col_gen = st.session_state.col_generica
        
        # Si existen ambas columnas en los datos
        if col_pim and col_gen and col_gen in df.columns:
            # Obtiene los primeros 8 valores únicos de la columna genérica (elimina nulos)
            genericas = df[col_gen].dropna().unique()[:8]
            
            # Si hay al menos una genérica
            if len(genericas) > 0:
                # Inicializa una lista para almacenar datos de cada genérica
                gen_data = []
                # Itera sobre cada genérica
                for gen in genericas:
                    # Filtra el DataFrame para solo esta genérica
                    df_g = df[df[col_gen] == gen]
                    # Suma todos los valores de PIM para esta genérica
                    pim_g = df_g[col_pim].sum() if col_pim in df_g.columns else 0
                    # Suma todos los valores de devengado para esta genérica
                    dev_g = sum(
                        df_g[c].sum()
                        # Itera sobre todas las columnas de devengado
                        for c in st.session_state.cols_devengado
                        # Solo si la columna existe en el DataFrame filtrado
                        if c in df_g.columns
                    )
                    # Calcula el porcentaje de ejecución (devengado / PIM * 100)
                    pct = (dev_g / pim_g * 100) if pim_g > 0 else 0
                    # Añade los datos de esta genérica a la lista
                    gen_data.append({
                        "generica": str(gen)[:35],  # Nombre truncado a 35 caracteres
                        "pim": pim_g,  # PIM de esta genérica
                        "devengado": dev_g,  # Devengado de esta genérica
                        "pct": pct  # Porcentaje de ejecución
                    })
                
                # Crea un DataFrame con los datos y los ordena por PIM ascendente
                gen_df = pd.DataFrame(gen_data).sort_values("pim", ascending=True)
                
                # Crea una figura de Plotly vacía
                fig_gen = go.Figure()
                
                # Añade la primera serie de barras (devengado)
                fig_gen.add_trace(go.Bar(
                    y=gen_df["generica"],  # Eje Y: nombres de genéricas
                    x=gen_df["devengado"],  # Eje X: valores devengados
                    name="Devengado",  # Nombre de la serie
                    marker=dict(color=PALETA.get("success", "#2ecc71")),  # Color verde
                    orientation="h"  # Barras horizontales
                ))
                
                # Añade la segunda serie de barras (pendiente de devengación)
                fig_gen.add_trace(go.Bar(
                    y=gen_df["generica"],  # Eje Y: nombres de genéricas
                    x=gen_df["pim"] - gen_df["devengado"],  # Eje X: diferencia (PIM - devengado)
                    name="Pendiente",  # Nombre de la serie
                    marker=dict(color=PALETA.get("light_gray", "#ecf0f1")),  # Color gris claro
                    orientation="h"  # Barras horizontales
                ))
                
                # Configura la apariencia del gráfico
                fig_gen.update_layout(
                    barmode="stack",  # Las barras se apilan una sobre otra
                    height=350,  # Altura del gráfico
                    margin=dict(l=150, r=10, t=20, b=10),  # Margen izquierdo amplio para nombres
                    xaxis_title="S/ (millones)",  # Título del eje X
                    hovermode="y",  # Al pasar el ratón, muestra información del eje Y
                    plot_bgcolor="rgba(240,240,240,0.3)"  # Color de fondo
                )
                
                # Muestra el gráfico
                st.plotly_chart(fig_gen, use_container_width=True)
            else:
                # Si no hay datos de genéricas
                st.info("Sin datos de genéricas")
        else:
            # Si faltan columnas necesarias
            st.info("Faltan datos para mostrar genéricas")
            
    # Si hay error en la creación del gráfico de distribución
    except Exception as e:
        # Muestra un mensaje de advertencia
        st.warning(f"⚠️ Error en distribución: {str(e)}")

    # Añade una línea separadora visual
    st.divider()

    # ════════════════════════════════════════════════════════════════════════════════════════════
    # SECCIÓN 5: PANEL DE ALERTAS Y RIESGOS
    # ════════════════════════════════════════════════════════════════════════════════════════════

    # Muestra el título de esta sección
    st.markdown("### ⚠️ Alertas y riesgos")
    # Intenta mostrar el panel de alertas
    try:
        # Si existen alertas en los indicadores
        if ind.get("alertas"):
            # Muestra el panel con las alertas
            panel_alertas(ind["alertas"])
        else:
            # Si no hay alertas, muestra un mensaje de confirmación
            st.info("✅ Sin alertas")
    # Si hay error al mostrar alertas
    except Exception as e:
        # Muestra un mensaje informativo de que el módulo no está disponible
        st.info("ℹ️ Módulo de alertas no disponible")

# ════════════════════════════════════════════════════════════════════════════════════════════════
# TAB 2: VISTA OPERACIONAL - ANÁLISIS DETALLADO Y TABLA DE DATOS
# ════════════════════════════════════════════════════════════════════════════════════════════════

# Abre el contexto de la pestaña "Operacional"
with tab_operacional:
    # Muestra el título de la sección
    st.markdown("## Análisis operacional")
    # Añade una línea separadora visual
    st.divider()
    
    # Crea tres columnas en proporción 1:1:1 (mismo ancho)
    col_ratios, col_distribucion, col_proyeccion = st.columns(3)
    
    # SUBSUBSECCIÓN: Ratios de eficiencia
    # Abre el contexto de la primera columna
    with col_ratios:
        # Muestra el título de esta subsección
        st.markdown("### 📈 Ratios")
        # Intenta mostrar los ratios
        try:
            # Obtiene el diccionario de eficiencia
            r = ind.get("eficiencia", {})
            # Muestra la métrica de ratio de compromiso vs certificado
            st.metric(
                "Comprometido/Cert",  # Título
                f"{r.get('ratio_compro_certif', 0):.1f}%"  # Valor con 1 decimal
            )
            # Muestra la métrica de ratio de devengado vs compromiso
            st.metric(
                "Devengado/Comprom",  # Título
                f"{r.get('ratio_deveng_compro', 0):.1f}%"  # Valor con 1 decimal
            )
        # Si hay error al mostrar ratios
        except Exception as e:
            # Muestra un mensaje de advertencia
            st.warning(f"Error en ratios: {str(e)}")

    # SUBSUBSECCIÓN: Distribución de gasto (corriente vs capital)
    # Abre el contexto de la segunda columna
    with col_distribucion:
        # Muestra el título de esta subsección
        st.markdown("### 💰 Distribución")
        # Intenta mostrar la distribución de gasto
        try:
            # Obtiene el diccionario de distribución
            d = ind.get("distribucion", {})
            # Si el diccionario contiene datos de gasto corriente
            if "gasto_corriente_pct" in d:
                # Muestra la métrica de gasto corriente (sueldos, servicios, etc.)
                st.metric(
                    "Gasto corriente",  # Título
                    f"{d['gasto_corriente_pct']:.1f}%"  # Porcentaje
                )
                # Muestra la métrica de gasto capital (inversión en activos)
                st.metric(
                    "Gasto capital",  # Título
                    f"{d['gasto_capital_pct']:.1f}%"  # Porcentaje
                )
            else:
                # Si no hay datos disponibles
                st.info("Datos no disponibles")
        # Si hay error al mostrar distribución
        except Exception as e:
            # Muestra un mensaje de advertencia
            st.warning(f"Error en distribución: {str(e)}")

    # SUBSUBSECCIÓN: Proyección de cierre (repetida para contexto operacional)
    # Abre el contexto de la tercera columna
    with col_proyeccion:
        # Muestra el título de esta subsección
        st.markdown("### 🎯 Proyección")
        # Intenta mostrar los datos de proyección
        try:
            # Obtiene el diccionario de proyecciones
            p = ind.get("proyecciones", {})
            # Muestra la métrica de forecast de cierre
            st.metric(
                "Forecast cierre",  # Título
                f"{p.get('proyeccion_pct', 0):.1f}%"  # Porcentaje proyectado
            )
            # Muestra la métrica de días restantes del año fiscal
            st.metric(
                "Días restantes",  # Título
                p.get("dias_restantes_fiscal", 0)  # Número de días
            )
        # Si hay error al mostrar proyección
        except Exception as e:
            # Muestra un mensaje de advertencia
            st.warning(f"Error en proyección: {str(e)}")

    # Añade una línea separadora visual
    st.divider()
    
    # SUBSUBSECCIÓN: Tabla de resumen detallada
    # Intenta mostrar la tabla de resumen de datos
    try:
        # Llama a la función que crea y muestra la tabla de resumen
        crear_tabla_resumen(df)
    # Si hay error al mostrar la tabla
    except Exception as e:
        # Muestra un mensaje de advertencia
        st.warning(f"⚠️ No se puede mostrar tabla: {str(e)}")

# ════════════════════════════════════════════════════════════════════════════════════════════════
# TAB 3: VISTA ANALÍTICA - INDICADORES DETALLADOS Y EVOLUCIÓN MENSUAL
# ════════════════════════════════════════════════════════════════════════════════════════════════

# Abre el contexto de la pestaña "Analítico"
with tab_analitico:
    # Muestra el título de la sección
    st.markdown("## Análisis analítico")
    # Añade una línea separadora visual
    st.divider()
    
    # SUBSUBSECCIÓN: Indicadores tipo gauge (medidores)
    # Intenta mostrar los indicadores
    try:
        # Llama a la función que muestra indicadores en forma de medidores
        mostrar_indicadores(
            ind["ejecucion"]["pim_total"],  # PIM total como primer parámetro
            ind["ejecucion"]["certificado_total"],  # Certificado total
            ind["ejecucion"]["compromiso_total"],  # Compromiso total
            ind["ejecucion"]["devengado_total"],  # Devengado total
        )
    # Si hay error al mostrar indicadores
    except Exception as e:
        # Muestra un mensaje de advertencia
        st.warning(f"⚠️ No se pueden mostrar indicadores: {str(e)}")

    # Añade una línea separadora visual
    st.divider()
    
    # SUBSUBSECCIÓN: Gráfico de evolución mensual
    # Muestra el título de esta subsección
    st.markdown("### 📊 Evolución mensual")
    # Intenta crear y mostrar el gráfico de evolución
    try:
        # Obtiene el DataFrame con la programación mensual
        df_prog = obtener_programacion_df()
        # Crea el gráfico de evolución mensual
        fig = crear_grafico_mensual(df, st.session_state.cols_devengado, df_prog)
        # Muestra el gráfico
        st.plotly_chart(fig, use_container_width=True)
    # Si hay error al mostrar evolución
    except Exception as e:
        # Muestra un mensaje de advertencia
        st.warning(f"⚠️ No se puede mostrar evolución: {str(e)}")

    # Añade una línea separadora visual
    st.divider()
    
    # SUBSUBSECCIÓN: Formulario de programación mensual
    # Muestra el título de esta subsección
    st.markdown("### 📅 Programación mensual")
    # Intenta mostrar el formulario de programación
    try:
        # Obtiene el nombre de la columna genérica del session_state
        col_gen_key = st.session_state.col_generica
        # Si existe una columna genérica y está en el DataFrame
        if col_gen_key and col_gen_key in df.columns:
            # Obtiene la lista única de genéricas, ordenada alfabéticamente
            gens = sorted(df[col_gen_key].dropna().unique().tolist())
            # Muestra el formulario de programación
            mostrar_formulario_programacion(gens)
        else:
            # Si falta la columna de genérica
            st.info("Falta columna de genérica para mostrar programación")
    # Si hay error al mostrar el formulario
    except Exception as e:
        # Muestra un mensaje de advertencia
        st.warning(f"⚠️ Error en formulario: {str(e)}")

# src/app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
import sys, os, re

sys.path.insert(0, os.path.dirname(__file__))

from config import PALETA, color_por_avance, MESES_ABREV
from utils.data_processor import DataProcessor
from utils.indicadores import calcular_todos_indicadores
from components.gauges import mostrar_indicadores
from components.monthly_chart import crear_grafico_mensual
from components.summary_table import crear_tabla_resumen
from components.sidebar import crear_filtros, mostrar_logo
from components.programacion_form import (
    inicializar_programacion, obtener_programacion_df,
    mostrar_resumen_sidebar, mostrar_formulario_programacion,
)
from components.kpi_cards import grid_kpis, panel_alertas

# Configuración de la página
st.set_page_config(
    page_title="Tablero SIAF · IPEN",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session_state con valores por defecto
session_defaults = {
    "df": None,
    "df_procesado": None,
    "columnas": {},
    "cols_devengado": [],
    "col_generica": None,
    "fecha_corte": date.today()
}

for k, v in session_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ──────────────────────────────────────────────────────────────────[...]
# SIDEBAR - Carga de datos
# ──────────────────────────────────────────────────────────────────[...]
with st.sidebar:
    # Logo
    try:
        mostrar_logo()
    except Exception as e:
        st.markdown("### 📊 IPEN")
        # st.caption(f"(Logo no disponible)")

    st.markdown("---")
    st.markdown("### 📁 Carga de datos")
    
    archivo = st.file_uploader("Subir Excel SIAF", type=["xls", "xlsx"])

    if archivo:
        with st.spinner("⏳ Procesando archivo..."):
            try:
                # Detectar motor correcto según extensión
                engine = "xlrd" if archivo.name.lower().endswith(".xls") else "openpyxl"
                df_raw = pd.read_excel(archivo, engine=engine)

                # Procesar datos
                processor = DataProcessor(df_raw)
                processor.procesar_completo()

                # Mapeo de columnas procesadas
                cols = {
                    "pim": "PIM",
                    "certificado": "Certificado",
                    "compromiso": "Compromiso_Anual",
                    "generica": processor.col_generica,
                    "devengado": processor.columnas_devengado,
                }

                # Guardar en session_state
                st.session_state.df = processor.obtener_dataframe()
                st.session_state.df_procesado = processor.obtener_dataframe()
                st.session_state.columnas = cols
                st.session_state.cols_devengado = processor.obtener_columnas_devengado()
                st.session_state.col_generica = processor.col_generica

                # Inicializar programación si existe columna genérica
                col_gen = processor.col_generica
                df_proc = processor.obtener_dataframe()
                
                if col_gen and col_gen in df_proc.columns:
                    gens = sorted(df_proc[col_gen].dropna().unique().tolist())
                    inicializar_programacion(gens)

                st.success(f"✅ Archivo cargado: {archivo.name}")
                
            except Exception as e:
                st.error(f"❌ Error al procesar: {str(e)}")

    # Mostrar opciones si hay datos cargados
    if st.session_state.df is not None:
        st.markdown("---")
        
        # Resumen sidebar
        try:
            mostrar_resumen_sidebar()
        except Exception as e:
            st.caption("ℹ️ Resumen no disponible")

        st.markdown("---")
        
        # Selector de fecha de corte
        st.session_state.fecha_corte = st.date_input(
            "📅 Fecha de corte",
            value=st.session_state.fecha_corte,
            min_value=date(2026, 1, 1),
            max_value=date(2026, 12, 31)
        )

# ──────────────────────────────────────────────────────────────────[...]
# HEADER - Título y metadatos
# ──────────────────────────────────────────────────────────────────[...]
col_titulo, col_fecha = st.columns([3, 1])

with col_titulo:
    st.markdown("# 📊 Tablero Presupuestal SIAF")
    st.markdown("**IPEN · Ejercicio fiscal 2026**")

with col_fecha:
    st.markdown(
        f"**Corte:**  \n{st.session_state.fecha_corte.strftime('%d/%m/%Y')}"
    )

st.divider()

# Validar que hay datos cargados
if st.session_state.df is None:
    st.info("👈 **Sube un archivo Excel SIAF en el sidebar para comenzar**")
    st.stop()

# Obtener datos del session_state
df = st.session_state.df_procesado
cols = st.session_state.columnas

# Calcular indicadores
try:
    ind = calcular_todos_indicadores(
        df,
        cols,
        fecha_corte=st.session_state.fecha_corte
    )
except Exception as e:
    st.error(f"❌ Error calculando indicadores: {str(e)}")
    st.stop()

# ──────────────────────────────────────────────────────────────────[...]
# TABS - Vistas principales
# ──────────────────────────────────────────────────────────────────[...]
tab_ejecutivo, tab_operacional, tab_analitico = st.tabs(
    ["📊 Ejecutivo", "⚙️ Operacional", "🔬 Analítico"]
)

# ──────────────────────────────────────────────────────────────────[...]
# TAB 1: EJECUTIVO
# ──────────────────────────────────────────────────────────────────[...]
with tab_ejecutivo:
    st.markdown("## Ejecución presupuestal")
    st.divider()

    # KPI Cards
    try:
        kpi_data = [
            {
                "titulo": "PIM",
                "valor": ind["ejecucion"]["pim_total"],
                "formato": "soles"
            },
            {
                "titulo": "Certificado",
                "valor": ind["ejecucion"]["certificado_total"],
                "formato": "soles",
                "progreso": ind["ejecucion"]["pct_certificado"],
                "target": 33,
                "estado": color_por_avance(ind["ejecucion"]["pct_certificado"])
            },
            {
                "titulo": "Devengado",
                "valor": ind["ejecucion"]["devengado_total"],
                "formato": "soles",
                "progreso": ind["ejecucion"]["pct_avance_financiero"],
                "target": 33,
                "estado": color_por_avance(ind["ejecucion"]["pct_avance_financiero"]),
                "subtitulo": "Indicador oficial MEF"
            },
            {
                "titulo": "Forecast cierre",
                "valor": ind["proyecciones"]["proyeccion_pct"],
                "formato": "porcentaje",
                "estado": color_por_avance(ind["proyecciones"]["proyeccion_pct"]),
                "subtitulo": f"Brecha S/ {ind['proyecciones']['brecha_proyectada']/1e6:.1f}M"
            },
        ]
        grid_kpis(kpi_data, columnas=4)
    except Exception as e:
        st.error(f"❌ Error en KPI cards: {str(e)}")

    st.divider()
    
    # Alertas
    st.markdown("### ⚠️ Alertas")
    try:
        if ind.get("alertas"):
            panel_alertas(ind["alertas"])
        else:
            st.info("✅ Sin alertas")
    except Exception as e:
        st.info("ℹ️ Módulo de alertas no disponible")

    st.divider()

    # Gráficos en dos columnas
    col_curva, col_generica = st.columns([1.2, 1])

    # Columna 1: Curva S
    with col_curva:
        st.markdown("### 📉 Curva S")
        try:
            # Calcular devengado acumulado
            meses_dev, acum = [], 0
            if st.session_state.cols_devengado:
                for col in st.session_state.cols_devengado:
                    if col in df.columns:
                        acum += df[col].sum()
                    meses_dev.append(acum)
            else:
                meses_dev = [0] * len(MESES_ABREV)

            # Calcular programado acumulado
            df_prog = obtener_programacion_df()
            meses_prog, acum_p = [], 0
            
            for mes in MESES_ABREV:
                if df_prog is not None and mes in df_prog.columns:
                    acum_p += df_prog[mes].sum()
                meses_prog.append(acum_p)

            # Crear gráfico
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=MESES_ABREV,
                y=meses_dev,
                name="Devengado",
                line=dict(color=PALETA.get("brand", "#1f77b4"), width=3),
                fill="tozeroy"
            ))
            
            fig.add_trace(go.Scatter(
                x=MESES_ABREV,
                y=meses_prog,
                name="Programado",
                line=dict(color=PALETA.get("info", "#ff7f0e"), width=2, dash="dot")
            ))
            
            fig.update_layout(
                height=300,
                hovermode="x unified",
                margin=dict(l=10, r=10, t=20, b=10),
                plot_bgcolor="rgba(240,240,240,0.5)"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.warning(f"⚠️ No se puede mostrar curva S: {str(e)}")

    # Columna 2: Por genérica
    with col_generica:
        st.markdown("### 📊 Por genérica (Top 6)")
        try:
            col_pim = cols.get("pim")
            col_gen = st.session_state.col_generica
            
            # Validar que existan las columnas necesarias
            if col_pim and col_gen and col_gen in df.columns:
                genericas = df[col_gen].dropna().unique()[:6]
                
                if len(genericas) > 0:
                    for gen in genericas:
                        df_g = df[df[col_gen] == gen]
                        pim_g = df_g[col_pim].sum() if col_pim in df_g.columns else 0
                        dev_g = sum(
                            df_g[c].sum()
                            for c in st.session_state.cols_devengado
                            if c in df_g.columns
                        )
                        pct = (dev_g / pim_g * 100) if pim_g > 0 else 0
                        color = color_por_avance(pct)
                        
                        # Usar componentes nativos de Streamlit en lugar de HTML
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(str(gen)[:30])
                        with col2:
                            st.write(f"**{pct:.1f}%**")
                        st.progress(min(pct / 100, 1.0))
                else:
                    st.info("Sin datos de genéricas")
            else:
                st.info("Faltan datos para mostrar genéricas")
                
        except Exception as e:
            st.warning(f"⚠️ Error en genéricas: {str(e)}")

# ──────────────────────────────────────────────────────────────────[...]
# TAB 2: OPERACIONAL
# ──────────────────────────────────────────────────────────────────[...]
with tab_operacional:
    st.markdown("## Análisis operacional")
    st.divider()
    
    col_ratios, col_distribucion, col_proyeccion = st.columns(3)
    
    # Ratios
    with col_ratios:
        st.markdown("### 📈 Ratios")
        try:
            r = ind.get("eficiencia", {})
            st.metric(
                "Comprometido/Cert",
                f"{r.get('ratio_compro_certif', 0):.1f}%"
            )
            st.metric(
                "Devengado/Comprom",
                f"{r.get('ratio_deveng_compro', 0):.1f}%"
            )
        except Exception as e:
            st.warning(f"Error en ratios: {str(e)}")

    # Distribución
    with col_distribucion:
        st.markdown("### 💰 Distribución")
        try:
            d = ind.get("distribucion", {})
            if "gasto_corriente_pct" in d:
                st.metric(
                    "Gasto corriente",
                    f"{d['gasto_corriente_pct']:.1f}%"
                )
                st.metric(
                    "Gasto capital",
                    f"{d['gasto_capital_pct']:.1f}%"
                )
            else:
                st.info("Datos no disponibles")
        except Exception as e:
            st.warning(f"Error en distribución: {str(e)}")

    # Proyección
    with col_proyeccion:
        st.markdown("### 🎯 Proyección")
        try:
            p = ind.get("proyecciones", {})
            st.metric(
                "Forecast cierre",
                f"{p.get('proyeccion_pct', 0):.1f}%"
            )
            st.metric(
                "Días restantes",
                p.get("dias_restantes_fiscal", 0)
            )
        except Exception as e:
            st.warning(f"Error en proyección: {str(e)}")

    st.divider()
    
    # Tabla de resumen
    try:
        crear_tabla_resumen(df)
    except Exception as e:
        st.warning(f"⚠️ No se puede mostrar tabla: {str(e)}")

# ──────────────────────────────────────────────────────────────────[...]
# TAB 3: ANALÍTICO
# ──────────────────────────────────────────────────────────────────[...]
with tab_analitico:
    st.markdown("## Análisis analítico")
    st.divider()
    
    # Indicadores tipo gauge
    try:
        mostrar_indicadores(
            ind["ejecucion"]["pim_total"],
            ind["ejecucion"]["certificado_total"],
            ind["ejecucion"]["compromiso_total"],
            ind["ejecucion"]["devengado_total"],
        )
    except Exception as e:
        st.warning(f"⚠️ No se pueden mostrar indicadores: {str(e)}")

    st.divider()
    
    # Evolución mensual
    st.markdown("### 📊 Evolución mensual")
    try:
        df_prog = obtener_programacion_df()
        fig = crear_grafico_mensual(df, st.session_state.cols_devengado, df_prog)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"⚠️ No se puede mostrar evolución: {str(e)}")

    st.divider()
    
    # Formulario de programación
    st.markdown("### 📅 Programación mensual")
    try:
        col_gen_key = st.session_state.col_generica
        if col_gen_key and col_gen_key in df.columns:
            gens = sorted(df[col_gen_key].dropna().unique().tolist())
            mostrar_formulario_programacion(gens)
        else:
            st.info("Falta columna de genérica para mostrar programación")
    except Exception as e:
        st.warning(f"⚠️ Error en formulario: {str(e)}")

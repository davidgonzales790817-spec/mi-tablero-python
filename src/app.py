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
# TAB 1: EJECUTIVO - Rediseñado con Gráficos
# ──────────────────────────────────────────────────────────────────[...]
with tab_ejecutivo:
    st.markdown("## Ejecución presupuestal")
    st.divider()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[...]
    # SECCIÓN 1: KPI HEADLINE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[...]
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
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[...]
    # SECCIÓN 2: GRÁFICO EN CASCADA - Flujo del ciclo presupuestal
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[...]
    st.markdown("### 📊 Ciclo presupuestal (Cascada)")
    col_cascada, col_flujo = st.columns([1.2, 1])
    
    with col_cascada:
        try:
            e = ind["ejecucion"]
            fases = ["PIM", "Certificado", "Compromiso", "Devengado", "Girado", "Pagado"]
            valores = [
                e["pim_total"],
                e["certificado_total"],
                e["compromiso_total"],
                e["devengado_total"],
                e["girado_total"],
                e["pagado_total"]
            ]
            
            fig_cascada = go.Figure(go.Waterfall(
                name="Ejecución",
                orientation="v",
                x=fases,
                y=valores,
                text=[f"S/ {v/1e6:.1f}M" for v in valores],
                textposition="outside",
                connector={"line": {"color": PALETA.get("border", "#ccc")}},
                increasing={"marker": {"color": PALETA.get("success", "#2ecc71")}},
                decreasing={"marker": {"color": PALETA.get("danger", "#e74c3c")}},
                totals={"marker": {"color": PALETA.get("brand", "#1f77b4")}},
            ))
            
            fig_cascada.update_layout(
                height=400,
                margin=dict(l=10, r=10, t=20, b=10),
                hovermode="x",
                plot_bgcolor="rgba(240,240,240,0.3)"
            )
            
            st.plotly_chart(fig_cascada, use_container_width=True)
        except Exception as e:
            st.warning(f"⚠️ Error en cascada: {str(e)}")
    
    with col_flujo:
        st.markdown("### 📈 Ratios de flujo")
        try:
            ef = ind["eficiencia"]
            
            ratio_data = [
                ("Comprom/Certif", ef.get("ratio_compro_certif", 0)),
                ("Deveng/Comprom", ef.get("ratio_deveng_compro", 0)),
                ("Girado/Deveng", ef.get("ratio_girado_deveng", 0)),
                ("Pagado/Girado", ef.get("ratio_pagado_girado", 0)),
            ]
            
            fig_ratios = go.Figure(go.Bar(
                y=[name for name, _ in ratio_data],
                x=[val for _, val in ratio_data],
                orientation="h",
                marker=dict(
                    color=[val for _, val in ratio_data],
                    colorscale="RdYlGn",
                    cmin=0,
                    cmax=100,
                    showscale=False
                ),
                text=[f"{val:.1f}%" for _, val in ratio_data],
                textposition="outside",
            ))
            
            fig_ratios.update_layout(
                height=400,
                margin=dict(l=10, r=10, t=20, b=10),
                xaxis_title="Porcentaje (%)",
                yaxis_title="",
                plot_bgcolor="rgba(240,240,240,0.3)"
            )
            
            st.plotly_chart(fig_ratios, use_container_width=True)
        except Exception as e:
            st.warning(f"⚠️ Error en ratios: {str(e)}")

    st.divider()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[...]
    # SECCIÓN 3: CURVA S + Proyección
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[...]
    st.markdown("### 📉 Curva S y Proyección")
    col_curva, col_proyeccion = st.columns([1.2, 1])

    # Columna 1: Curva S
    with col_curva:
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
                height=350,
                hovermode="x unified",
                margin=dict(l=10, r=10, t=20, b=10),
                plot_bgcolor="rgba(240,240,240,0.5)",
                yaxis_title="S/ (millones)"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.warning(f"⚠️ No se puede mostrar curva S: {str(e)}")

    # Columna 2: Proyección y alertas
    with col_proyeccion:
        st.markdown("### 🎯 Proyección al cierre")
        try:
            proy = ind["proyecciones"]
            
            # Indicadores de proyección
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.metric(
                    "Proyección cierre",
                    f"{proy['proyeccion_pct']:.1f}%",
                    delta=f"{proy['proyeccion_pct'] - 50:.1f}pp",
                    delta_color="inverse" if proy['proyeccion_pct'] < 80 else "normal"
                )
            with col_p2:
                st.metric(
                    "Brecha proyectada",
                    f"S/ {proy['brecha_proyectada']/1e6:.1f}M",
                    delta=f"{proy['dias_restantes_fiscal']} días"
                )
            
            # Gauge de proyección
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=proy['proyeccion_pct'],
                title={"text": "Meta: 100%"},
                delta={"reference": 100, "suffix": "pp"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": color_por_avance(proy['proyeccion_pct'])},
                    "steps": [
                        {"range": [0, 60], "color": "rgba(255, 0, 0, 0.1)"},
                        {"range": [60, 80], "color": "rgba(255, 165, 0, 0.1)"},
                        {"range": [80, 100], "color": "rgba(0, 255, 0, 0.1)"}
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": 80
                    }
                }
            ))
            
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)
            
        except Exception as e:
            st.warning(f"⚠️ Error en proyección: {str(e)}")

    st.divider()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[...]
    # SECCIÓN 4: DISTRIBUCIÓN POR GENÉRICA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[...]
    st.markdown("### 💰 Distribución por genérica (Top 8)")
    try:
        col_pim = cols.get("pim")
        col_gen = st.session_state.col_generica
        
        if col_pim and col_gen and col_gen in df.columns:
            genericas = df[col_gen].dropna().unique()[:8]
            
            if len(genericas) > 0:
                gen_data = []
                for gen in genericas:
                    df_g = df[df[col_gen] == gen]
                    pim_g = df_g[col_pim].sum() if col_pim in df_g.columns else 0
                    dev_g = sum(
                        df_g[c].sum()
                        for c in st.session_state.cols_devengado
                        if c in df_g.columns
                    )
                    pct = (dev_g / pim_g * 100) if pim_g > 0 else 0
                    gen_data.append({
                        "generica": str(gen)[:35],
                        "pim": pim_g,
                        "devengado": dev_g,
                        "pct": pct
                    })
                
                gen_df = pd.DataFrame(gen_data).sort_values("pim", ascending=True)
                
                fig_gen = go.Figure()
                
                fig_gen.add_trace(go.Bar(
                    y=gen_df["generica"],
                    x=gen_df["devengado"],
                    name="Devengado",
                    marker=dict(color=PALETA.get("success", "#2ecc71")),
                    orientation="h"
                ))
                
                fig_gen.add_trace(go.Bar(
                    y=gen_df["generica"],
                    x=gen_df["pim"] - gen_df["devengado"],
                    name="Pendiente",
                    marker=dict(color=PALETA.get("light_gray", "#ecf0f1")),
                    orientation="h"
                ))
                
                fig_gen.update_layout(
                    barmode="stack",
                    height=350,
                    margin=dict(l=150, r=10, t=20, b=10),
                    xaxis_title="S/ (millones)",
                    hovermode="y",
                    plot_bgcolor="rgba(240,240,240,0.3)"
                )
                
                st.plotly_chart(fig_gen, use_container_width=True)
            else:
                st.info("Sin datos de genéricas")
        else:
            st.info("Faltan datos para mostrar genéricas")
            
    except Exception as e:
        st.warning(f"⚠️ Error en distribución: {str(e)}")

    st.divider()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[...]
    # SECCIÓN 5: ALERTAS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[...]
    st.markdown("### ⚠️ Alertas y riesgos")
    try:
        if ind.get("alertas"):
            panel_alertas(ind["alertas"])
        else:
            st.info("✅ Sin alertas")
    except Exception as e:
        st.info("ℹ️ Módulo de alertas no disponible")

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

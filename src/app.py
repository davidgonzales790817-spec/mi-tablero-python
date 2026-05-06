# src/app.py
# ═══════════════════════════════════════════════════════════════════════════
# TABLERO PRESUPUESTAL SIAF v2.0 - VERSIÓN SIMPLIFICADA
# ═══════════════════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
import sys
import os

# Agregar ruta correcta
sys.path.insert(0, os.path.dirname(__file__))

# Importar SOLO lo que NO depende de config
try:
    from utils.data_processor import DataProcessor
    from utils.file_handler import FileHandler
except ImportError as e:
    st.error(f"Error: {e}")
    st.stop()

# Ahora importar lo que SÍ depende de config (después que config está cargado)
try:
    from components.gauges import crear_gauges
    from components.monthly_chart import monthly_chart
    from components.summary_table import mostrar_tabla_resumen
    from components.programacion_form import (
        inicializar_programacion,
        obtener_programacion_df,
        mostrar_resumen_sidebar,
    )
    from components.kpi_cards import grid_kpis, panel_alertas
except ImportError as e:
    st.error(f"Error importando componentes: {e}")
    st.stop()

# Ahora importar config (después que todo cargó)
try:
    from config import PALETA, color_por_avance, MESES_ABREV
    from utils.indicadores import calcular_todos_indicadores
except ImportError as e:
    st.error(f"Error importando config/indicadores: {e}")
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════
# CONFIG STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Tablero Presupuestal SIAF · IPEN",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 600; }
    [data-testid="stMetricLabel"] { font-size: 0.9rem; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════

if "df" not in st.session_state:
    st.session_state.df = None
if "columnas" not in st.session_state:
    st.session_state.columnas = {}
if "indicadores" not in st.session_state:
    st.session_state.indicadores = None
if "fecha_corte" not in st.session_state:
    st.session_state.fecha_corte = date.today()


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# 📊 Tablero Presupuestal SIAF")
        st.markdown("**IPEN · 2026**")
    with col2:
        st.markdown(f"**Corte:** {st.session_state.fecha_corte.strftime('%d/%m/%Y')}")
    
    st.divider()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📁 Carga de datos")
        archivo = st.file_uploader("Subir Excel SIAF", type=['xlsx', 'xls'])
        
        if archivo:
            with st.spinner("Procesando..."):
                try:
                    file_handler = FileHandler()
                    df_raw = file_handler.cargar_excel(archivo)
                    processor = DataProcessor(df_raw)
                    processor.detectar_columnas()
                    
                    st.session_state.df = df_raw
                    st.session_state.columnas = processor.columnas
                    
                    if "generica" in processor.columnas:
                        genericas = sorted(df_raw[processor.columnas["generica"]].unique().tolist())
                        inicializar_programacion(genericas)
                    
                    st.success("✅ Archivo procesado")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        if st.session_state.df is not None:
            st.markdown("---")
            try:
                mostrar_resumen_sidebar()
            except:
                pass
    
    # Main content
    if st.session_state.df is None:
        st.info("👈 Carga un Excel SIAF en el sidebar")
        return
    
    # Calcular indicadores
    try:
        st.session_state.indicadores = calcular_todos_indicadores(
            st.session_state.df,
            st.session_state.columnas,
            fecha_corte=st.session_state.fecha_corte,
        )
    except Exception as e:
        st.error(f"Error calculando indicadores: {e}")
        return
    
    ind = st.session_state.indicadores
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Ejecutivo", "⚙️ Operacional", "🔬 Analítico"])
    
    # TAB 1: Ejecutivo
    with tab1:
        st.markdown("## Ejecución presupuestal")
        st.divider()
        st.markdown("### 📈 KPIs principales")
        
        try:
            grid_kpis([
                {"titulo": "PIM", "valor": ind["ejecucion"]["pim_total"], "formato": "soles"},
                {
                    "titulo": "Certificado",
                    "valor": ind["ejecucion"]["certificado_total"],
                    "formato": "soles",
                    "progreso": ind["ejecucion"]["pct_certificado"],
                    "estado": color_por_avance(ind["ejecucion"]["pct_certificado"]),
                },
                {
                    "titulo": "Devengado",
                    "valor": ind["ejecucion"]["devengado_total"],
                    "formato": "soles",
                    "progreso": ind["ejecucion"]["pct_avance_financiero"],
                    "estado": color_por_avance(ind["ejecucion"]["pct_avance_financiero"]),
                },
                {
                    "titulo": "Forecast",
                    "valor": ind["proyecciones"]["proyeccion_pct"],
                    "formato": "porcentaje",
                    "estado": color_por_avance(ind["proyecciones"]["proyeccion_pct"]),
                },
            ], columnas=4)
        except Exception as e:
            st.error(f"Error en KPIs: {e}")
        
        st.divider()
        st.markdown("### ⚠️ Alertas")
        try:
            panel_alertas(ind["alertas"])
        except:
            st.info("Sin alertas")
        
        st.divider()
        
        # Curva S
        col1, col2 = st.columns([1.2, 1])
        with col1:
            st.markdown("### 📉 Curva S")
            try:
                meses_dev = []
                acumulado = 0
                for col in st.session_state.columnas.get("devengado", []):
                    acumulado += st.session_state.df[col].sum()
                    meses_dev.append(acumulado)
                
                df_prog = obtener_programacion_df()
                meses_prog = []
                if df_prog is not None:
                    acumulado_prog = 0
                    for mes in MESES_ABREV:
                        if mes in df_prog.columns:
                            acumulado_prog += df_prog[mes].sum()
                        meses_prog.append(acumulado_prog)
                else:
                    meses_prog = [0] * len(MESES_ABREV)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=MESES_ABREV, y=meses_dev,
                    name="Devengado",
                    line=dict(color=PALETA["brand"], width=3),
                    fill="tozeroy",
                ))
                fig.add_trace(go.Scatter(
                    x=MESES_ABREV, y=meses_prog,
                    name="Programado",
                    line=dict(color=PALETA["info"]),
                ))
                fig.update_layout(height=250, hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Error: {e}")
        
        with col2:
            st.markdown("### 📊 Por genérica")
            try:
                if "generica" in st.session_state.columnas:
                    for gen in st.session_state.df[st.session_state.columnas["generica"]].unique()[:6]:
                        df_gen = st.session_state.df[st.session_state.df[st.session_state.columnas["generica"]] == gen]
                        pim_gen = df_gen[st.session_state.columnas["pim"]].sum()
                        dev_gen = sum(df_gen[c].sum() for c in st.session_state.columnas.get("devengado", []))
                        pct = (dev_gen / pim_gen * 100) if pim_gen > 0 else 0
                        color = color_por_avance(pct)
                        
                        st.markdown(f"""
                        <div style="margin-bottom: 6px;">
                            <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 2px;">
                                <span>{str(gen)[:30]}</span><span style="font-weight: 600;">{pct:.1f}%</span>
                            </div>
                            <div style="height: 4px; background: #e8e8e8; border-radius: 2px;">
                                <div style="height: 100%; width: {min(pct, 100):.1f}%; background: {color}; border-radius: 2px;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"Error: {e}")
    
    # TAB 2: Operacional
    with tab2:
        st.markdown("## Análisis operacional")
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            ratios = ind["eficiencia"]
            st.metric("Compromiso/Cert", f"{ratios.get('ratio_compro_certif', 0):.1f}%")
        with col2:
            dist = ind["distribucion"]
            if "gasto_corriente_pct" in dist:
                st.metric("Gasto corriente", f"{dist['gasto_corriente_pct']:.1f}%")
        with col3:
            proy = ind["proyecciones"]
            st.metric("Proyección", f"{proy['proyeccion_pct']:.1f}%")
        
        st.divider()
        try:
            mostrar_tabla_resumen(st.session_state.df, st.session_state.columnas)
        except:
            st.warning("No se pudo mostrar tabla")
    
    # TAB 3: Analítico
    with tab3:
        st.markdown("## Análisis analítico")
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        try:
            with col1:
                st.plotly_chart(crear_gauges(st.session_state.df, st.session_state.columnas), use_container_width=True)
        except:
            st.warning("No se pudo renderizar")
        
        st.divider()
        try:
            fig = monthly_chart(st.session_state.df, st.session_state.columnas.get("devengado", []))
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.warning("No se pudo mostrar gráfico")


if __name__ == "__main__":
    main()

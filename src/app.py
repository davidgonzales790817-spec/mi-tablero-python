# src/app.py
# ═══════════════════════════════════════════════════════════════════════════
# APLICACIÓN PRINCIPAL · Tablero Presupuestal SIAF v2.0
# Instituto Peruano de Energía Nuclear (IPEN) · 2026
# ═══════════════════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime
import sys
import os

# Agregar el directorio src al path de Python
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# ─ Importar módulos locales ──────────────────────────────────────────────
from utils.data_processor import DataProcessor
from utils.file_handler import FileHandler
from utils.indicadores import calcular_todos_indicadores
from components.sidebar import mostrar_sidebar
from components.gauges import crear_gauges
from components.monthly_chart import monthly_chart
from components.summary_table import mostrar_tabla_resumen
from components.programacion_form import (
    inicializar_programacion,
    obtener_programacion_df,
    mostrar_formulario_programacion,
    mostrar_resumen_sidebar,
)
from components.kpi_cards import grid_kpis, panel_alertas
from config import PALETA, color_por_avance, MESES_ABREV


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Tablero Presupuestal SIAF · IPEN",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados
st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 600;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-weight: 600;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZACIÓN DE SESSION STATE
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
# FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Flujo principal de la aplicación."""
    
    # Header principal
    col_header_title, col_header_info = st.columns([3, 1])
    
    with col_header_title:
        st.markdown("# 📊 Tablero Presupuestal SIAF")
        st.markdown("**Instituto Peruano de Energía Nuclear (IPEN) · Ejercicio fiscal 2026**")
    
    with col_header_info:
        st.markdown(f"""
        **Corte:** {st.session_state.fecha_corte.strftime('%d/%m/%Y')}
        
        **Status:** {'🟢 En seguimiento' if st.session_state.df is not None else '⚠️ Cargando datos'}
        """)
    
    st.divider()
    
    # ─────────────────────────────────────────────────────────────────────
    # SIDEBAR
    # ─────────────────────────────────────────────────────────────────────
    
    with st.sidebar:
        st.markdown("### 📁 Carga de datos")
        
        # Widget de carga de archivo
        archivo = st.file_uploader(
            "Subir archivo Excel SIAF",
            type=['xlsx', 'xls'],
            help="Archivo exportado directamente del SIAF-MEF"
        )
        
        if archivo:
            # Procesar archivo con DataProcessor
            with st.spinner("🔄 Procesando archivo..."):
                try:
                    file_handler = FileHandler()
                    df_raw = file_handler.cargar_excel(archivo)
                    
                    # Detectar automáticamente columnas
                    processor = DataProcessor(df_raw)
                    processor.detectar_columnas()
                    
                    st.session_state.df = df_raw
                    st.session_state.columnas = processor.columnas
                    
                    # Inicializar programación si hay genéricas
                    if "generica" in processor.columnas:
                        genericas = sorted(df_raw[processor.columnas["generica"]].unique().tolist())
                        inicializar_programacion(genericas)
                    
                    st.success("✅ Archivo procesado correctamente")
                
                except Exception as e:
                    st.error(f"Error procesando archivo: {e}")
                    return
        
        if st.session_state.df is not None:
            st.markdown("---")
            
            # Mostrar resumen en sidebar
            try:
                mostrar_resumen_sidebar()
            except Exception as e:
                st.warning(f"No se pudo mostrar resumen: {e}")
            
            st.markdown("---")
            
            # Selector de fecha de corte
            fecha_selector = st.date_input(
                "Fecha de corte (para proyecciones)",
                value=st.session_state.fecha_corte,
                max_value=date(2026, 12, 31),
                min_value=date(2026, 1, 1)
            )
            st.session_state.fecha_corte = fecha_selector
    
    # ─────────────────────────────────────────────────────────────────────
    # CONTENIDO PRINCIPAL
    # ─────────────────────────────────────────────────────────────────────
    
    if st.session_state.df is None:
        st.info("👈 Carga un archivo Excel SIAF en el sidebar para comenzar")
        return
    
    # Calcular indicadores v2.0 (los 47 indicadores derivables)
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
    
    # Crear tabs para las 3 vistas
    tab_ejecutivo, tab_operacional, tab_analitico = st.tabs([
        "📊 Ejecutivo",
        "⚙️ Operacional",
        "🔬 Analítico",
    ])
    
    # ═════════════════════════════════════════════════════════════════════
    # TAB 1: VISTA EJECUTIVA
    # ═════════════════════════════════════════════════════════════════════
    
    with tab_ejecutivo:
        st.markdown("## Ejecución presupuestal · Visión ejecutiva")
        st.markdown(f"*Actualizado al {ind['fecha_corte']}*")
        st.divider()
        
        # KPI CARDS principales
        st.markdown("### 📈 Indicadores principales")
        
        try:
            grid_kpis([
                {
                    "titulo": "PIM",
                    "valor": ind["ejecucion"]["pim_total"],
                    "formato": "soles",
                    "subtitulo": "Presupuesto Inicial Modificado",
                },
                {
                    "titulo": "Certificado",
                    "valor": ind["ejecucion"]["certificado_total"],
                    "formato": "soles",
                    "progreso": ind["ejecucion"]["pct_certificado"],
                    "target": 33,
                    "estado": color_por_avance(ind["ejecucion"]["pct_certificado"]),
                },
                {
                    "titulo": "Compromiso",
                    "valor": ind["ejecucion"]["compromiso_total"],
                    "formato": "soles",
                    "progreso": ind["ejecucion"]["pct_compromiso"],
                    "target": 33,
                    "estado": color_por_avance(ind["ejecucion"]["pct_compromiso"]),
                },
                {
                    "titulo": "Devengado",
                    "valor": ind["ejecucion"]["devengado_total"],
                    "formato": "soles",
                    "progreso": ind["ejecucion"]["pct_avance_financiero"],
                    "target": 33,
                    "estado": color_por_avance(ind["ejecucion"]["pct_avance_financiero"]),
                    "subtitulo": "📊 Indicador oficial MEF",
                },
                {
                    "titulo": "Saldo certificable",
                    "valor": ind["ejecucion"]["saldo_certificable"],
                    "formato": "soles",
                    "subtitulo": "Aún por certificar",
                },
                {
                    "titulo": "Pendiente de girar",
                    "valor": ind["ejecucion"]["pendiente_girar"],
                    "formato": "soles",
                    "estado": "warning" if ind["ejecucion"]["pendiente_girar"] > 0 else "success",
                    "subtitulo": "En tesorería",
                },
                {
                    "titulo": "Forecast cierre",
                    "valor": ind["proyecciones"]["proyeccion_pct"],
                    "valor_es_porcentaje": True,
                    "formato": "porcentaje",
                    "estado": color_por_avance(ind["proyecciones"]["proyeccion_pct"]),
                    "subtitulo": f"Brecha: S/ {ind['proyecciones']['brecha_proyectada']/1e6:.1f}M",
                },
                {
                    "titulo": "Velocidad",
                    "valor": ind["proyecciones"]["multiplicador_aceleracion"],
                    "formato": "numero",
                    "estado": "danger" if ind["proyecciones"]["multiplicador_aceleracion"] > 2 else "warning",
                    "subtitulo": f"{ind['proyecciones']['multiplicador_aceleracion']:.1f}× requerido",
                },
            ], columnas=4)
        except Exception as e:
            st.error(f"Error renderizando KPI cards: {e}")
        
        st.divider()
        
        # ALERTAS
        st.markdown("### ⚠️ Alertas activas")
        try:
            panel_alertas(ind["alertas"])
        except Exception as e:
            st.warning(f"Error mostrando alertas: {e}")
        
        st.divider()
        
        # CURVA S y ejecución por genérica
        col_curva, col_generica = st.columns([1.2, 1])
        
        with col_curva:
            st.markdown("### 📉 Curva S")
            
            try:
                meses_dev = []
                acumulado = 0
                for col in st.session_state.columnas.get("devengado", []):
                    acumulado += st.session_state.df[col].sum()
                    meses_dev.append(acumulado)
                
                df_prog = obtener_programacion_df()
                if df_prog is not None:
                    meses_prog = []
                    acumulado_prog = 0
                    for mes in MESES_ABREV:
                        if mes in df_prog.columns:
                            acumulado_prog += df_prog[mes].sum()
                        meses_prog.append(acumulado_prog)
                else:
                    meses_prog = [0] * len(MESES_ABREV)
                
                fig_curva = go.Figure()
                
                fig_curva.add_trace(go.Scatter(
                    x=MESES_ABREV, y=meses_dev,
                    name="Devengado real",
                    mode="lines+markers",
                    line=dict(color=PALETA["brand"], width=3),
                    marker=dict(size=8),
                    fill="tozeroy",
                    fillcolor=f"{PALETA['brand']}30",
                ))
                
                fig_curva.add_trace(go.Scatter(
                    x=MESES_ABREV, y=meses_prog,
                    name="Programado",
                    mode="lines",
                    line=dict(color=PALETA["info"], width=2),
                ))
                
                fig_curva.update_layout(
                    hovermode="x unified",
                    template="plotly_white",
                    height=300,
                    margin=dict(l=0, r=0, t=30, b=0),
                )
                
                st.plotly_chart(fig_curva, use_container_width=True)
            
            except Exception as e:
                st.warning(f"Error en curva S: {e}")
        
        with col_generica:
            st.markdown("### 📊 Por genérica")
            
            try:
                if "generica" in st.session_state.columnas:
                    gen_avance = []
                    for gen in st.session_state.df[st.session_state.columnas["generica"]].unique():
                        df_gen = st.session_state.df[st.session_state.df[st.session_state.columnas["generica"]] == gen]
                        pim_gen = df_gen[st.session_state.columnas["pim"]].sum() if st.session_state.columnas.get("pim") else 0
                        dev_gen = sum(df_gen[c].sum() for c in st.session_state.columnas.get("devengado", []))
                        pct = (dev_gen / pim_gen * 100) if pim_gen > 0 else 0
                        gen_avance.append({"genérica": gen, "avance": pct})
                    
                    gen_avance_sorted = sorted(gen_avance, key=lambda x: x["avance"], reverse=True)
                    
                    for item in gen_avance_sorted[:6]:  # Top 6
                        color = color_por_avance(item["avance"])
                        st.markdown(f"""
                        <div style="margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                                <span style="font-size: 11px;">{item['genérica'][:35]}</span>
                                <span style="font-size: 11px; font-weight: 600;">{item['avance']:.1f}%</span>
                            </div>
                            <div style="height: 5px; background: #e8e8e8; border-radius: 2px; position: relative;">
                                <div style="position: absolute; height: 100%; width: {min(item['avance'], 100):.1f}%; background: {color}; border-radius: 2px;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            
            except Exception as e:
                st.warning(f"Error: {e}")
    
    # ═════════════════════════════════════════════════════════════════════
    # TAB 2: VISTA OPERACIONAL
    # ═════════════════════════════════════════════════════════════════════
    
    with tab_operacional:
        st.markdown("## Análisis operacional")
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 📈 Ratios")
            ratios = ind["eficiencia"]
            st.metric("Compromiso/Certificado", f"{ratios.get('ratio_compro_certif', 0):.1f}%")
            st.metric("Devengado/Compromiso", f"{ratios.get('ratio_deveng_compro', 0):.1f}%")
        
        with col2:
            st.markdown("### 💰 Distribución")
            dist = ind["distribucion"]
            if "gasto_corriente_pct" in dist:
                st.metric("Gasto corriente", f"{dist['gasto_corriente_pct']:.1f}%")
                st.metric("Gasto de capital", f"{dist['gasto_capital_pct']:.1f}%")
        
        with col3:
            st.markdown("### 🎯 Proyecciones")
            proy = ind["proyecciones"]
            st.metric("Proyección cierre", f"{proy['proyeccion_pct']:.1f}%")
            st.metric("Días restantes", proy.get("dias_restantes_fiscal", 0))
        
        st.divider()
        try:
            mostrar_tabla_resumen(st.session_state.df, st.session_state.columnas)
        except Exception as e:
            st.warning(f"Error en tabla: {e}")
    
    # ═════════════════════════════════════════════════════════════════════
    # TAB 3: VISTA ANALÍTICA
    # ═════════════════════════════════════════════════════════════════════
    
    with tab_analitico:
        st.markdown("## Análisis analítico")
        st.divider()
        st.info("Gráficos de ejecución detallada")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            try:
                st.plotly_chart(crear_gauges(st.session_state.df, st.session_state.columnas), use_container_width=True)
            except:
                st.warning("No se pudo renderizar gauge")
        
        with col2:
            try:
                if st.session_state.columnas.get("certificado"):
                    pim = st.session_state.df[st.session_state.columnas["pim"]].sum()
                    cert = st.session_state.df[st.session_state.columnas["certificado"]].sum()
                    pct = (cert / pim * 100) if pim > 0 else 0
                    
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=pct,
                        title="Certificado",
                        gauge={"axis": {"range": [None, 100]}, "bar": {"color": PALETA["info"]}}
                    ))
                    fig.update_layout(height=300, margin=dict(l=0, r=0, t=60, b=0))
                    st.plotly_chart(fig, use_container_width=True)
            except:
                st.warning("No se pudo renderizar")
        
        with col3:
            try:
                if st.session_state.columnas.get("compromiso"):
                    pim = st.session_state.df[st.session_state.columnas["pim"]].sum()
                    comp = st.session_state.df[st.session_state.columnas["compromiso"]].sum()
                    pct = (comp / pim * 100) if pim > 0 else 0
                    
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=pct,
                        title="Compromiso",
                        gauge={"axis": {"range": [None, 100]}, "bar": {"color": PALETA["warning"]}}
                    ))
                    fig.update_layout(height=300, margin=dict(l=0, r=0, t=60, b=0))
                    st.plotly_chart(fig, use_container_width=True)
            except:
                st.warning("No se pudo renderizar")
        
        st.divider()
        try:
            fig = monthly_chart(st.session_state.df, st.session_state.columnas.get("devengado", []))
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Error: {e}")


# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    main()

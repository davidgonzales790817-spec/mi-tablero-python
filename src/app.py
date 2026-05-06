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

st.set_page_config(page_title="Tablero SIAF · IPEN", page_icon="📊", layout="wide")

for k, v in {"df": None, "df_procesado": None, "columnas": {},
             "cols_devengado": [], "fecha_corte": date.today()}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# SIDEBAR
with st.sidebar:
    try: mostrar_logo()
    except: st.markdown("### 📊 IPEN")

    st.markdown("---")
    st.markdown("### 📁 Carga de datos")
    archivo = st.file_uploader("Subir Excel SIAF", type=["xls", "xlsx"])

    if archivo:
        with st.spinner("Procesando..."):
            try:
                engine = "xlrd" if archivo.name.lower().endswith(".xls") else "openpyxl"
                df_raw = pd.read_excel(archivo, engine=engine)
                processor = DataProcessor(df_raw)
                processor.normalizar_columnas()
                processor.detectar_columnas_devengado()
                processor.detectar_otras_columnas()
                st.session_state.df             = df_raw
                st.session_state.df_procesado   = processor.df
                st.session_state.columnas       = processor.columnas
                st.session_state.cols_devengado = processor.columnas_devengado
                col_gen = processor.col_generica
                if col_gen and col_gen in processor.df.columns:
                    gens = sorted(processor.df[col_gen].dropna().unique().tolist())
                    inicializar_programacion(gens)
                st.success(f"✅ {archivo.name}")
            except Exception as e:
                st.error(f"Error: {e}")

    if st.session_state.df is not None:
        st.markdown("---")
        try: mostrar_resumen_sidebar()
        except: pass
        st.markdown("---")
        st.session_state.fecha_corte = st.date_input(
            "Fecha de corte", value=st.session_state.fecha_corte,
            min_value=date(2026, 1, 1), max_value=date(2026, 12, 31))

# HEADER
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("# 📊 Tablero Presupuestal SIAF")
    st.markdown("**IPEN · Ejercicio fiscal 2026**")
with c2:
    st.markdown(f"**Corte:** {st.session_state.fecha_corte.strftime('%d/%m/%Y')}")
st.divider()

if st.session_state.df is None:
    st.info("👈 Sube un Excel SIAF en el sidebar para comenzar")
    st.stop()

df   = st.session_state.df_procesado or st.session_state.df
cols = st.session_state.columnas

try:
    ind = calcular_todos_indicadores(df, cols, fecha_corte=st.session_state.fecha_corte)
except Exception as e:
    st.error(f"Error calculando indicadores: {e}")
    st.stop()

t1, t2, t3 = st.tabs(["📊 Ejecutivo", "⚙️ Operacional", "🔬 Analítico"])

# TAB 1
with t1:
    st.markdown("## Ejecución presupuestal")
    st.divider()
    try:
        grid_kpis([
            {"titulo": "PIM", "valor": ind["ejecucion"]["pim_total"], "formato": "soles"},
            {"titulo": "Certificado", "valor": ind["ejecucion"]["certificado_total"],
             "formato": "soles", "progreso": ind["ejecucion"]["pct_certificado"],
             "target": 33, "estado": color_por_avance(ind["ejecucion"]["pct_certificado"])},
            {"titulo": "Devengado", "valor": ind["ejecucion"]["devengado_total"],
             "formato": "soles", "progreso": ind["ejecucion"]["pct_avance_financiero"],
             "target": 33, "estado": color_por_avance(ind["ejecucion"]["pct_avance_financiero"]),
             "subtitulo": "Indicador oficial MEF"},
            {"titulo": "Forecast cierre", "valor": ind["proyecciones"]["proyeccion_pct"],
             "formato": "porcentaje", "estado": color_por_avance(ind["proyecciones"]["proyeccion_pct"]),
             "subtitulo": f"Brecha S/ {ind['proyecciones']['brecha_proyectada']/1e6:.1f}M"},
        ], columnas=4)
    except Exception as e:
        st.error(f"Error KPI cards: {e}")

    st.divider()
    st.markdown("### Alertas")
    try: panel_alertas(ind["alertas"])
    except: st.info("Sin alertas")

    st.divider()
    col_curva, col_gen = st.columns([1.2, 1])
    with col_curva:
        st.markdown("### 📉 Curva S")
        try:
            meses_dev, acum = [], 0
            for c in st.session_state.cols_devengado:
                acum += df[c].sum(); meses_dev.append(acum)
            df_prog = obtener_programacion_df()
            meses_prog, acum_p = [], 0
            for mes in MESES_ABREV:
                if df_prog is not None and mes in df_prog.columns:
                    acum_p += df_prog[mes].sum()
                meses_prog.append(acum_p)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=MESES_ABREV, y=meses_dev, name="Devengado",
                line=dict(color=PALETA["brand"], width=3), fill="tozeroy"))
            fig.add_trace(go.Scatter(x=MESES_ABREV, y=meses_prog, name="Programado",
                line=dict(color=PALETA["info"], width=2, dash="dot")))
            fig.update_layout(height=260, hovermode="x unified", margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Error: {e}")

    with col_gen:
        st.markdown("### 📊 Por genérica")
        try:
            col_pim = cols.get("pim", "mto_pim")
            col_generica = None
            for c in df.columns:
                if re.search(r"^generica$", c, re.I): col_generica = c; break
            if col_generica:
                for gen in df[col_generica].dropna().unique()[:6]:
                    df_g  = df[df[col_generica] == gen]
                    pim_g = df_g[col_pim].sum() if col_pim in df_g else 0
                    dev_g = sum(df_g[c].sum() for c in st.session_state.cols_devengado if c in df_g)
                    pct   = (dev_g / pim_g * 100) if pim_g > 0 else 0
                    color = color_por_avance(pct)
                    st.markdown(f"""<div style="margin-bottom:6px;">
                      <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:2px;">
                        <span>{str(gen)[:32]}</span><b>{pct:.1f}%</b></div>
                      <div style="height:5px;background:#e4e4e7;border-radius:3px;">
                        <div style="height:100%;width:{min(pct,100):.1f}%;background:{color};border-radius:3px;"></div>
                      </div></div>""", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Error: {e}")

# TAB 2
with t2:
    st.markdown("## Análisis operacional")
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### Ratios")
        r = ind["eficiencia"]
        st.metric("Comprometido/Cert", f"{r.get('ratio_compro_certif', 0):.1f}%")
        st.metric("Devengado/Comprom", f"{r.get('ratio_deveng_compro', 0):.1f}%")
    with c2:
        st.markdown("### Distribución")
        d = ind["distribucion"]
        if "gasto_corriente_pct" in d:
            st.metric("Gasto corriente", f"{d['gasto_corriente_pct']:.1f}%")
            st.metric("Gasto capital",   f"{d['gasto_capital_pct']:.1f}%")
    with c3:
        st.markdown("### Proyección")
        p = ind["proyecciones"]
        st.metric("Forecast cierre", f"{p['proyeccion_pct']:.1f}%")
        st.metric("Días restantes",  p.get("dias_restantes_fiscal", 0))
    st.divider()
    try: crear_tabla_resumen(df)
    except Exception as e: st.warning(f"Error tabla: {e}")

# TAB 3
with t3:
    st.markdown("## Análisis analítico")
    st.divider()
    try:
        mostrar_indicadores(
            ind["ejecucion"]["pim_total"],
            ind["ejecucion"]["certificado_total"],
            ind["ejecucion"]["compromiso_total"],
            ind["ejecucion"]["devengado_total"],
        )
    except Exception as e:
        st.warning(f"Error gauges: {e}")
    st.divider()
    st.markdown("### 📊 Evolución mensual")
    try:
        df_prog = obtener_programacion_df()
        fig = crear_grafico_mensual(df, st.session_state.cols_devengado, df_prog)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Error: {e}")
    st.divider()
    st.markdown("### 📅 Programación mensual")
    try:
        col_gen_key = cols.get("generica", "generica")
        if col_gen_key in df.columns:
            gens = sorted(df[col_gen_key].dropna().unique().tolist())
            mostrar_formulario_programacion(gens)
    except Exception as e:
        st.warning(f"Error formulario: {e}")

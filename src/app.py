# src/app.py
# ═══════════════════════════════════════════════════════════════════════════
# TABLERO PRESUPUESTAL SIAF v2.0 · IPEN 2026
# ═══════════════════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
import sys
import os

# Agregar src/ al path
sys.path.insert(0, os.path.dirname(__file__))

# ─ Imports usando nombres EXACTOS de cada módulo ─────────────────────────

# utils/data_processor.py  → clase DataProcessor
from utils.data_processor import DataProcessor

# utils/file_handler.py    → funciones sueltas (no clase)
from utils.file_handler import widget_carga_archivo, cargar_excel

# utils/indicadores.py     → calcular_todos_indicadores
from utils.indicadores import calcular_todos_indicadores

# components/gauges.py     → crear_gauge (singular), mostrar_indicadores
from components.gauges import crear_gauge, mostrar_indicadores

# components/monthly_chart.py → crear_grafico_mensual
from components.monthly_chart import crear_grafico_mensual

# components/summary_table.py → crear_tabla_resumen
from components.summary_table import crear_tabla_resumen

# components/sidebar.py   → crear_filtros, mostrar_logo
from components.sidebar import crear_filtros, mostrar_logo

# components/programacion_form.py → varias funciones
from components.programacion_form import (
    inicializar_programacion,
    obtener_programacion_df,
    mostrar_resumen_sidebar,
    mostrar_formulario_programacion,
)

# components/kpi_cards.py → grid_kpis, panel_alertas
from components.kpi_cards import grid_kpis, panel_alertas

# config.py → constantes
from config import PALETA, color_por_avance, MESES_ABREV


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
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

for key, default in {
    "df": None,
    "df_raw": None,
    "df_procesado": None,
    "columnas": {},
    "cols_devengado": [],
    "indicadores": None,
    "fecha_corte": date.today(),
    "archivo_activo": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════

def render_sidebar():
    """Renderiza el sidebar completo."""
    with st.sidebar:
        # Logo
        try:
            mostrar_logo()
        except Exception:
            st.markdown("### 📊 IPEN")

        st.markdown("---")

        # Carga de archivo
        st.markdown("### 📁 Carga de datos")
        archivo = st.file_uploader(
            "Subir Excel SIAF",
            type=["xls", "xlsx"],
            help="Archivo exportado del SIAF-MEF",
        )

        if archivo is not None:
            with st.spinner("Procesando..."):
                try:
                    engine = "xlrd" if archivo.name.lower().endswith(".xls") else "openpyxl"
                    df_raw = pd.read_excel(archivo, engine=engine)

                    processor = DataProcessor(df_raw)
                    processor.normalizar_columnas()
                    processor.detectar_columnas_devengado()
                    processor.detectar_otras_columnas()

                    st.session_state.df_raw      = df_raw
                    st.session_state.df          = df_raw
                    st.session_state.df_procesado = processor.df
                    st.session_state.columnas    = processor.columnas
                    st.session_state.cols_devengado = processor.columnas_devengado
                    st.session_state.archivo_activo = archivo.name

                    # Inicializar programación
                    col_gen = processor.col_generica
                    if col_gen and col_gen in processor.df.columns:
                        genericas = sorted(processor.df[col_gen].dropna().unique().tolist())
                        inicializar_programacion(genericas)

                    st.success(f"✅ {archivo.name}")

                except Exception as e:
                    st.error(f"Error: {e}")

        if st.session_state.df is not None:
            st.markdown("---")
            try:
                mostrar_resumen_sidebar()
            except Exception:
                pass

            st.markdown("---")
            st.session_state.fecha_corte = st.date_input(
                "Fecha de corte",
                value=st.session_state.fecha_corte,
                min_value=date(2026, 1, 1),
                max_value=date(2026, 12, 31),
            )


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def get_totales(df, cols):
    """Calcula totales principales del DataFrame."""
    pim   = df[cols.get("pim",   "")].sum() if cols.get("pim")   else 0
    cert  = df[cols.get("cert",  "")].sum() if cols.get("cert")  else 0
    comp  = df[cols.get("comp",  "")].sum() if cols.get("comp")  else 0
    dev   = sum(df[c].sum() for c in st.session_state.cols_devengado)
    girado = df[cols.get("girado", "")].sum() if cols.get("girado") else 0
    pagado = df[cols.get("pagado", "")].sum() if cols.get("pagado") else 0
    return pim, cert, comp, dev, girado, pagado


# ═══════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════

def tab_ejecutivo(df, cols, ind):
    """Vista ejecutiva: KPIs + alertas + curva S."""
    st.markdown("## Ejecución presupuestal · Vista ejecutiva")
    st.divider()

    # KPI cards
    st.markdown("### 📈 Indicadores principales")
    try:
        grid_kpis([
            {
                "titulo": "PIM",
                "valor": ind["ejecucion"]["pim_total"],
                "formato": "soles",
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
                "titulo": "Devengado",
                "valor": ind["ejecucion"]["devengado_total"],
                "formato": "soles",
                "progreso": ind["ejecucion"]["pct_avance_financiero"],
                "target": 33,
                "estado": color_por_avance(ind["ejecucion"]["pct_avance_financiero"]),
                "subtitulo": "📊 Indicador oficial MEF",
            },
            {
                "titulo": "Forecast cierre",
                "valor": ind["proyecciones"]["proyeccion_pct"],
                "formato": "porcentaje",
                "estado": color_por_avance(ind["proyecciones"]["proyeccion_pct"]),
                "subtitulo": f"Brecha S/ {ind['proyecciones']['brecha_proyectada']/1e6:.1f}M",
            },
        ], columnas=4)
    except Exception as e:
        st.error(f"Error en KPI cards: {e}")

    st.divider()

    # Alertas
    st.markdown("### ⚠️ Alertas activas")
    try:
        panel_alertas(ind["alertas"])
    except Exception:
        st.info("Sin alertas registradas")

    st.divider()

    # Curva S + ejecución por genérica
    col_curva, col_gen = st.columns([1.2, 1])

    with col_curva:
        st.markdown("### 📉 Curva S")
        try:
            # Devengado acumulado mensual
            meses_dev = []
            acum = 0
            for c in st.session_state.cols_devengado:
                acum += df[c].sum()
                meses_dev.append(acum)

            # Programación acumulada
            df_prog = obtener_programacion_df()
            meses_prog = []
            if df_prog is not None:
                acum_prog = 0
                for mes in MESES_ABREV:
                    if mes in df_prog.columns:
                        acum_prog += df_prog[mes].sum()
                    meses_prog.append(acum_prog)
            else:
                meses_prog = [0] * len(MESES_ABREV)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=MESES_ABREV, y=meses_dev,
                name="Devengado",
                line=dict(color=PALETA["brand"], width=3),
                fill="tozeroy",
                fillcolor=f"{PALETA['brand']}30",
            ))
            fig.add_trace(go.Scatter(
                x=MESES_ABREV, y=meses_prog,
                name="Programado",
                line=dict(color=PALETA["info"], width=2, dash="dot"),
            ))
            fig.update_layout(height=260, hovermode="x unified",
                              margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.warning(f"Error: {e}")

    with col_gen:
        st.markdown("### 📊 Por genérica")
        try:
            col_generica = cols.get("generica") or processor_col_generica(df)
            col_pim      = cols.get("pim", "mto_pim")

            if col_generica and col_generica in df.columns:
                for gen in df[col_generica].unique()[:6]:
                    df_g    = df[df[col_generica] == gen]
                    pim_g   = df_g[col_pim].sum() if col_pim in df_g.columns else 0
                    dev_g   = sum(df_g[c].sum() for c in st.session_state.cols_devengado if c in df_g.columns)
                    pct     = (dev_g / pim_g * 100) if pim_g > 0 else 0
                    color   = color_por_avance(pct)

                    st.markdown(f"""
                    <div style="margin-bottom:6px;">
                        <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:2px;">
                            <span>{str(gen)[:32]}</span>
                            <b>{pct:.1f}%</b>
                        </div>
                        <div style="height:5px;background:#e4e4e7;border-radius:3px;">
                            <div style="height:100%;width:{min(pct,100):.1f}%;
                                        background:{color};border-radius:3px;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        except Exception as e:
            st.warning(f"Error: {e}")


def tab_operacional(df, cols, ind):
    """Vista operacional: ratios + tabla."""
    st.markdown("## Análisis operacional")
    st.divider()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 📈 Ratios")
        r = ind["eficiencia"]
        st.metric("Comprometido/Cert",  f"{r.get('ratio_compro_certif', 0):.1f}%")
        st.metric("Devengado/Comprom",  f"{r.get('ratio_deveng_compro', 0):.1f}%")
    with c2:
        st.markdown("### 💰 Distribución")
        d = ind["distribucion"]
        if "gasto_corriente_pct" in d:
            st.metric("Gasto corriente", f"{d['gasto_corriente_pct']:.1f}%")
            st.metric("Gasto capital",   f"{d['gasto_capital_pct']:.1f}%")
    with c3:
        st.markdown("### 🎯 Proyección")
        p = ind["proyecciones"]
        st.metric("Forecast cierre",  f"{p['proyeccion_pct']:.1f}%")
        st.metric("Días restantes",   p.get("dias_restantes_fiscal", 0))

    st.divider()

    # Tabla resumen usando crear_tabla_resumen (la función real)
    try:
        tabla = crear_tabla_resumen(df)
        st.dataframe(tabla, use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning(f"No se pudo mostrar tabla: {e}")


def tab_analitico(df, cols, ind):
    """Vista analítica: gauges + gráfico mensual."""
    st.markdown("## Análisis analítico")
    st.divider()

    # Gauges usando mostrar_indicadores (la función real)
    try:
        pim   = ind["ejecucion"]["pim_total"]
        cert  = ind["ejecucion"]["certificado_total"]
        comp  = ind["ejecucion"]["compromiso_total"]
        dev   = ind["ejecucion"]["devengado_total"]
        mostrar_indicadores(pim, cert, comp, dev)
    except Exception as e:
        st.warning(f"Error en gauges: {e}")

    st.divider()

    # Gráfico mensual usando crear_grafico_mensual (la función real)
    st.markdown("### 📊 Evolución mensual del devengado")
    try:
        df_prog = obtener_programacion_df()
        fig = crear_grafico_mensual(df, st.session_state.cols_devengado, df_prog)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Error en gráfico: {e}")

    st.divider()

    # Formulario programación
    st.markdown("### 📅 Programación mensual")
    try:
        col_gen = cols.get("generica")
        if col_gen and col_gen in df.columns:
            genericas = sorted(df[col_gen].dropna().unique().tolist())
            mostrar_formulario_programacion(genericas)
    except Exception as e:
        st.warning(f"Error en formulario: {e}")


def processor_col_generica(df):
    """Detecta la columna genérica del df si no está en cols."""
    import re
    for col in df.columns:
        if re.search(r"^generica$|^genérica$", col, re.IGNORECASE):
            return col
    return None


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    # Sidebar
    render_sidebar()

    # Header
    h1, h2 = st.columns([3, 1])
    with h1:
        st.markdown("# 📊 Tablero Presupuestal SIAF")
        st.markdown("**IPEN · Ejercicio fiscal 2026**")
    with h2:
        st.markdown(f"**Corte:** {st.session_state.fecha_corte.strftime('%d/%m/%Y')}")
        if st.session_state.df is not None:
            st.markdown("🟢 Datos cargados")

    st.divider()

    # Sin datos
    if st.session_state.df is None:
        st.info("👈 Sube un archivo Excel SIAF en el sidebar para comenzar")
        return

    df   = st.session_state.df_procesado or st.session_state.df
    cols = st.session_state.columnas

    # Calcular indicadores
    try:
        ind = calcular_todos_indicadores(
            df, cols, fecha_corte=st.session_state.fecha_corte
        )
        st.session_state.indicadores = ind
    except Exception as e:
        st.error(f"Error calculando indicadores: {e}")
        return

    # Tabs principales
    t1, t2, t3 = st.tabs(["📊 Ejecutivo", "⚙️ Operacional", "🔬 Analítico"])

    with t1:
        tab_ejecutivo(df, cols, ind)
    with t2:
        tab_operacional(df, cols, ind)
    with t3:
        tab_analitico(df, cols, ind)


if __name__ == "__main__":
    main()

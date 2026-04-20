# src/app.py
# ─────────────────────────────────────────────────────────────────────────────
# Tablero Presupuestal SIAF
# Punto de entrada principal de la aplicación Streamlit
#
# Ejecutar desde la carpeta raíz del proyecto:
#   streamlit run src/app.py
#
# Dependencias:
#   pip install streamlit pandas plotly openpyxl xlrd pytz
# ─────────────────────────────────────────────────────────────────────────────

import pytz
import pandas as pd
import streamlit as st
from datetime import datetime

from config import PAGE_CONFIG, CSS_EXTRA

from utils.file_handler    import widget_carga_archivo
from utils.data_processor  import DataProcessor

from components.sidebar           import mostrar_logo, crear_filtros
from components.gauges            import mostrar_indicadores
from components.summary_table     import crear_tabla_resumen
from components.monthly_chart     import crear_grafico_mensual
from components.programacion_form import (
    mostrar_formulario_programacion,
    mostrar_resumen_sidebar,
    obtener_programacion_df,
)

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(**PAGE_CONFIG)
st.markdown(CSS_EXTRA, unsafe_allow_html=True)


# ── Inicialización de session_state ──────────────────────────────────────────

def _init_state():
    defaults = {
        "df_raw":          None,
        "df_procesado":    None,
        "cols_devengado":  [],
        "archivo_activo":  None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Carga y procesamiento del Excel ──────────────────────────────────────────

def _cargar_y_procesar(ruta: str):
    """Lee el Excel y ejecuta el pipeline de DataProcessor."""
    from utils.file_handler import cargar_excel
    df_raw = cargar_excel(ruta)
    if df_raw is None:
        return

    procesador = DataProcessor(df_raw)
    procesador.procesar_completo()
    df_proc   = procesador.obtener_dataframe()
    cols_dev  = procesador.obtener_columnas_devengado()

    if df_proc.empty:
        st.warning("⚠️ No hay filas válidas después del procesamiento.")
        return

    st.session_state.df_raw         = df_raw
    st.session_state.df_procesado   = df_proc
    st.session_state.cols_devengado = cols_dev


# ── Pantalla de bienvenida ────────────────────────────────────────────────────

def _pantalla_bienvenida():
    st.markdown(
        """
        <div style="text-align:center; margin-top:100px;">
          <h1 style="color:#1e3a5f;">📊 Tablero Presupuestal SIAF</h1>
          <p style="color:#64748b; font-size:17px; margin-top:12px;">
            Carga un archivo Excel del SIAF desde la barra lateral para comenzar.<br>
            Formatos soportados: <code>.xls</code> y <code>.xlsx</code>
          </p>
          <p style="color:#94a3b8; font-size:13px; margin-top:24px;">
            Los archivos se guardan automáticamente en <code>Respaldo_Data/</code>
            y estarán disponibles para futuras sesiones.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Header de la aplicación ───────────────────────────────────────────────────

def _render_header(df_proc: pd.DataFrame):
    zona_lima    = pytz.timezone("America/Lima")
    fecha_act    = datetime.now(zona_lima).strftime("%d/%m/%Y %H:%M")
    pliego       = df_proc["pliego"].iloc[0]  if "pliego"  in df_proc.columns else "—"
    ano_eje      = df_proc["ano_eje"].iloc[0] if "ano_eje" in df_proc.columns else "—"

    col_h, col_f = st.columns([4, 1])
    with col_h:
        st.markdown(
            f'<p class="header-sub">Ejecución Presupuestal · Año Fiscal {ano_eje}</p>'
            f'<p class="header-title">{pliego}</p>',
            unsafe_allow_html=True,
        )
    with col_f:
        st.markdown(
            f'<p class="header-sub" style="text-align:right">Actualizado</p>'
            f'<p class="header-sub" style="text-align:right; color:#1e3a5f; font-weight:600">'
            f'{fecha_act}<br><small>hora Lima, Perú</small></p>',
            unsafe_allow_html=True,
        )
    st.markdown("---")


# ── KPIs superiores ───────────────────────────────────────────────────────────

def _render_kpis(df: pd.DataFrame):
    fmt = lambda v: f"S/ {round(v):,}".replace(",", ".")
    pim   = df["PIM"].sum()
    cert  = df["Certificado"].sum()
    comp  = df["Compromiso_Anual"].sum()
    dev   = df["Devengado_Total"].sum()
    saldo = pim - dev

    pct = lambda v: f"{v / pim * 100:.1f}% del PIM" if pim else "—"

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("PIM",             fmt(pim))
    k2.metric("Certificado",     fmt(cert),  pct(cert))
    k3.metric("Compromiso",      fmt(comp),  pct(comp))
    k4.metric("Devengado",       fmt(dev),   pct(dev))
    k5.metric("Saldo Pendiente", fmt(saldo), f"{saldo / pim * 100:.1f}% sin ejecutar" if pim else "—")

    return pim, cert, comp, dev


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    _init_state()

    # ── Sidebar: logo + archivo ───────────────────────────────────────────────
    mostrar_logo()
    archivo_activo = widget_carga_archivo()

    # Procesar si el archivo cambió
    if archivo_activo and st.session_state.df_raw is None:
        _cargar_y_procesar(archivo_activo)

    # Sin datos → pantalla de bienvenida
    if st.session_state.df_procesado is None:
        _pantalla_bienvenida()
        return

    df_proc     = st.session_state.df_procesado
    cols_dev    = st.session_state.cols_devengado

    # ── Sidebar: filtros + resumen programación ───────────────────────────────
    st.sidebar.markdown("---")
    df_filtrado = crear_filtros(df_proc)
    mostrar_resumen_sidebar()

    if df_filtrado is None or df_filtrado.empty:
        st.warning("⚠️ Sin datos para los filtros actuales.")
        return

    # ── Header + KPIs ─────────────────────────────────────────────────────────
    _render_header(df_proc)
    pim, cert, comp, dev = _render_kpis(df_filtrado)

    # ── Tabs principales ──────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Indicadores",
        "📊 Por Genérica",
        "📆 Evolución Mensual",
        "📅 Programación",
    ])

    # ── Tab 1: Gauges ─────────────────────────────────────────────────────────
    with tab1:
        mostrar_indicadores(pim, cert, comp, dev)

    # ── Tab 2: Tabla resumen + drill-down ─────────────────────────────────────
    with tab2:
        crear_tabla_resumen(df_filtrado)

    # ── Tab 3: Gráfico mensual ────────────────────────────────────────────────
    with tab3:
        df_prog = obtener_programacion_df()
        crear_grafico_mensual(df_filtrado, cols_dev, df_prog)

    # ── Tab 4: Programación editable ──────────────────────────────────────────
    with tab4:
        genericas_ord = sorted(df_filtrado["generica"].unique().tolist())
        mostrar_formulario_programacion(genericas_ord)


if __name__ == "__main__":
    main()

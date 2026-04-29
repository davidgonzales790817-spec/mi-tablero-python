# ═══════════════════════════════════════════════════════════════════════════════
# src/app.py — PUNTO DE ENTRADA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
#
# PROPÓSITO:
#   Este es el archivo principal que ejecuta Streamlit.
#   Cuando haces: streamlit run src/app.py
#   Streamlit carga este archivo y ejecuta el código de arriba a abajo.
#
# FLUJO GENERAL:
#   1. Importar todas las dependencias
#   2. Configurar la página (ancho, tema, etc)
#   3. Inicializar session_state (cache en memoria)
#   4. Cargar y procesar archivo Excel (si está disponible)
#   5. Renderizar sidebar (logo, carga archivo, filtros)
#   6. Renderizar contenido principal (header, KPIs, 4 tabs)
#
# NOTA IMPORTANTE:
#   En Fase 0 NO hay autenticación. En Fase 1, al inicio se añade:
#   if not requerir_login():
#       return
#   El resto del código se deja igual, solo se agregan capas de autenticación.
#
# ═══════════════════════════════════════════════════════════════════════════════

# Importar las librerías que necesitamos
import pytz                                # Para manejo de zonas horarias
import pandas as pd                        # Para trabajar con tablas (DataFrames)
import streamlit as st                     # El framework web
from datetime import datetime              # Para fecha y hora

# Importar configuración centralizada
from config import PAGE_CONFIG, CSS_EXTRA

# Importar utilidades (helpers)
from utils.file_handler import widget_carga_archivo      # Widget de subir archivo
from utils.data_processor import DataProcessor           # Pipeline de procesamiento

# Importar componentes visuales (cada uno renderiza una parte de la UI)
from components.sidebar import mostrar_logo, crear_filtros
from components.gauges import mostrar_indicadores
from components.summary_table import crear_tabla_resumen
from components.monthly_chart import crear_grafico_mensual
from components.programacion_form import (
    inicializar_programacion,
    mostrar_formulario_programacion,
    mostrar_resumen_sidebar,
    obtener_programacion_df,
)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════════

# Aplicar la configuración definida en config.py
st.set_page_config(**PAGE_CONFIG)

# Inyectar CSS personalizado para mejorar el look and feel
st.markdown(CSS_EXTRA, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# INICIALIZACIÓN DEL ESTADO (SESSION_STATE)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Streamlit reexecuta todo el archivo cada vez que algo cambia.
# Para evitar recalcular DataFrames, se guardan en session_state (cache en RAM).
#
# EXPLICACIÓN:
# - session_state es un dict que persiste durante toda la sesión del usuario
# - Primera vez que entra: crea las claves con valores por defecto (None)
# - Siguientes recargas: usa lo que guardó sin recrear

def _init_state():
    """Inicializa las variables de session_state si no existen."""
    defaults = {
        "df_raw": None,           # DataFrame crudo del Excel (sin procesar)
        "df_procesado": None,     # DataFrame procesado y normalizado
        "cols_devengado": [],     # Lista de nombres de columnas de devengado
        "archivo_activo": None,   # Ruta al archivo Excel cargado
    }
    
    # Iterar sobre los defaults y crear en session_state si no existen
    for clave, valor_defecto in defaults.items():
        if clave not in st.session_state:
            st.session_state[clave] = valor_defecto


# Llamar a inicialización al inicio del script
_init_state()

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN: CARGAR Y PROCESAR EXCEL
# ═══════════════════════════════════════════════════════════════════════════════

def _cargar_y_procesar():
    """
    Procesa el DataFrame que ya está en session_state.
    
    PASOS:
        1. Obtener df_raw de session_state
        2. Crear DataProcessor y ejecutar pipeline
        3. Guardar resultados en session_state
    
    NOTA:
        En Streamlit Cloud, el archivo ya está en memoria (cargado por widget_carga_archivo).
        No necesitamos leerlo de disco.
    """
    # Paso 1: Obtener el DataFrame que ya cargó widget_carga_archivo()
    df_raw = st.session_state.get("df_raw")
    if df_raw is None:
        st.error("❌ No hay datos cargados.")
        return
    
    # Paso 2: Crear el procesador y ejecutar pipeline
    procesador = DataProcessor(df_raw)
    procesador.procesar_completo()  # Normalizar + detectar + calcular
    
    # Paso 3: Extraer resultados
    df_proc = procesador.obtener_dataframe()      # DataFrame procesado
    cols_dev = procesador.obtener_columnas_devengado()  # Nombres de columnas
    
    # Verificar si hay filas válidas después del procesamiento
    if df_proc.empty:
        st.warning("⚠️ El archivo no tiene datos válidos después del procesamiento.")
        return
    
    # Guardar en session_state para las próximas recargas
    st.session_state.df_procesado = df_proc
    st.session_state.cols_devengado = cols_dev


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN: PANTALLA DE BIENVENIDA (SIN DATOS)
# ═══════════════════════════════════════════════════════════════════════════════

def _pantalla_bienvenida():
    """Muestra un mensaje instructivo cuando no hay datos cargados."""
    st.markdown(
        """
        <div style="text-align:center; margin-top:100px;">
          <h1 style="color:#1e3a5f;">📊 Tablero Presupuestal SIAF</h1>
          <p style="color:#64748b; font-size:17px; margin-top:12px;">
            Carga un archivo Excel del SIAF desde la barra lateral para comenzar.<br>
            Formatos soportados: <code>.xls</code> y <code>.xlsx</code>
          </p>
          <p style="color:#94a3b8; font-size:13px; margin-top:24px;">
            Los archivos se procesan en memoria y estarán disponibles durante tu sesión.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN: HEADER DE LA PÁGINA
# ═══════════════════════════════════════════════════════════════════════════════

def _render_header(df_proc: pd.DataFrame):
    """
    Renderiza el encabezado con institución, año y fecha de actualización.
    
    PARÁMETROS:
        df_proc: DataFrame procesado (para extraer pliego y año)
    """
    # Obtener zona horaria de Lima y hora actual
    zona_lima = pytz.timezone("America/Lima")
    fecha_act = datetime.now(zona_lima).strftime("%d/%m/%Y %H:%M")
    
    # Extraer información del DataFrame (o valores por defecto)
    pliego = df_proc["pliego"].iloc[0] if "pliego" in df_proc.columns else "—"
    ano_eje = df_proc["ano_eje"].iloc[0] if "ano_eje" in df_proc.columns else "—"
    
    # Layout en dos columnas: título a izq, fecha a derecha
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
    
    # Línea separadora
    st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN: KPIs (MÉTRICAS PRINCIPALES)
# ═══════════════════════════════════════════════════════════════════════════════

def _render_kpis(df: pd.DataFrame):
    """
    Renderiza 5 cajas de métrica con números principales.
    
    MÉTRICAS:
        1. PIM (presupuesto inicial modificado)
        2. Certificado (presupuesto certificado + % del PIM)
        3. Compromiso (presupuesto comprometido + % del PIM)
        4. Devengado (presupuesto ejecutado + % del PIM)
        5. Saldo (dinero sin gastar + % sin ejecutar)
    
    PARÁMETROS:
        df: DataFrame filtrado (después de aplicar filtros)
    
    RETORNA:
        tuple: (pim, certificado, compromiso, devengado)
        Se usa para pasar a los gráficos y gauges
    """
    # Función auxiliar para formatear números con separador de miles
    # Convierte 1000000 → "S/ 1.000.000" (formato peruano)
    fmt = lambda v: f"S/ {round(v):,}".replace(",", ".")
    
    # Sumar columnas del DataFrame
    pim = df["PIM"].sum()                        # Presupuesto inicial
    cert = df["Certificado"].sum()               # Certificado
    comp = df["Compromiso_Anual"].sum()          # Compromiso
    dev = df["Devengado_Total"].sum()            # Devengado
    saldo = pim - dev                            # Lo que queda
    
    # Función auxiliar para porcentaje del PIM
    pct = lambda v: f"{v / pim * 100:.1f}% del PIM" if pim else "—"
    
    # Crear 5 columnas para mostrar las métricas
    k1, k2, k3, k4, k5 = st.columns(5)
    
    k1.metric("PIM", fmt(pim))
    k2.metric("Certificado", fmt(cert), pct(cert))
    k3.metric("Compromiso", fmt(comp), pct(comp))
    k4.metric("Devengado", fmt(dev), pct(dev))
    k5.metric("Saldo Pendiente", fmt(saldo), f"{saldo / pim * 100:.1f}% sin ejecutar" if pim else "—")
    
    return pim, cert, comp, dev


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL: main()
# ═══════════════════════════════════════════════════════════════════════════════
#
# Esta es la función que Streamlit ejecuta.
# Todo lo importante pasa aquí.

def main():
    """Función principal que renderiza toda la app."""
    
    # --- PASO 1: SIDEBAR ---
    # Mostrar logo en el sidebar
    mostrar_logo()
    
    # Widget de carga de archivo (devuelve ruta si hay archivo activo)
    archivo_activo = widget_carga_archivo()
    
    # --- PASO 2: PROCESAR ARCHIVO SI CAMBIÓ ---
    # Si hay archivo pero no está procesado aún, procesarlo
    if st.session_state.df_raw is not None and st.session_state.df_procesado is None:
        _cargar_y_procesar()
    
    # --- PASO 3: PANTALLA DE BIENVENIDA (SI SIN DATOS) ---
    # Si no hay datos, mostrar mensaje instructivo
    if st.session_state.df_procesado is None:
        _pantalla_bienvenida()
        return  # Salir sin mostrar el resto
    
    # --- PASO 4: EXTRAER DATOS DE SESSION_STATE ---
    # Si llegamos aquí, hay datos procesados
    df_proc = st.session_state.df_procesado
    cols_dev = st.session_state.cols_devengado
    
    # --- PASO 5: SIDEBAR - FILTROS ---
    st.sidebar.markdown("---")
    df_filtrado = crear_filtros(df_proc)  # Aplica filtros y devuelve DF filtrado
    
    # --- PASO 6: INICIALIZAR PROGRAMACIÓN ---
    # Necesario antes de los tabs para que Tab3 tenga datos
    genericas_ord = sorted(df_filtrado["generica"].unique().tolist())
    inicializar_programacion(genericas_ord)
    mostrar_resumen_sidebar()
    
    # --- VERIFICACIÓN: HAY DATOS CON FILTROS APLICADOS? ---
    if df_filtrado.empty:
        st.warning("⚠️ Sin datos para los filtros actuales.")
        return
    
    # --- PASO 7: HEADER Y KPIs ---
    _render_header(df_proc)
    pim, cert, comp, dev = _render_kpis(df_filtrado)
    
    # --- PASO 8: TABS PRINCIPALES ---
    # Crear 4 tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Indicadores",
        "📊 Por Genérica",
        "📆 Evolución Mensual",
        "📅 Programación",
    ])
    
    # TAB 1: Gauges (indicadores visuales)
    with tab1:
        mostrar_indicadores(pim, cert, comp, dev)
    
    # TAB 2: Tabla de resumen por genérica
    with tab2:
        crear_tabla_resumen(df_filtrado)
    
    # TAB 3: Gráfico mensual
    with tab3:
        crear_grafico_mensual(df_filtrado, cols_dev, obtener_programacion_df())
    
    # TAB 4: Formulario de programación editable
    with tab4:
        mostrar_formulario_programacion(genericas_ord)


# ═══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════
# Cuando ejecutas: streamlit run src/app.py
# Python ejecuta el código de arriba a abajo, y al final llama a main()

if __name__ == "__main__":
    main()

# ═══════════════════════════════════════════════════════════════════════════════
# FIN DE APP.PY
# ═══════════════════════════════════════════════════════════════════════════════

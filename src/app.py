# =============================================================================
#  TABLERO DE EJECUCIÓN PRESUPUESTAL — IPEN 2026
#  Desarrollado con Streamlit + Plotly + Pandas
#  Marco normativo: Ley N° 32513 (Presupuesto 2026) y D.L. 1440
# =============================================================================
#
#  ¿QUÉ ES ESTE ARCHIVO?
#  Este es el archivo principal de la aplicación. Cuando lo ejecutas con el
#  comando "streamlit run app.py", Streamlit lo interpreta de arriba a abajo
#  y construye la página web automáticamente.
#
#  ¿QUÉ SON LOS "import"?
#  Son instrucciones para cargar bibliotecas (paquetes de código ya escritos
#  por otras personas que usamos gratuitamente). Cada una cumple una función:
# =============================================================================

import streamlit as st          # La biblioteca que convierte este script en una app web
import pandas as pd             # Para manejar tablas de datos (como Excel pero en Python)
import plotly.graph_objects as go   # Para crear gráficos interactivos (barras, líneas, etc.)
import plotly.express as px         # Versión simplificada de Plotly para gráficos rápidos
import json                     # Para leer y escribir archivos de texto en formato JSON
import os                       # Para verificar si un archivo existe en el disco
from datetime import datetime   # Para obtener la fecha y hora actuales


# =============================================================================
#  CONFIGURACIÓN INICIAL DE LA PÁGINA
#  st.set_page_config() debe ser la PRIMERA instrucción de Streamlit.
#  Define cómo se ve la ventana del navegador.
# =============================================================================
st.set_page_config(
    page_title="Tablero Presupuestal IPEN 2026",  # Título en la pestaña del navegador
    page_icon="📊",                                # Ícono en la pestaña del navegador
    layout="wide",                                 # Usa todo el ancho de la pantalla
    initial_sidebar_state="expanded"              # El menú lateral aparece abierto al inicio
)


# =============================================================================
#  ESTILOS CSS PERSONALIZADOS
#  CSS es el lenguaje que controla colores, tamaños y formas en páginas web.
#  st.markdown(..., unsafe_allow_html=True) permite insertar código HTML/CSS
#  directamente en la app para personalizar su apariencia.
# =============================================================================
st.markdown("""
<style>
/* Hace los números de las métricas más grandes */
[data-testid="stMetricValue"] { font-size: 1.6rem !important; }
/* Hace las etiquetas de las métricas más pequeñas y grises */
[data-testid="stMetricLabel"] { font-size: 0.78rem !important; color: #666 !important; }
/* Ajusta el tamaño de los indicadores de cambio (flechas arriba/abajo) */
[data-testid="stMetricDelta"] { font-size: 0.78rem !important; }
/* Da un fondo gris suave a las tarjetas de métricas */
div[data-testid="metric-container"] {
    background: #f8f9fa; border-radius: 10px;
    padding: 14px 18px; border: 0.5px solid #e0e0e0;
}
/* Títulos de sección (letras pequeñas en mayúsculas) */
.section-title {
    font-size: 0.72rem; font-weight: 600; letter-spacing: .07em;
    text-transform: uppercase; color: #888; margin: 1.4rem 0 0.6rem;
}
/* Badges para semáforos: verde=OK, amarillo=Alerta, rojo=Crítico */
.badge-ok    { background:#d4edda; color:#155724; padding:2px 9px; border-radius:20px; font-size:11px; font-weight:600; }
.badge-warn  { background:#fff3cd; color:#856404; padding:2px 9px; border-radius:20px; font-size:11px; font-weight:600; }
.badge-alert { background:#f8d7da; color:#721c24; padding:2px 9px; border-radius:20px; font-size:11px; font-weight:600; }
.badge-gray  { background:#e2e3e5; color:#383d41; padding:2px 9px; border-radius:20px; font-size:11px; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
#  CONSTANTES Y DATOS FIJOS
#  Las constantes son valores que no cambian. Se escriben en MAYÚSCULAS
#  por convención para distinguirlas de las variables normales.
# =============================================================================

# Lista de nombres de meses (los usaremos en gráficos y tablas)
MESES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]

# Nombre del archivo donde se guarda la programación mensual del usuario.
# JSON es un formato de texto simple, como un diccionario guardado en disco.
PROG_FILE = "programacion.json"

# Información de partidas con restricciones legales (Ley 32513 y D.L. 1440).
# Es una lista de diccionarios: cada diccionario describe una partida restringida.
RESTRICCIONES = [
    {
        "codigo": "L-02", "partida": "2.3.2.1",
        "nombre": "Energía / agua / gas",
        "norma": "Ley 32513 Art. 9",
        "detalle": "Prohibido usar esta partida como fuente para habilitar otras, salvo dentro de la misma UE o entre UE del mismo pliego.",
        "nivel": "warn"   # warn = amarillo (alerta moderada)
    },
    {
        "codigo": "L-03", "partida": "2.3.2.2",
        "nombre": "Telefonía e internet",
        "norma": "Ley 32513 Art. 9",
        "detalle": "Misma restricción que 2.3.2.1. Tope S/ 120/línea/mes para telefonía móvil.",
        "nivel": "warn"
    },
    {
        "codigo": "L-04", "partida": "2.1.1.1.3",
        "nombre": "CAS (Contrato Administrativo de Servicios)",
        "norma": "Ley 32513 Art. 8",
        "detalle": "No puede ser habilitada salvo entre UE del mismo pliego. Cualquier modificación positiva requiere justificación.",
        "nivel": "alert"  # alert = rojo (crítico)
    },
    {
        "codigo": "L-05", "partida": "2.6.3",
        "nombre": "Adquisición de vehículos",
        "norma": "Ley 32513 (medidas de austeridad)",
        "detalle": "Solo para renovación de unidades con más de 10 años. Requiere resolución expresa del Titular del Pliego.",
        "nivel": "alert"
    },
    {
        "codigo": "L-06", "partida": "Genérica 1",
        "nombre": "Personal y obligaciones sociales (planilla)",
        "norma": "D.L. 1440 Art. 6 y 48",
        "detalle": "Plazas y remuneraciones requieren CAP/PAP aprobado. Incrementos requieren norma con rango de ley.",
        "nivel": "ok"     # ok = verde (bajo control)
    },
    {
        "codigo": "L-07", "partida": "Modificaciones",
        "nombre": "Modificaciones en partidas restringidas",
        "norma": "D.L. 1440 Art. 47-48",
        "detalle": "Modificaciones en partidas restringidas requieren resolución del Titular y opinión favorable de Presupuesto.",
        "nivel": "warn"
    },
]

# Palabras clave para buscar cada partida restringida en el Excel.
# Para L-06 y L-07 se usa otra lógica (filtro por genérica o por modificaciones).
KEYWORDS_RESTRICCION = {
    "L-02": ["ENERGIA ELECTRICA", "AGUA Y DESAGUE", "GAS"],
    "L-03": ["TELEFON", "INTERNET", "CELULAR"],
    "L-04": ["CONTRATO ADMINISTRATIVO DE SERVICIOS", " CAS "],
    "L-05": ["VEHICULO"],
    "L-06": [],
    "L-07": [],
}

# Avance sectorial del Sector 16-Energía y Minas por mes (estimaciones históricas).
# El usuario puede sobreescribir estos valores con datos reales de Consulta Amigable MEF.
BENCHMARK_SECTOR = {
    "Ene": 5.5,  "Feb": 10.2, "Mar": 15.8, "Abr": 21.3,
    "May": 27.1, "Jun": 33.0, "Jul": 39.4, "Ago": 46.2,
    "Sep": 53.5, "Oct": 61.8, "Nov": 72.4, "Dic": 88.6
}


# =============================================================================
#  FUNCIONES AUXILIARES
#  Una función es un bloque de código reutilizable. Se define con "def nombre():"
#  El decorador @st.cache_data guarda el resultado en memoria para no recalcular
#  cada vez que el usuario interactúa con la app.
# =============================================================================

@st.cache_data(show_spinner=False)
def cargar_datos(archivo_subido):
    """
    Lee el archivo Excel del SIAF y prepara la tabla de datos (DataFrame).

    Pasos:
    1. Lee la hoja 'SheetGasto' del Excel
    2. Crea columnas de totales sumando los 12 meses de cada concepto
    3. Devuelve la tabla y las listas de nombres de columnas mensuales

    @st.cache_data significa: si el mismo archivo ya fue procesado antes,
    devuelve el resultado guardado sin volver a leer el Excel (mucho más rápido).
    """
    # Leer el Excel. header=0 = la primera fila tiene los nombres de columnas.
    df = pd.read_excel(archivo_subido, sheet_name="SheetGasto", header=0)

    # Construir listas con los nombres de las 12 columnas mensuales de cada concepto.
    # f"mto_devenga_{i:02d}" genera: "mto_devenga_01", "mto_devenga_02", ..., "mto_devenga_12"
    # El ":02d" formatea el número con 2 dígitos (01 en lugar de 1)
    dev_cols  = [f"mto_devenga_{i:02d}" for i in range(1, 13)]
    gir_cols  = [f"mto_girado_{i:02d}"  for i in range(1, 13)]
    pag_cols  = [f"mto_pagado_{i:02d}"  for i in range(1, 13)]
    comp_cols = [f"mto_at_comp_{i:02d}" for i in range(1, 13)]

    # Si alguna columna no existe en el Excel, crearla con valor 0.
    # Esto evita errores cuando el reporte no tiene datos de todos los meses.
    for c in dev_cols + gir_cols + pag_cols + comp_cols:
        if c not in df.columns:
            df[c] = 0.0

    # Convertir las columnas numéricas a formato número (por si quedaron como texto).
    # errors="coerce" convierte los valores no numéricos a NaN (nulo).
    # fillna(0) reemplaza los nulos con 0.
    cols_numericas = (dev_cols + gir_cols + pag_cols + comp_cols +
                      ["mto_pia","mto_pim","mto_certificado","mto_compro_anual",
                       "mto_modificaciones","cant_meta_anual","avan_fisico_anual"])
    for c in cols_numericas:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Crear columnas de totales anuales sumando los 12 meses horizontalmente.
    # .sum(axis=1) suma a lo largo del eje de columnas (fila por fila)
    df["dev_total"]  = df[dev_cols].sum(axis=1)
    df["gir_total"]  = df[gir_cols].sum(axis=1)
    df["pag_total"]  = df[pag_cols].sum(axis=1)
    df["comp_total"] = df[comp_cols].sum(axis=1)

    return df, dev_cols, gir_cols, pag_cols, comp_cols


def fmt(valor):
    """
    Formatea un número como soles peruanos con separadores de miles.
    Ejemplo: fmt(1234567) → "S/ 1,234,567"
    El formato {:,.0f} agrega comas como separadores y no muestra decimales.
    """
    return f"S/ {valor:,.0f}"


def pct(numerador, denominador):
    """
    Calcula un porcentaje evitando la división entre cero.
    Si el denominador es 0 (o None), devuelve 0.0 en lugar de causar un error.
    round(..., 1) redondea a 1 decimal.
    """
    return round(numerador / denominador * 100, 1) if denominador else 0.0


def badge_html(valor_pct, ok_thr=85, umbral_warn=60):
    """
    Genera una etiqueta HTML de color (semáforo) según el valor.
    - Verde (badge-ok):    valor >= ok_thr
    - Amarillo (badge-warn): valor >= umbral_warn
    - Rojo (badge-alert):  valor < umbral_warn
    Se usa con st.markdown(..., unsafe_allow_html=True) para mostrarla.
    """
    if valor_pct >= ok_thr:
        clase = "badge-ok"
    elif valor_pct >= umbral_warn:
        clase = "badge-warn"
    else:
        clase = "badge-alert"
    return f'<span class="{clase}">{valor_pct:.1f}%</span>'


def cargar_programacion():
    """
    Lee el archivo JSON con la programación mensual guardada.
    Si el archivo no existe (primera vez), devuelve un diccionario vacío {}.
    json.load() convierte el texto JSON a un diccionario de Python.
    """
    if os.path.exists(PROG_FILE):
        with open(PROG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardar_programacion(datos):
    """
    Guarda el diccionario de programación en el archivo JSON.
    json.dump() convierte el diccionario a texto JSON y lo escribe en el archivo.
    indent=2 hace el archivo legible (con sangría de 2 espacios).
    ensure_ascii=False permite guardar tildes y caracteres especiales.
    """
    with open(PROG_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)


def detectar_mes_corte(dev_mensual):
    """
    Detecta hasta qué mes hay datos de devengado en el Excel.
    Recorre los meses de diciembre (11) hacia enero (0) buscando el primero con valor > 0.
    Retorna el número del mes (1=enero, ..., 12=diciembre).
    """
    for i in range(11, -1, -1):   # range(11, -1, -1) = [11, 10, 9, ..., 1, 0]
        if dev_mensual[i] > 0:
            return i + 1          # +1 porque los índices van de 0 a 11, los meses de 1 a 12
    return 1


# =============================================================================
#  BARRA LATERAL (SIDEBAR)
#  Todo lo que está dentro de "with st.sidebar:" aparece en el panel izquierdo.
# =============================================================================
with st.sidebar:
    # Intentar cargar el logo del IPEN desde Wikipedia
    try:
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/IPEN_Logo.svg/200px-IPEN_Logo.svg.png",
            width=110
        )
    except Exception:
        pass  # Si falla (sin internet), continúa sin mostrar imagen

    st.markdown("### Tablero presupuestal")
    st.caption("Pliego 220 · Sector 16 · Ley 32513 · D.L. 1440")
    st.divider()   # Línea horizontal separadora

    # Widget para cargar el archivo Excel. El usuario lo arrastra o lo busca.
    # type=["xls","xlsx"] acepta solo archivos Excel.
    # La variable será None si no se ha cargado nada, o tendrá el archivo si se cargó.
    archivo_subido = st.file_uploader(
        "📂 Cargar reporte SIAF (.xls / .xlsx)",
        type=["xls", "xlsx"],
        help="Hoja SheetGasto en formato estándar del SIAF-MEF"
    )

    st.divider()

    # Menú de navegación. Solo se puede seleccionar una opción a la vez.
    # La variable "pagina" guarda cuál eligió el usuario.
    pagina = st.radio(
        "Módulo",
        options=[
            "🏠 Resumen ejecutivo",
            "📊 Ejecución por genérica",
            "📅 Estacionalidad y proyección",
            "🎯 Programación mensual",
            "🏁 Metas físicas",
            "📡 Benchmark sectorial",
            "⚖️ Restricciones normativas",
            "🔍 Explorador de partidas",
        ],
        label_visibility="collapsed"
    )

    st.divider()
    # Mostrar fecha y hora de la última carga
    st.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")


# =============================================================================
#  PANTALLA DE BIENVENIDA
#  Si no hay archivo cargado, mostrar bienvenida y detener la ejecución.
#  st.stop() hace que Python no ejecute nada más después de esta línea.
# =============================================================================
if archivo_subido is None:
    st.markdown("## 👋 Bienvenido al tablero de ejecución presupuestal")
    st.markdown("**Pliego 220 — Instituto Peruano de Energía Nuclear (IPEN)**")
    st.info("📂 Cargue el reporte SIAF desde el panel izquierdo para comenzar.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Indicadores disponibles", "54", "11 categorías")
    c2.metric("Módulos de análisis", "8", "incluye benchmark y metas físicas")
    c3.metric("Marco normativo", "Ley 32513", "+ D.L. 1440")

    st.markdown("""
    **Módulos disponibles:**
    - 🏠 Resumen ejecutivo — KPIs principales y ciclo de gasto
    - 📊 Ejecución por genérica — análisis por clasificador económico
    - 📅 Estacionalidad y proyección — curva-S y proyección de cierre
    - 🎯 Programación mensual — registro y seguimiento vs. real SIAF
    - 🏁 Metas físicas — seguimiento físico-financiero por meta (M-01 a M-05)
    - 📡 Benchmark sectorial — IPEN vs. Sector 16-Energía y Minas (C-04)
    - ⚖️ Restricciones normativas — partidas Ley 32513 y D.L. 1440
    - 🔍 Explorador de partidas — cruce dinámico por cualquier dimensión
    """)
    st.stop()   # Detener aquí: lo que sigue solo se ejecuta si hay archivo cargado


# =============================================================================
#  CARGA Y PROCESAMIENTO DE DATOS
#  A partir de aquí sabemos que el usuario sí subió un archivo.
# =============================================================================

with st.spinner("Procesando data SIAF..."):
    df, dev_cols, gir_cols, pag_cols, comp_cols = cargar_datos(archivo_subido)

# Calcular totales globales sumando toda la columna (.sum() suma verticalmente)
PIM   = df["mto_pim"].sum()
PIA   = df["mto_pia"].sum()
CERT  = df["mto_certificado"].sum()
COMP  = df["mto_compro_anual"].sum()
DEV   = df["dev_total"].sum()
GIR   = df["gir_total"].sum()
PAG   = df["pag_total"].sum()
MODIF = df["mto_modificaciones"].sum()

# Lista con el total de devengado de cada mes (suma de todos los registros)
dev_mensual = [df[c].sum() for c in dev_cols]

# Detectar el mes de corte de la data
mes_corte = detectar_mes_corte(dev_mensual)

# Calcular indicadores derivados
avance_pct = pct(DEV, PIM)                      # E-01: avance devengado %
ideal_pct  = round(mes_corte / 12 * 100, 1)     # Avance ideal lineal al mes de corte
desfase    = round(avance_pct - ideal_pct, 1)    # T-05: desfase vs. ideal
efic_pago  = pct(PAG, DEV)                       # E-05: eficacia de pago
efic_giro  = pct(GIR, DEV)                       # Te-01: eficacia de giro
efic_cert  = pct(CERT, PIM)                      # E-03: avance certificación
efic_comp  = pct(COMP, PIM)                      # E-02: avance compromiso
meses_rest = 12 - mes_corte
ritmo_req  = (PIM - DEV) / meses_rest if meses_rest > 0 else 0  # T-03: ritmo requerido/mes


# =============================================================================
#  MÓDULO 1 — RESUMEN EJECUTIVO
# =============================================================================
if pagina == "🏠 Resumen ejecutivo":

    st.markdown("## Resumen ejecutivo — Ejecución presupuestal")
    st.caption(f"Corte: mes {mes_corte} ({MESES[mes_corte-1]}) 2026 · PIM vigente: {fmt(PIM)}")

    # --- Fila 1: Indicadores de eficacia ---
    st.markdown('<div class="section-title">Indicadores de eficacia financiera (E-01 a E-07)</div>',
                unsafe_allow_html=True)

    # st.columns(5) divide el espacio en 5 columnas iguales
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("E-01 · Avance devengado",     f"{avance_pct}%",   f"{desfase:+.1f} pp vs ideal {ideal_pct}%")
    k2.metric("E-02 · Avance compromiso",    f"{efic_comp}%",    fmt(COMP))
    k3.metric("E-03 · Avance certificación", f"{efic_cert}%",    fmt(CERT))
    k4.metric("E-05 · Eficacia de pago",     f"{efic_pago}%",    "Meta ≥ 95%")
    k5.metric("Te-01 · Eficacia de giro",    f"{efic_giro}%",    "Meta ≥ 98%")

    # --- Fila 2: Saldos y proyección ---
    k6, k7, k8, k9, k10 = st.columns(5)
    k6.metric("PIA inicial",            fmt(PIA),      "")
    k7.metric("Modificaciones",         fmt(MODIF),    f"{pct(MODIF, PIA):+.2f}% sobre PIA")
    k8.metric("PIM vigente",            fmt(PIM),      "")
    k9.metric("Saldo por ejecutar",     fmt(PIM-DEV),  f"{100-avance_pct:.1f}% del PIM")
    k10.metric("T-03 · Ritmo req./mes", fmt(ritmo_req),f"{meses_rest} meses restantes")

    st.divider()

    # --- Ciclo de fases + Semáforo ---
    col_fases, col_sem = st.columns([1.2, 1])

    with col_fases:
        st.markdown("#### Ciclo de gasto — etapas presupuestales")
        # Lista de fases: (nombre, monto, color)
        fases = [
            ("PIM",          PIM,  "#bdbdbd"),
            ("Certificado",  CERT, "#4caf50"),
            ("Comprometido", COMP, "#2196f3"),
            ("Devengado",    DEV,  "#1565c0"),
            ("Girado",       GIR,  "#0d47a1"),
            ("Pagado",       PAG,  "#01579b"),
        ]
        fig_fases = go.Figure()
        for nombre, valor, color in fases:
            p = pct(valor, PIM)
            # Barra horizontal: orientation="h" hace las barras de izquierda a derecha
            fig_fases.add_trace(go.Bar(
                x=[p], y=[nombre], orientation="h",
                marker_color=color,
                text=f"{p:.1f}%  ({fmt(valor)})",
                textposition="inside" if p > 15 else "outside",
                textfont=dict(size=11),
                hovertemplate=f"<b>{nombre}</b><br>{fmt(valor)}<br>{p:.1f}% del PIM<extra></extra>",
                showlegend=False
            ))
        fig_fases.update_layout(
            height=280, margin=dict(l=0, r=10, t=10, b=10),
            xaxis=dict(range=[0, 115], showgrid=True, gridcolor="#eee", ticksuffix="%"),
            yaxis=dict(autorange="reversed"),  # PIM queda arriba
            plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
            barmode="overlay"
        )
        st.plotly_chart(fig_fases, use_container_width=True)

    with col_sem:
        st.markdown("#### Semáforo de indicadores clave")
        dev_capital = df[df["categoria_gasto"].str.startswith("6", na=False)]["dev_total"].sum()
        pim_gen_12  = df[df["generica"].str.startswith(("1.","2."), na=False)]["mto_pim"].sum()

        # Lista: (nombre, valor, umbral_verde, umbral_amarillo)
        indicadores_sem = [
            ("E-01 · Avance devengado",       avance_pct,                  85, 70),
            ("E-03 · Certificación / PIM",    efic_cert,                   50, 30),
            ("E-02 · Compromiso / PIM",       efic_comp,                   40, 25),
            ("E-05 · Pago / devengado",       efic_pago,                   95, 85),
            ("Te-01 · Giro / devengado",      efic_giro,                   97, 90),
            ("G-06 · Capital ejecut. / PIM",  pct(dev_capital, PIM),       10,  5),
            ("G-04 · Rigidez planilla/PIM",   pct(pim_gen_12, PIM),        70, 80),
        ]
        for nombre, val, ok_t, warn_t in indicadores_sem:
            icono = "🟢" if val >= ok_t else ("🟡" if val >= warn_t else "🔴")
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"{icono} {nombre}")
            c2.markdown(f"**{val:.1f}%**")
        st.markdown("---")
        st.caption("🟢 Cumple   🟡 Alerta   🔴 Crítico")

    st.divider()

    # --- Distribución por fuente de financiamiento ---
    st.markdown("#### Distribución PIM y ejecución por fuente (F-01, F-02)")
    # groupby agrupa filas y .agg() calcula sumas para cada grupo
    fuente_df = df.groupby("fuente_financ").agg(
        pim=("mto_pim","sum"), dev=("dev_total","sum")).reset_index()
    fuente_df["avance_pct"] = fuente_df.apply(lambda r: pct(r["dev"], r["pim"]), axis=1)
    fuente_df["share_pim"]  = fuente_df.apply(lambda r: pct(r["pim"], PIM),     axis=1)

    for _, fila in fuente_df.iterrows():
        fa, fb, fc, fd = st.columns([3, 1.5, 1.5, 1.5])
        fa.markdown(f"**{fila['fuente_financ'][:50]}**")
        fb.markdown(f"PIM: {fmt(fila['pim'])}")
        fc.markdown(f"Dev: {fmt(fila['dev'])}")
        fd.markdown(badge_html(fila['avance_pct'], ok_thr=85, umbral_warn=50) +
                    f" &nbsp; ({fila['share_pim']:.1f}% del total)", unsafe_allow_html=True)


# =============================================================================
#  MÓDULO 2 — EJECUCIÓN POR GENÉRICA
# =============================================================================
elif pagina == "📊 Ejecución por genérica":

    st.markdown("## Ejecución por genérica de gasto")
    st.caption("Indicadores G-03, G-04, G-05, G-06")

    # Agrupar por genérica y calcular sumas financieras
    gen_df = df.groupby("generica").agg(
        pim=("mto_pim","sum"), cert=("mto_certificado","sum"),
        comp=("mto_compro_anual","sum"), dev=("dev_total","sum"),
        gir=("gir_total","sum"), pag=("pag_total","sum")
    ).reset_index()
    gen_df["avance_pct"] = gen_df.apply(lambda r: pct(r["dev"], r["pim"]), axis=1)
    gen_df["share_pim"]  = gen_df.apply(lambda r: pct(r["pim"], PIM),     axis=1)

    # Gráfico de barras agrupadas (PIM, Certificado, Comprometido, Devengado)
    fig_gen = go.Figure()
    for nombre_col, col_key, color in [
        ("PIM","pim","#bdbdbd"), ("Certificado","cert","#4caf50"),
        ("Comprometido","comp","#2196f3"), ("Devengado","dev","#1565c0")
    ]:
        fig_gen.add_trace(go.Bar(
            name=nombre_col,
            x=gen_df["generica"].str[:35],
            y=gen_df[col_key] / 1_000_000,   # Dividir entre 1 millón = mostrar en M
            marker_color=color,
            hovertemplate="%{x}<br>" + nombre_col + ": S/ %{y:.2f}M<extra></extra>"
        ))
    fig_gen.update_layout(
        height=400, barmode="group", yaxis_title="Millones de S/",
        xaxis_tickangle=-30, legend=dict(orientation="h", yanchor="bottom", y=1.02),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=50, b=10)
    )
    st.plotly_chart(fig_gen, use_container_width=True)

    # Tabla detalle por genérica con badges de semáforo
    st.markdown("#### Detalle por genérica")
    for _, fila in gen_df.iterrows():
        c1, c2, c3, c4, c5, c6 = st.columns([3, 1.3, 1.3, 1.3, 1, 1])
        c1.markdown(f"**{fila['generica'][:45]}**")
        c2.markdown(f"PIM: {fmt(fila['pim'])}")
        c3.markdown(f"Dev: {fmt(fila['dev'])}")
        c4.markdown(f"Pago: {fmt(fila['pag'])}")
        c5.markdown(f"Share: **{fila['share_pim']:.1f}%**")
        c6.markdown(badge_html(fila['avance_pct'], ok_thr=85, umbral_warn=50), unsafe_allow_html=True)

    st.divider()

    # Torta corriente vs. capital (G-03)
    st.markdown("#### G-03 · Gasto corriente vs. capital")
    cat_df = df.groupby("categoria_gasto").agg(
        pim=("mto_pim","sum"), dev=("dev_total","sum")).reset_index()
    cat_df["avance"] = cat_df.apply(lambda r: pct(r["dev"], r["pim"]), axis=1)

    col_pie, col_det = st.columns([1, 1.4])
    with col_pie:
        # Gráfico de dona (pie con agujero en el centro: hole=0.5)
        fig_cat = px.pie(cat_df, values="pim", names="categoria_gasto",
                         color_discrete_sequence=["#2196f3","#e53935","#43a047"], hole=0.5)
        fig_cat.update_traces(textinfo="label+percent",
                              hovertemplate="%{label}<br>PIM: S/ %{value:,.0f}<extra></extra>")
        fig_cat.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=10),
                              showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_det:
        for _, fila in cat_df.iterrows():
            st.markdown(
                f"**{fila['categoria_gasto'][:35]}**  \n"
                f"PIM: {fmt(fila['pim'])} | Dev: {fmt(fila['dev'])} | "
                f"Avance: {badge_html(fila['avance'], ok_thr=85, umbral_warn=50)}",
                unsafe_allow_html=True
            )
            st.markdown("")

    st.divider()

    # Detalle por subgenérica con selector interactivo
    st.markdown("#### Detalle por subgenérica (selector interactivo)")
    gen_elegida = st.selectbox("Seleccionar genérica:", sorted(df["generica"].dropna().unique()))
    sub_df = df[df["generica"] == gen_elegida].groupby("subgenerica_det").agg(
        pim=("mto_pim","sum"), dev=("dev_total","sum"), cert=("mto_certificado","sum")
    ).reset_index()
    sub_df["avance"] = sub_df.apply(lambda r: pct(r["dev"], r["pim"]), axis=1)
    sub_df = sub_df.sort_values("pim", ascending=False)

    # style.background_gradient aplica colores según valor (rojo=bajo, verde=alto)
    st.dataframe(
        sub_df.rename(columns={"subgenerica_det":"Subgenérica","pim":"PIM",
                                "cert":"Certificado","dev":"Devengado","avance":"Avance %"})
        .style.background_gradient(subset=["Avance %"], cmap="RdYlGn", vmin=0, vmax=100)
        .format({"PIM":"S/ {:,.0f}","Certificado":"S/ {:,.0f}",
                 "Devengado":"S/ {:,.0f}","Avance %":"{:.1f}%"}),
        use_container_width=True, hide_index=True
    )


# =============================================================================
#  MÓDULO 3 — ESTACIONALIDAD Y PROYECCIÓN
# =============================================================================
elif pagina == "📅 Estacionalidad y proyección":

    st.markdown("## Estacionalidad y proyección de cierre")
    st.caption("Indicadores T-01, T-02, T-03, T-04, T-05")

    # Calcular devengado acumulado mes a mes
    # Empezamos en 0 y sumamos cada mes al acumulado anterior
    dev_acum, acumulado = [], 0
    for v in dev_mensual:
        acumulado += v
        dev_acum.append(acumulado)

    # Trayectoria ideal: gastar exactamente 1/12 del PIM cada mes
    ideal_acum = [PIM * (i+1) / 12 for i in range(12)]

    # Proyección de cierre: si se mantiene el ritmo actual
    proyeccion = (DEV / mes_corte * 12) if mes_corte > 0 else 0

    # Curva-S
    st.markdown("#### Curva-S de ejecución acumulada")
    fig_curva = go.Figure()

    fig_curva.add_trace(go.Scatter(   # Línea ideal (punteada gris)
        x=MESES, y=[v/1e6 for v in ideal_acum], mode="lines", name="Ideal lineal",
        line=dict(dash="dot", color="#bdbdbd", width=2),
        hovertemplate="Ideal %{x}: S/ %{y:.2f}M<extra></extra>"
    ))
    fig_curva.add_trace(go.Scatter(   # Línea real (azul sólida)
        x=MESES, y=[v/1e6 for v in dev_acum], mode="lines+markers", name="Devengado real",
        line=dict(color="#1565c0", width=2.5), marker=dict(size=7),
        hovertemplate="Real %{x}: S/ %{y:.2f}M<extra></extra>"
    ))

    # Proyección desde el mes de corte hasta diciembre (línea naranja punteada)
    x_proy = MESES[mes_corte-1:]
    base   = dev_acum[mes_corte-1]
    paso   = (proyeccion - base) / (len(x_proy)-1) if len(x_proy) > 1 else 0
    y_proy = [(base + paso*i)/1e6 for i in range(len(x_proy))]
    fig_curva.add_trace(go.Scatter(
        x=x_proy, y=y_proy, mode="lines", name="Proyección (ritmo actual)",
        line=dict(dash="dash", color="#ef6c00", width=2),
        hovertemplate="Proyección %{x}: S/ %{y:.2f}M<extra></extra>"
    ))

    # Línea horizontal roja = el PIM total (la meta)
    fig_curva.add_hline(y=PIM/1e6, line_dash="dot", line_color="#e53935",
                        annotation_text=f"PIM: S/ {PIM/1e6:.1f}M")
    fig_curva.update_layout(
        height=400, yaxis_title="Millones de S/ (acumulado)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=50, b=10), hovermode="x unified"
    )
    st.plotly_chart(fig_curva, use_container_width=True)

    # Métricas de proyección
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    col_p1.metric("T-04 · Proyección cierre",   fmt(proyeccion),    f"{pct(proyeccion,PIM):.1f}% del PIM")
    col_p2.metric("T-03 · Ritmo req./mes",       fmt(ritmo_req),     f"{meses_rest} meses restantes")
    col_p3.metric("T-05 · Desfase vs ideal",     f"{desfase:+.1f} pp", f"Ideal mes {mes_corte}: {ideal_pct}%")
    col_p4.metric("R-04 · Saldo no comprometido",fmt(PIM-COMP),      f"{100-efic_comp:.1f}% del PIM")

    st.divider()

    # Barras mensuales de devengado (T-01 Estacionalidad)
    st.markdown("#### T-01 · Devengado mensual — estacionalidad")
    colores_m = ["#1565c0" if i < mes_corte else "#e3f2fd" for i in range(12)]
    fig_m = go.Figure(go.Bar(
        x=MESES, y=[v/1e6 for v in dev_mensual], marker_color=colores_m,
        text=[f"S/ {v/1e6:.2f}M" if v > 0 else "" for v in dev_mensual],
        textposition="outside",
        hovertemplate="%{x}: S/ %{y:.3f}M<extra></extra>"
    ))
    fig_m.add_hline(y=PIM/12/1e6, line_dash="dot", line_color="#ef6c00",
                    annotation_text=f"Ideal: S/ {PIM/12/1e6:.2f}M/mes")
    fig_m.update_layout(height=320, yaxis_title="Millones de S/",
                        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=0,r=0,t=30,b=10))
    st.plotly_chart(fig_m, use_container_width=True)

    # T-02: Variación mensual (ritmo)
    st.markdown("#### T-02 · Variación mensual del devengado (ritmo)")
    variacion = [dev_mensual[0]] + [dev_mensual[i]-dev_mensual[i-1] for i in range(1,12)]
    colores_var = ["#4caf50" if v >= 0 else "#e53935" for v in variacion]
    fig_var = go.Figure(go.Bar(
        x=MESES, y=[v/1e6 for v in variacion], marker_color=colores_var,
        hovertemplate="%{x}: Δ S/ %{y:.3f}M<extra></extra>"
    ))
    fig_var.add_hline(y=0, line_color="#333", line_width=0.5)
    fig_var.update_layout(height=240, yaxis_title="Variación (millones S/)",
                          plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
                          margin=dict(l=0,r=0,t=10,b=10))
    st.plotly_chart(fig_var, use_container_width=True)


# =============================================================================
#  MÓDULO 4 — PROGRAMACIÓN MENSUAL
# =============================================================================
elif pagina == "🎯 Programación mensual":

    st.markdown("## Programación mensual de ejecución")
    st.caption("Registre el devengado mensual programado y compare vs. el real del SIAF.")

    prog = cargar_programacion()   # Cargar programación guardada del archivo JSON

    # st.tabs crea pestañas horizontales
    tab_reg, tab_tabla, tab_graf = st.tabs([
        "✏️ Registrar / editar", "📋 Tabla comparativa", "📈 Gráfico"
    ])

    with tab_reg:
        st.markdown("#### Ingrese el devengado mensual programado (en soles)")
        modo = st.radio("Nivel:", ["Total entidad", "Por genérica"], horizontal=True)

        if modo == "Total entidad":
            vals = {}
            cols_mes = st.columns(4)   # 4 columnas → 3 filas de 4 meses
            for i, mes in enumerate(MESES):
                with cols_mes[i % 4]:  # i % 4 cicla entre 0,1,2,3
                    vals[mes] = st.number_input(
                        mes, min_value=0.0,
                        value=float(prog.get("total", {}).get(mes, 0.0)),
                        step=10_000.0, format="%.0f", key=f"t_{mes}"
                    )
            if st.button("💾 Guardar", type="primary"):
                prog["total"] = vals
                guardar_programacion(prog)
                st.success("✅ Guardado.")
                st.rerun()   # Recargar la app para reflejar cambios
        else:
            gen_elegida = st.selectbox("Genérica:", sorted(df["generica"].dropna().unique()))
            vals_g = {}
            cols_mes = st.columns(4)
            for i, mes in enumerate(MESES):
                with cols_mes[i % 4]:
                    vals_g[mes] = st.number_input(
                        mes, min_value=0.0,
                        value=float(prog.get(gen_elegida, {}).get(mes, 0.0)),
                        step=10_000.0, format="%.0f", key=f"g_{i}"
                    )
            if st.button("💾 Guardar por genérica", type="primary"):
                prog[gen_elegida] = vals_g
                guardar_programacion(prog)
                st.success("✅ Guardado.")
                st.rerun()

        st.divider()
        if st.button("🗑️ Borrar toda la programación", type="secondary"):
            if os.path.exists(PROG_FILE):
                os.remove(PROG_FILE)
            st.warning("Programación eliminada.")
            st.rerun()

    with tab_tabla:
        if "total" not in prog:
            st.warning("Aún no ha registrado la programación. Vaya a 'Registrar / editar'.")
        else:
            prog_lista = [prog["total"].get(m, 0) for m in MESES]
            real_lista = dev_mensual

            # Construir tabla comparativa
            tabla = pd.DataFrame({
                "Mes":         MESES,
                "Programado":  prog_lista,
                "Real (SIAF)": real_lista,
                "Diferencia":  [r-p for r,p in zip(real_lista, prog_lista)],
                "Cumpl. %":    [pct(r,p) if p > 0 else 0.0 for r,p in zip(real_lista, prog_lista)],
                "Estado":      ["✅" if p>0 and pct(r,p)>=85 else
                                ("⚠️" if p>0 and pct(r,p)>=60 else
                                 ("❌" if p>0 else "—"))
                                for r,p in zip(real_lista, prog_lista)]
            })
            # Fila de totales
            total_row = pd.DataFrame([{
                "Mes":"TOTAL", "Programado":sum(prog_lista), "Real (SIAF)":sum(real_lista),
                "Diferencia":sum(real_lista)-sum(prog_lista),
                "Cumpl. %":pct(sum(real_lista),sum(prog_lista)), "Estado":""
            }])
            tabla = pd.concat([tabla, total_row], ignore_index=True)

            st.dataframe(
                tabla.style
                .background_gradient(subset=["Cumpl. %"], cmap="RdYlGn", vmin=0, vmax=120)
                .format({"Programado":"S/ {:,.0f}","Real (SIAF)":"S/ {:,.0f}",
                         "Diferencia":"S/ {:,.0f}","Cumpl. %":"{:.1f}%"}),
                use_container_width=True, hide_index=True
            )

    with tab_graf:
        if "total" not in prog:
            st.warning("Registre primero la programación.")
        else:
            prog_lista = [prog["total"].get(m, 0) for m in MESES]
            fig_pg = go.Figure()
            fig_pg.add_trace(go.Bar(name="Programado", x=MESES,
                y=[v/1e6 for v in prog_lista], marker_color="#90caf9",
                hovertemplate="%{x} prog.: S/ %{y:.3f}M<extra></extra>"))
            fig_pg.add_trace(go.Bar(name="Real SIAF", x=MESES,
                y=[v/1e6 for v in dev_mensual], marker_color="#1565c0",
                hovertemplate="%{x} real: S/ %{y:.3f}M<extra></extra>"))
            fig_pg.update_layout(height=350, barmode="group", yaxis_title="Millones de S/",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=50,b=10))
            st.plotly_chart(fig_pg, use_container_width=True)

            # Curva acumulada
            st.markdown("#### Curva acumulada: programado vs. real")
            pa=ra=0; prog_acum=[]; real_acum=[]
            for pv, rv in zip(prog_lista, dev_mensual):
                pa+=pv; ra+=rv; prog_acum.append(pa); real_acum.append(ra)
            fig_ac = go.Figure()
            fig_ac.add_trace(go.Scatter(x=MESES, y=[v/1e6 for v in prog_acum],
                name="Programado acum.", mode="lines+markers",
                line=dict(dash="dot", color="#90caf9", width=2), marker=dict(size=6)))
            fig_ac.add_trace(go.Scatter(x=MESES, y=[v/1e6 for v in real_acum],
                name="Real acum.", mode="lines+markers",
                line=dict(color="#1565c0", width=2.5), marker=dict(size=7)))
            fig_ac.update_layout(height=300, yaxis_title="Millones de S/ (acumulado)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=50,b=10), hovermode="x unified")
            st.plotly_chart(fig_ac, use_container_width=True)


# =============================================================================
#  MÓDULO 5 — METAS FÍSICAS
#  Seguimiento físico-financiero por meta presupuestal (sec_func)
#  Indicadores M-01 a M-05
# =============================================================================
elif pagina == "🏁 Metas físicas":

    st.markdown("## Metas físicas — seguimiento físico-financiero")
    st.caption("Indicadores M-01 a M-05 · por meta presupuestal (sec_func)")

    st.info(
        "📌 Muestra el avance físico y financiero por cada meta presupuestal. "
        "El coeficiente M-02 compara qué tan alineados están el avance físico y el gasto."
    )

    # Agrupar por meta presupuestal.
    # Para las columnas descriptivas tomamos el primer valor ("first").
    # Para las financieras sumamos todos los registros de esa meta.
    metas_df = df.groupby("sec_func").agg(
        finalidad=("finalidad","first"),
        unidad_medida=("unidad_medida","first"),
        cant_anual=("cant_meta_anual","first"),
        avance_fis=("avan_fisico_anual","first"),
        pim=("mto_pim","sum"),
        dev=("dev_total","sum"),
        programa=("programa_pptal","first")
    ).reset_index()

    # Funciones auxiliares para calcular indicadores por fila
    def af_pct(row): return pct(row["avance_fis"], row["cant_anual"])         # M-01
    def fin_pct(row): return pct(row["dev"], row["pim"])                      # avance financiero
    def efic(row):                                                             # M-02
        # Coeficiente: >1 eficiente, <1 ineficiente, =1 en equilibrio
        f = fin_pct(row)
        return round(af_pct(row) / f, 2) if f > 0 else 0.0
    def cu_prog(row): return round(row["pim"]/row["cant_anual"],2) if row["cant_anual"]>0 else 0   # M-03
    def cu_exec(row): return round(row["dev"]/row["avance_fis"],2) if row["avance_fis"]>0 else 0  # M-04

    # Aplicar los cálculos al DataFrame usando .apply()
    # axis=1 significa "aplicar la función a cada fila" (en lugar de columna)
    metas_df["av_fis_%"]   = metas_df.apply(af_pct,   axis=1)
    metas_df["av_fin_%"]   = metas_df.apply(fin_pct,  axis=1)
    metas_df["efic_M02"]   = metas_df.apply(efic,     axis=1)
    metas_df["cu_prog"]    = metas_df.apply(cu_prog,  axis=1)
    metas_df["cu_exec"]    = metas_df.apply(cu_exec,  axis=1)
    metas_df["brecha"]     = metas_df["av_fis_%"] - metas_df["av_fin_%"]

    # Resumen general
    total_metas   = len(metas_df)
    sin_fis       = (metas_df["av_fis_%"] == 0).sum()
    metas_ok      = (metas_df["av_fin_%"] >= 85).sum()

    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    col_r1.metric("Total metas (sec_func)",     total_metas)
    col_r2.metric("Sin avance físico",           sin_fis,  f"{pct(sin_fis,total_metas):.1f}%")
    col_r3.metric("Avance fin. ≥ 85%",           metas_ok, f"{pct(metas_ok,total_metas):.1f}%")
    col_r4.metric("PIM total",                   fmt(metas_df["pim"].sum()))

    st.divider()

    # Filtros interactivos
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        progs_disp = sorted(metas_df["programa"].dropna().unique())
        filtro_prog = st.multiselect("Programa presupuestal:", progs_disp, default=[])
    with col_f2:
        solo_crit = st.checkbox("Solo metas sin avance físico", value=False)
    with col_f3:
        orden = st.selectbox("Ordenar por:",
                             ["PIM (mayor a menor)","Avance financiero %","Brecha físico-financiero"])

    # Aplicar filtros al DataFrame
    mf = metas_df.copy()
    if filtro_prog: mf = mf[mf["programa"].isin(filtro_prog)]
    if solo_crit:   mf = mf[mf["av_fis_%"] == 0]
    if orden == "PIM (mayor a menor)":        mf = mf.sort_values("pim", ascending=False)
    elif orden == "Avance financiero %":      mf = mf.sort_values("av_fin_%", ascending=True)
    else:                                     mf = mf.sort_values("brecha", ascending=True)

    st.markdown(f"**{len(mf)} metas** mostradas")

    # Gráfico de dispersión: físico vs. financiero (M-02)
    st.markdown("#### M-02 · Avance físico vs. financiero por meta")
    st.caption("Cada punto es una meta. Diagonal = eficiencia perfecta. Bajo la diagonal = gasto supera al avance físico.")

    fig_disp = go.Figure()
    # Línea diagonal de referencia (eficiencia perfecta)
    fig_disp.add_trace(go.Scatter(
        x=[0,100], y=[0,100], mode="lines", name="Eficiencia perfecta",
        line=dict(dash="dot", color="#bdbdbd", width=1.5), hoverinfo="skip"
    ))
    # Puntos de dispersión: el tamaño del punto refleja el PIM de la meta
    fig_disp.add_trace(go.Scatter(
        x=mf["av_fin_%"], y=mf["av_fis_%"], mode="markers", name="Metas",
        marker=dict(
            size=mf["pim"].apply(lambda v: max(8, min(30, v/500_000))),  # Tamaño proporcional al PIM
            color=mf["efic_M02"], colorscale="RdYlGn", cmin=0, cmax=2,  # Color = eficiencia
            showscale=True, colorbar=dict(title="Eficiencia", thickness=12)
        ),
        text=mf["finalidad"].str[:40],
        hovertemplate="<b>%{text}</b><br>Fin.: %{x:.1f}%<br>Fís.: %{y:.1f}%<extra></extra>"
    ))
    fig_disp.update_layout(
        height=400,
        xaxis=dict(title="Avance financiero %", range=[-5,105]),
        yaxis=dict(title="Avance físico %",     range=[-5,105]),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=10,b=10)
    )
    st.plotly_chart(fig_disp, use_container_width=True)

    # Tabla de metas
    st.markdown("#### Tabla de metas presupuestales")
    tabla_m = mf[["sec_func","finalidad","unidad_medida","cant_anual","avance_fis",
                  "av_fis_%","pim","dev","av_fin_%","efic_M02","cu_prog","brecha"]].rename(columns={
        "sec_func":"Sec.func.","finalidad":"Finalidad","unidad_medida":"Unidad",
        "cant_anual":"Meta anual","avance_fis":"Avance fís.","av_fis_%":"Fís.%",
        "pim":"PIM","dev":"Devengado","av_fin_%":"Fin.%",
        "efic_M02":"Efic.M02","cu_prog":"Costo unit.prog.","brecha":"Brecha pp"
    })
    st.dataframe(
        tabla_m.style
        .background_gradient(subset=["Fin.%"], cmap="RdYlGn", vmin=0, vmax=100)
        .background_gradient(subset=["Fís.%"], cmap="RdYlGn", vmin=0, vmax=100)
        .format({"PIM":"S/ {:,.0f}","Devengado":"S/ {:,.0f}","Costo unit.prog.":"S/ {:,.0f}",
                 "Fin.%":"{:.1f}%","Fís.%":"{:.1f}%","Brecha pp":"{:+.1f}","Efic.M02":"{:.2f}"}),
        use_container_width=True, height=420, hide_index=True
    )
    csv_m = tabla_m.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Exportar metas a CSV", csv_m,
                       file_name=f"metas_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")


# =============================================================================
#  MÓDULO 6 — BENCHMARK SECTORIAL
#  IPEN vs. Sector 16-Energía y Minas — Indicador C-04
# =============================================================================
elif pagina == "📡 Benchmark sectorial":

    st.markdown("## Benchmark sectorial — IPEN vs. Sector 16-Energía y Minas")
    st.caption("Indicador C-04 · Fuente: Consulta Amigable MEF (apps5.mineco.gob.pe/transparencia)")

    st.info(
        "📌 Los valores del sector se obtienen de la Consulta Amigable MEF. "
        "Actualice los campos con datos reales del portal. Los valores por defecto son estimaciones históricas."
    )

    # Cargar benchmark guardado, o usar valores por defecto (BENCHMARK_SECTOR)
    prog_bm = cargar_programacion()
    bm = prog_bm.get("benchmark_sector", BENCHMARK_SECTOR.copy())

    # Formulario para actualizar benchmark sectorial (colapsado por defecto)
    with st.expander("✏️ Actualizar avances sectoriales desde Consulta Amigable MEF", expanded=False):
        bm_nuevos = {}
        cols_bm = st.columns(4)
        for i, mes in enumerate(MESES):
            with cols_bm[i % 4]:
                bm_nuevos[mes] = st.number_input(
                    f"Sector {mes} (%)", min_value=0.0, max_value=100.0,
                    value=float(bm.get(mes, BENCHMARK_SECTOR.get(mes, 0.0))),
                    step=0.1, format="%.1f", key=f"bm_{mes}"
                )
        if st.button("💾 Guardar benchmark", type="primary"):
            prog_bm["benchmark_sector"] = bm_nuevos
            guardar_programacion(prog_bm)
            bm = bm_nuevos
            st.success("✅ Benchmark sectorial actualizado.")
            st.rerun()

    # Calcular avance IPEN acumulado mes a mes (en %)
    ipen_acum = []
    acum = 0
    for v in dev_mensual:
        acum += v
        ipen_acum.append(pct(acum, PIM))

    # Convertir benchmark a lista en orden de meses
    sector_acum = [bm.get(m, 0.0) for m in MESES]

    # Métricas comparativas al mes de corte
    av_ipen_c   = ipen_acum[mes_corte - 1]
    av_sector_c = sector_acum[mes_corte - 1]
    brecha_c    = round(av_ipen_c - av_sector_c, 1)

    col_c1, col_c2, col_c3 = st.columns(3)
    col_c1.metric(f"IPEN — avance a {MESES[mes_corte-1]}",   f"{av_ipen_c:.1f}%",   fmt(DEV))
    col_c2.metric(f"Sector 16 — avance a {MESES[mes_corte-1]}", f"{av_sector_c:.1f}%", "Consulta Amigable MEF")
    col_c3.metric("C-04 · Brecha IPEN vs. Sector",           f"{brecha_c:+.1f} pp",
                  "Positivo = IPEN adelante del sector")

    st.divider()

    # Gráfico comparativo de trayectorias
    st.markdown("#### Trayectoria de avance acumulado: IPEN vs. Sector 16")
    fig_bm = go.Figure()

    # Línea ideal lineal (punteada gris)
    fig_bm.add_trace(go.Scatter(
        x=MESES, y=[round((i+1)/12*100,1) for i in range(12)], mode="lines",
        name="Ideal lineal", line=dict(dash="dot", color="#bdbdbd", width=1.5), hoverinfo="skip"
    ))
    # Línea Sector 16 (naranja)
    fig_bm.add_trace(go.Scatter(
        x=MESES, y=sector_acum, mode="lines+markers", name="Sector 16-Energía y Minas",
        line=dict(color="#ef6c00", width=2, dash="dashdot"),
        marker=dict(size=7, symbol="diamond"),
        hovertemplate="Sector %{x}: %{y:.1f}%<extra></extra>"
    ))
    # Línea IPEN (azul)
    fig_bm.add_trace(go.Scatter(
        x=MESES, y=ipen_acum, mode="lines+markers", name="IPEN (Pliego 220)",
        line=dict(color="#1565c0", width=2.5), marker=dict(size=8),
        hovertemplate="IPEN %{x}: %{y:.1f}%<extra></extra>"
    ))
    # Zona sombreada entre las curvas para visualizar la brecha
    fig_bm.add_trace(go.Scatter(
        x=MESES + MESES[::-1],     # Lista de meses + lista inversa de meses
        y=ipen_acum + sector_acum[::-1],  # Valores IPEN + valores sector inversos
        fill="toself", fillcolor="rgba(21,101,192,0.08)",
        line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
    ))
    fig_bm.add_hline(y=100, line_dash="dot", line_color="#e53935", annotation_text="Meta 100%")
    fig_bm.update_layout(
        height=420, yaxis=dict(title="Avance %", range=[0,110], ticksuffix="%"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=50,b=10), hovermode="x unified"
    )
    st.plotly_chart(fig_bm, use_container_width=True)

    # Tabla de brechas mes a mes
    st.markdown("#### Tabla de brechas IPEN vs. Sector 16")
    tabla_bm = pd.DataFrame({
        "Mes":         MESES,
        "IPEN %":      [round(v,1) for v in ipen_acum],
        "Sector 16 %": [round(v,1) for v in sector_acum],
        "Brecha (pp)": [round(i-s,1) for i,s in zip(ipen_acum, sector_acum)],
        "Posición":    ["🟢 Adelante" if i > s+2 else ("🔴 Rezagado" if i < s-2 else "⚪ Par")
                        for i,s in zip(ipen_acum, sector_acum)]
    })
    st.dataframe(
        tabla_bm.style.background_gradient(subset=["Brecha (pp)"], cmap="RdYlGn", vmin=-20, vmax=20),
        use_container_width=True, hide_index=True
    )

    st.divider()
    st.markdown("""
    **Cómo obtener datos del Sector 16 en Consulta Amigable MEF:**
    1. Ir a [apps5.mineco.gob.pe/transparencia](https://apps5.mineco.gob.pe/transparencia/navegador/default.aspx)
    2. Seleccionar: Año = 2026 → Sector = **16 Energía y Minas**
    3. Ver el porcentaje Devengado / PIM acumulado al mes de corte
    4. Ingresar esos valores en el formulario de arriba
    """)


# =============================================================================
#  MÓDULO 7 — RESTRICCIONES NORMATIVAS
#  Indicadores L-02 a L-07
# =============================================================================
elif pagina == "⚖️ Restricciones normativas":

    st.markdown("## Restricciones normativas — Ley N° 32513 y D.L. 1440")
    st.caption("Monitoreo de partidas con restricción legal. Indicadores L-02 a L-07.")

    st.warning(
        "⚠️ Las partidas en rojo tienen restricciones críticas. "
        "El incumplimiento puede generar responsabilidad administrativa y penal."
    )

    # Iterar sobre cada restricción definida en la constante RESTRICCIONES
    for r in RESTRICCIONES:
        kws   = KEYWORDS_RESTRICCION.get(r["codigo"], [])
        nivel = r["nivel"]

        # Filtrar el DataFrame según la restricción
        if kws:
            # Buscar filas donde el nombre de la específica contiene alguna palabra clave
            # .fillna("") evita errores si hay celdas vacías
            # .str.upper() convierte a mayúsculas para comparación sin importar capitalización
            mask  = df["especifica_det"].fillna("").str.upper()
            mask  = mask.apply(lambda x: any(k.upper() in x for k in kws))
            sub   = df[mask]
        elif r["codigo"] == "L-06":
            sub = df[df["generica"].str.startswith("1.", na=False)]
        elif r["codigo"] == "L-07":
            sub = df[df["mto_modificaciones"] != 0]
        else:
            sub = pd.DataFrame()

        pim_r = sub["mto_pim"].sum()  if not sub.empty else 0
        dev_r = sub["dev_total"].sum() if not sub.empty else 0
        mod_r = sub["mto_modificaciones"].sum() if not sub.empty else 0
        av_r  = pct(dev_r, pim_r)

        icono = {"ok":"🟢","warn":"🟡","alert":"🔴"}.get(nivel,"⚪")

        # st.expander: sección colapsable (el usuario puede abrirla/cerrarla)
        with st.expander(f"{icono} **{r['codigo']}** · {r['nombre']} · `{r['partida']}`"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("PIM asignado", fmt(pim_r))
            c2.metric("Devengado",    fmt(dev_r))
            c3.metric("Avance",       f"{av_r:.1f}%")
            c4.metric("Modificaciones", fmt(mod_r),
                      "⚠️ Verificar" if mod_r != 0 and r["codigo"] in ["L-02","L-03","L-04"] else "")
            st.markdown(f"**Base normativa:** `{r['norma']}`")
            st.caption(r["detalle"])

            if not sub.empty:
                det = sub.groupby("especifica_det").agg(
                    PIM=("mto_pim","sum"),
                    Modificaciones=("mto_modificaciones","sum"),
                    Devengado=("dev_total","sum")
                ).reset_index().rename(columns={"especifica_det":"Específica"})
                det["Avance %"] = det.apply(lambda x: pct(x["Devengado"], x["PIM"]), axis=1)
                st.dataframe(
                    det.style.format({"PIM":"S/ {:,.0f}","Modificaciones":"S/ {:,.0f}",
                                      "Devengado":"S/ {:,.0f}","Avance %":"{:.1f}%"}),
                    use_container_width=True, hide_index=True
                )

    st.divider()
    st.markdown("#### Resumen de modificaciones por genérica (L-07)")
    mod_df = df[df["mto_modificaciones"] != 0]
    if not mod_df.empty:
        res_mod = mod_df.groupby("generica").agg(
            pim=("mto_pim","sum"), modif=("mto_modificaciones","sum")).reset_index()
        res_mod["Δ% sobre PIA"] = res_mod.apply(lambda x: pct(x["modif"], x["pim"]-x["modif"]), axis=1)
        st.dataframe(
            res_mod.rename(columns={"generica":"Genérica","pim":"PIM","modif":"Modif. neta"})
            .style.format({"PIM":"S/ {:,.0f}","Modif. neta":"S/ {:,.0f}","Δ% sobre PIA":"{:+.1f}%"}),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("No se detectaron modificaciones en la data cargada.")


# =============================================================================
#  MÓDULO 8 — EXPLORADOR DE PARTIDAS
#  Cruce dinámico por cualquier dimensión — Indicadores R-01, R-03
# =============================================================================
elif pagina == "🔍 Explorador de partidas":

    st.markdown("## Explorador dinámico de partidas")
    st.caption("Cruce flexible por cualquier dimensión del SIAF. R-01 (concentración) y R-03 (durmientes).")

    # Filtros en la barra lateral (sidebar)
    with st.sidebar:
        st.markdown("**🔧 Filtros del explorador**")

        cats_l = ["Todos"] + sorted(df["categoria_gasto"].dropna().unique())
        cat_s  = st.selectbox("Categoría:", cats_l, key="ex_cat")

        fue_l  = ["Todas"] + sorted(df["fuente_financ"].dropna().unique())
        fue_s  = st.selectbox("Fuente:", fue_l, key="ex_fue")

        gen_l  = ["Todas"] + sorted(df["generica"].dropna().unique())
        gen_s  = st.selectbox("Genérica:", gen_l, key="ex_gen")

        prog_l = ["Todos"] + sorted(df["programa_pptal"].dropna().unique())
        prog_s = st.selectbox("Programa:", prog_l, key="ex_prog")

        solo_dur = st.checkbox("Solo partidas durmientes R-03\n(PIM>0 y Dev=0)", value=False)

        # Slider: filtrar por monto mínimo de PIM (en miles de soles)
        pim_min = st.slider("PIM mínimo (miles S/):", 0, 500, 0, 10) * 1_000

    # Aplicar filtros al DataFrame
    dff = df.copy()
    if cat_s  != "Todos":  dff = dff[dff["categoria_gasto"] == cat_s]
    if fue_s  != "Todas":  dff = dff[dff["fuente_financ"]   == fue_s]
    if gen_s  != "Todas":  dff = dff[dff["generica"]        == gen_s]
    if prog_s != "Todos":  dff = dff[dff["programa_pptal"]  == prog_s]
    if solo_dur:           dff = dff[(dff["mto_pim"]>0) & (dff["dev_total"]==0)]
    if pim_min > 0:        dff = dff[dff["mto_pim"] >= pim_min]

    # Selector de dimensión de agrupación
    col_dim, col_info = st.columns([2, 1])
    with col_dim:
        dim = st.selectbox(
            "Agrupar resultados por:",
            ["especifica_det","subgenerica_det","generica","fuente_financ",
             "categoria_gasto","funcion","sec_func","programa_pptal",
             "producto_proyecto","departamento_meta"]
        )
    with col_info:
        st.metric("Registros", f"{len(dff):,}")
        st.metric("PIM filtrado", fmt(dff["mto_pim"].sum()))

    pim_fil = dff["mto_pim"].sum()

    # Agrupar y calcular la tabla de resultados
    tabla_e = dff.groupby(dim).agg(
        PIM=("mto_pim","sum"), Certificado=("mto_certificado","sum"),
        Comprometido=("mto_compro_anual","sum"), Devengado=("dev_total","sum"),
        Pagado=("pag_total","sum")
    ).reset_index()
    tabla_e["Avance %"] = tabla_e.apply(lambda r: round(pct(r["Devengado"], r["PIM"]),1), axis=1)
    tabla_e["Share %"]  = tabla_e.apply(lambda r: round(pct(r["PIM"], pim_fil),1), axis=1)
    tabla_e = tabla_e.sort_values("PIM", ascending=False)

    # Mostrar tabla con gradiente de color en la columna Avance %
    st.dataframe(
        tabla_e.style
        .background_gradient(subset=["Avance %"], cmap="RdYlGn", vmin=0, vmax=100)
        .format({"PIM":"S/ {:,.0f}","Certificado":"S/ {:,.0f}","Comprometido":"S/ {:,.0f}",
                 "Devengado":"S/ {:,.0f}","Pagado":"S/ {:,.0f}",
                 "Avance %":"{:.1f}%","Share %":"{:.1f}%"}),
        use_container_width=True, height=420, hide_index=True
    )

    # Análisis de concentración — Top 10 (R-01)
    st.divider()
    st.markdown("#### R-01 · Concentración — Top 10 por PIM")
    top10 = tabla_e.head(10).copy()
    concentracion = pct(top10["PIM"].sum(), pim_fil)

    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        fig_t = go.Figure(go.Bar(
            x=top10[dim].str[:35], y=top10["PIM"]/1e6,
            marker_color=["#1565c0" if i<5 else "#90caf9" for i in range(len(top10))],
            text=[f"{pct(v, pim_fil):.1f}%" for v in top10["PIM"]],
            textposition="outside",
            hovertemplate="%{x}<br>PIM: S/ %{y:.2f}M<extra></extra>"
        ))
        fig_t.update_layout(height=300, yaxis_title="Millones S/", xaxis_tickangle=-35,
                            plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
                            margin=dict(l=0,r=0,t=20,b=10))
        st.plotly_chart(fig_t, use_container_width=True)

    with col_t2:
        st.metric("Concentración Top 10", f"{concentracion:.1f}%", "del PIM filtrado")
        if concentracion >= 70:
            st.error("Alta concentración")
        elif concentracion >= 50:
            st.warning("Concentración moderada")
        else:
            st.success("Gasto diversificado")

    # Botón para descargar la tabla como archivo CSV
    csv_e = tabla_e.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Exportar a CSV", csv_e,
        file_name=f"partidas_{dim}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )


# =============================================================================
#  FIN DE LA APLICACIÓN
#  Streamlit ejecuta este archivo de arriba a abajo cada vez que el usuario
#  interactúa. Las funciones con @st.cache_data guardan resultados en memoria
#  para no recalcular innecesariamente (importante con archivos Excel grandes).
# =============================================================================

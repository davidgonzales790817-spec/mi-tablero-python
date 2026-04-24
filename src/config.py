# ═══════════════════════════════════════════════════════════════════════════════
# src/config.py — CONFIGURACIÓN CENTRALIZADA
# ═══════════════════════════════════════════════════════════════════════════════
#
# PROPÓSITO: Un único lugar para TODAS las constantes de la app
# Si necesitas cambiar un color, número o texto, lo cambias aquí una sola vez
# y automáticamente se actualiza en toda la aplicación.
#
# ═══════════════════════════════════════════════════════════════════════════════

# Importar Plotly Express para acceder a paletas de colores predefinidas
import plotly.express as px

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1: CONFIGURACIÓN DE STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════════
# Estos parámetros controlan cómo se ve la página en el navegador

PAGE_CONFIG = {
    # Texto que aparece en la pestaña del navegador
    "page_title": "Tablero Presupuestal SIAF",
    
    # Emoji que aparece junto al título en la pestaña
    "page_icon": "📊",
    
    # Layout: "wide" = ocupar todo el ancho, "centered" = centrado con márgenes
    "layout": "wide",
    
    # Estado inicial del sidebar: "expanded" = abierto, "collapsed" = cerrado
    "initial_sidebar_state": "expanded",
}

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2: RUTAS DE ARCHIVOS
# ═══════════════════════════════════════════════════════════════════════════════

# Carpeta donde se guardarán los archivos Excel que suban los usuarios
# Relativa a donde ejecutas: streamlit run src/app.py
CARPETA_DATA = "Respaldo_Data"

# URL del logo de IPEN (se muestra en el sidebar)
LOGO_URL = "https://www.ipen.gob.pe/templates/ipen/images/logo-ipen.png"

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3: CALENDARIO
# ═══════════════════════════════════════════════════════════════════════════════
# Lista de los 12 meses en español, en orden

MESES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Setiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4: COLORES PARA GRÁFICOS
# ═══════════════════════════════════════════════════════════════════════════════

# Paleta de colores para gráficos de barras apiladas (6 colores bonitos)
# Set2 es una paleta de Plotly que se ve bien
COLORES_GENERICAS = px.colors.qualitative.Set2

# Colores específicos para los indicadores (gauges)
COLORES_GAUGE = {
    "certificado": "#1f77b4",  # Azul oscuro
    "compromiso": "#ff7f0e",   # Naranja
    "devengado": "#2ca02c",    # Verde
}

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5: PATRONES REGEX PARA DETECTAR COLUMNAS SIAF
# ═══════════════════════════════════════════════════════════════════════════════
#
# El problema: cada institución exporta el Excel con nombres de columna diferentes
# - IPEN usa: "mto_devenga_01", "mto_devenga_02", etc.
# - Otra institución puede usar: "devengado_01", "mes_01", etc.
#
# Solución: Usar expresiones regulares (regex) para encontrar columnas por patrón
# En lugar de buscar el nombre exacto, buscamos un patrón.

PATRONES_DEVENGADO = [
    r"mto_devenga_\d{2}",      # Ejemplo: "mto_devenga_01" (dos dígitos)
    r"devengado",              # Simplemente contiene la palabra "devengado"
    r"monto_devengado",        # O "monto_devengado"
    r"mes_\d{2}",              # O "mes_01", "mes_02", etc.
]

# Palabras que EXCLUYEN una columna de ser identificada como devengado
# Porque si dice "mto_pim" no la queremos confundir con devengado
PATRONES_EXCLUIR = [
    "mto_pim",
    "pim",
    "mto_certificado",
    "certificado",
    "mto_compro_anual",
    "compromiso",
    "total",
    "año",
    "ano",
]

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6: CSS PERSONALIZADO
# ═══════════════════════════════════════════════════════════════════════════════
# HTML + CSS que se inyecta en la página para personalizar estilos

CSS_EXTRA = """
<style>
/* Barra lateral: ancho mínimo de 260 pixels */
[data-testid="stSidebar"] { min-width: 260px !important; }

/* Contenedor principal: agregar espacio arriba */
.block-container { padding-top: 1rem !important; }

/* Tarjetas de métrica (los KPI boxes con números grandes) */
div[data-testid="metric-container"] {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px 16px;
}

/* Título del header */
.header-title {
    font-size: clamp(16px, 2.5vw, 24px);
    font-weight: 700;
    color: #1e3a5f;
}

/* Subtítulo del header */
.header-sub {
    font-size: clamp(11px, 1.5vw, 14px);
    color: #64748b;
}

/* En celulares */
@media (max-width: 768px) {
    .block-container { padding: 0.5rem !important; }
    div[data-testid="metric-container"] { padding: 8px 10px; }
}
</style>
"""

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7: PROGRAMACIÓN PRECARGADA (DATOS DE IPEN 2026)
# ═══════════════════════════════════════════════════════════════════════════════
#
# EXPLICACIÓN:
# Este es un diccionario (dict) con la programación presupuestal de IPEN para 2026
#
# ESTRUCTURA:
#   - Nivel 1: Clave = Genérica de gasto (ej: "1.PERSONAL Y OBLIGACIONES SOCIALES")
#   - Nivel 2: Clave = Mes en español (ej: "Enero", "Febrero")
#   - Valor: Monto en soles programado para ese mes-genérica
#
# EJEMPLO DE LECTURA:
#   PROGRAMACION_PRECARGADA["1.PERSONAL Y OBLIGACIONES SOCIALES"]["Enero"]
#   = 1_580_315 soles
#
# USO EN LA APP:
#   Cuando el usuario carga el archivo Excel, la app permite editar la programación
#   Si el usuario quiere "restaurar valores oficiales", estos datos se usan.
#
# NOTA: Los números tienen guiones bajos (_) para legibilidad
#   1_580_315 es lo mismo que 1580315, pero más fácil de leer

PROGRAMACION_PRECARGADA = {
    "1.PERSONAL Y OBLIGACIONES SOCIALES": {
        "Enero": 1_580_315,
        "Febrero": 1_513_999,
        "Marzo": 1_758_827,
        "Abril": 2_511_367,
        "Mayo": 1_777_661,
        "Junio": 1_769_061,
        "Julio": 3_283_142,
        "Agosto": 1_752_061,
        "Setiembre": 1_752_061,
        "Octubre": 2_511_367,
        "Noviembre": 1_752_061,
        "Diciembre": 4_433_250,
    },
    "2.PENSIONES Y OTRAS PRESTACIONES SOCIALES": {
        "Enero": 120_258,
        "Febrero": 103_476,
        "Marzo": 102_467,
        "Abril": 104_058,
        "Mayo": 104_058,
        "Junio": 104_058,
        "Julio": 122_591,
        "Agosto": 104_058,
        "Setiembre": 104_058,
        "Octubre": 104_058,
        "Noviembre": 104_058,
        "Diciembre": 168_358,
    },
    "3.BIENES Y SERVICIOS": {
        "Enero": 254_138,
        "Febrero": 944_140,
        "Marzo": 1_405_023,
        "Abril": 2_563_008,
        "Mayo": 2_640_117,
        "Junio": 2_631_808,
        "Julio": 2_760_267,
        "Agosto": 2_803_458,
        "Setiembre": 2_804_461,
        "Octubre": 2_792_513,
        "Noviembre": 2_892_769,
        "Diciembre": 3_637_567,
    },
    "4.DONACIONES Y TRANSFERENCIAS": {
        "Enero": 0,
        "Febrero": 400_000,
        "Marzo": 0,
        "Abril": 0,
        "Mayo": 0,
        "Junio": 0,
        "Julio": 0,
        "Agosto": 0,
        "Setiembre": 86_914,
        "Octubre": 0,
        "Noviembre": 0,
        "Diciembre": 0,
    },
    "5.OTROS GASTOS": {
        "Enero": 0,
        "Febrero": 67_398,
        "Marzo": 1_432,
        "Abril": 0,
        "Mayo": 0,
        "Junio": 0,
        "Julio": 93_295,
        "Agosto": 0,
        "Setiembre": 0,
        "Octubre": 0,
        "Noviembre": 0,
        "Diciembre": 0,
    },
    "6.ADQUISICION DE ACTIVOS NO FINANCIEROS": {
        "Enero": 0,
        "Febrero": 279_909,
        "Marzo": 165_463,
        "Abril": 482_713,
        "Mayo": 5_982_148,
        "Junio": 1_542_038,
        "Julio": 1_381_225,
        "Agosto": 1_600_025,
        "Setiembre": 2_162_400,
        "Octubre": 1_994_755,
        "Noviembre": 1_634_224,
        "Diciembre": 4_741_390,
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# FIN DE CONFIG.PY
# ═══════════════════════════════════════════════════════════════════════════════

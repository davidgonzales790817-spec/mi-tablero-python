# src/config.py
# ─────────────────────────────────────────────────────────────────────────────
# Configuración global del Tablero Presupuestal SIAF — versión 2.0
# Paleta "Treasury Vault" basada en tendencias dashboards 2026
# ─────────────────────────────────────────────────────────────────────────────

# ═══════════════════════════════════════════════════════════════════════════
# PALETA TREASURY VAULT
# Inspirada en investigación 2026: Recursion (tinted neutrals), media.io
# (Vault Green), Phoenix Strategy (financial dashboards). Cada color tiene
# un rol semántico — no se usa para diferenciación visual arbitraria.
# ═══════════════════════════════════════════════════════════════════════════

PALETA = {
    # Neutrales tintados zinc (no gris puro #808080)
    # Usar para: bases, texto, ejes, grids, bordes
    "bg_primary":      "#FAFAFA",  # fondo principal modo claro
    "bg_secondary":    "#F4F4F5",  # superficies (cards, panels)
    "bg_tertiary":     "#E4E4E7",  # bordes suaves, separadores
    "bg_dark_primary": "#09090B",  # fondo principal modo oscuro
    "bg_dark_secondary": "#18181B", # superficies oscuras
    "bg_dark_tertiary":  "#27272A", # bordes oscuros

    "text_primary":   "#18181B",  # texto principal modo claro
    "text_secondary": "#52525B",  # texto secundario
    "text_muted":     "#71717A",  # texto terciario, hints
    "text_dark_primary":   "#FAFAFA",  # texto principal modo oscuro
    "text_dark_secondary": "#A1A1AA",  # texto secundario modo oscuro

    # Treasury green — color de marca (usar con moderación)
    # Usar para: KPI principal, programación, ejecución acumulada, líneas meta
    "brand":      "#1D9E75",
    "brand_dark": "#0F6E56",
    "brand_light": "#5DCAA5",
    "brand_50":   "#E1F5EE",   # backgrounds suaves para badges

    # Trust blue — información, drill-down, certificado
    "info":       "#185FA5",
    "info_dark":  "#0C447C",
    "info_light": "#85B7EB",
    "info_50":    "#E6F1FB",

    # Caution amber — atención, riesgo moderado, ejecución 30%-70%
    "warning":      "#BA7517",
    "warning_dark": "#854F0B",
    "warning_50":   "#FAEEDA",

    # Critical red — subejecución, anomalías, alertas urgentes
    "danger":      "#A32D2D",
    "danger_dark": "#791F1F",
    "danger_50":   "#FCEBEB",

    # Coral accent — comparativos vs año anterior, marcadores temporales
    "accent":     "#D85A30",
    "accent_dark": "#993C1D",
}

# ═══════════════════════════════════════════════════════════════════════════
# COLORES POR GENÉRICA (rampa única teal — no rainbow)
# Todas las genéricas usan stops del mismo color para no saturar visualmente
# ═══════════════════════════════════════════════════════════════════════════

COLORES_GENERICAS = [
    "#04342C",  # 1. Personal — más oscuro (mayor presupuesto típicamente)
    "#085041",  # 2. Pensiones
    "#0F6E56",  # 3. Bienes y servicios
    "#1D9E75",  # 4. Donaciones
    "#5DCAA5",  # 5. Otros gastos
    "#9FE1CB",  # 6. Adquisición activos
]

# Mapping específico por código de genérica para consistencia
COLOR_POR_GENERICA = {
    "1.PERSONAL Y OBLIGACIONES SOCIALES": "#04342C",
    "2.PENSIONES Y OTRAS PRESTACIONES SOCIALES": "#085041",
    "3.BIENES Y SERVICIOS": "#0F6E56",
    "4.DONACIONES Y TRANSFERENCIAS": "#1D9E75",
    "5.OTROS GASTOS": "#5DCAA5",
    "6.ADQUISICION DE ACTIVOS NO FINANCIEROS": "#9FE1CB",
}

# ═══════════════════════════════════════════════════════════════════════════
# UMBRALES DE EJECUCIÓN (basados en directiva DGPP-MEF)
# Las "tres zonas" oficiales del MEF para clasificación de avance financiero
# ═══════════════════════════════════════════════════════════════════════════

UMBRALES_EJECUCION = {
    "bajo":     {"min": 0,    "max": 31.7, "color": "#A32D2D", "label": "Bajo"},
    "moderado": {"min": 31.7, "max": 45.2, "color": "#BA7517", "label": "Moderado"},
    "alto":     {"min": 45.2, "max": 100,  "color": "#1D9E75", "label": "Alto"},
}

def color_por_avance(pct: float) -> str:
    """Retorna el color semántico según el % de avance."""
    if pct < UMBRALES_EJECUCION["bajo"]["max"]:
        return UMBRALES_EJECUCION["bajo"]["color"]
    if pct < UMBRALES_EJECUCION["moderado"]["max"]:
        return UMBRALES_EJECUCION["moderado"]["color"]
    return UMBRALES_EJECUCION["alto"]["color"]

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTES TEMPORALES
# ═══════════════════════════════════════════════════════════════════════════

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Setiembre", "Octubre", "Noviembre", "Diciembre"
]

MESES_ABREV = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
               "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE GRÁFICOS PLOTLY (modo claro y oscuro)
# ═══════════════════════════════════════════════════════════════════════════

PLOTLY_THEME_LIGHT = {
    "layout": {
        "font": {"family": "Inter, system-ui, sans-serif", "size": 12, "color": "#52525B"},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "#FAFAFA",
        "xaxis": {"gridcolor": "#E4E4E7", "linecolor": "#E4E4E7", "zerolinecolor": "#E4E4E7"},
        "yaxis": {"gridcolor": "#E4E4E7", "linecolor": "#E4E4E7", "zerolinecolor": "#E4E4E7"},
        "colorway": COLORES_GENERICAS,
        "hoverlabel": {"bgcolor": "#18181B", "font": {"color": "#FAFAFA", "size": 12}},
    }
}

PLOTLY_THEME_DARK = {
    "layout": {
        "font": {"family": "Inter, system-ui, sans-serif", "size": 12, "color": "#A1A1AA"},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "#18181B",
        "xaxis": {"gridcolor": "#27272A", "linecolor": "#27272A", "zerolinecolor": "#27272A"},
        "yaxis": {"gridcolor": "#27272A", "linecolor": "#27272A", "zerolinecolor": "#27272A"},
        "colorway": COLORES_GENERICAS,
        "hoverlabel": {"bgcolor": "#FAFAFA", "font": {"color": "#18181B", "size": 12}},
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# PATRONES DE COLUMNAS SIAF (regex para detección automática)
# ═══════════════════════════════════════════════════════════════════════════

PATRONES_COLUMNAS = {
    "pia":         [r"mto_pia", r"pia$", r"presupuesto_inicial_apertura"],
    "pim":         [r"mto_pim", r"pim$", r"presupuesto_inicial_modificado"],
    "certificado": [r"mto_certificado", r"certificado", r"certif"],
    "compromiso":  [r"mto_compro_anual", r"compromiso", r"compro_anual"],
    "devengado":   [r"mto_devenga_\d{2}", r"devengado_\d{2}", r"deveng_\d{2}"],
    "girado":      [r"mto_girado", r"girado"],
    "pagado":      [r"mto_pagado", r"pagado"],
    "generica":    [r"^generica$", r"genérica", r"clasif_generica"],
    "fuente":      [r"fuente_financ", r"ff_concat", r"ff$"],
    "ue":          [r"unidad_ejecutora", r"^ue$", r"sec_ejec"],
    "clasificador":[r"clasificador", r"especifica"],
}

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN INSTITUCIONAL (overrideable via .env)
# ═══════════════════════════════════════════════════════════════════════════

INSTITUCION = {
    "nombre": "IPEN",
    "nombre_completo": "Instituto Peruano de Energía Nuclear",
    "logo_url": "https://www.ipen.gob.pe/templates/ipen/images/logo-ipen.png",
    "ejercicio_fiscal": 2026,
}

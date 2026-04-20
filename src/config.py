# src/config.py
# ─────────────────────────────────────────────────────────────────────────────
# Configuración global del Tablero Presupuestal SIAF
# ─────────────────────────────────────────────────────────────────────────────

import plotly.express as px

# ── Página ────────────────────────────────────────────────────────────────────
PAGE_CONFIG = {
    "page_title": "Tablero Presupuestal SIAF",
    "page_icon":  "📊",
    "layout":     "wide",
    "initial_sidebar_state": "expanded",
}

# ── Rutas ─────────────────────────────────────────────────────────────────────
CARPETA_DATA = "Respaldo_Data"
LOGO_URL     = "https://www.ipen.gob.pe/templates/ipen/images/logo-ipen.png"

# ── Calendario ────────────────────────────────────────────────────────────────
MESES = [
    "Enero", "Febrero", "Marzo", "Abril",
    "Mayo",  "Junio",   "Julio", "Agosto",
    "Setiembre", "Octubre", "Noviembre", "Diciembre",
]

# ── Paleta de colores ─────────────────────────────────────────────────────────
COLORES_GENERICAS = px.colors.qualitative.Set2

COLORES_GAUGE = {
    "certificado": "#1f77b4",
    "compromiso":  "#ff7f0e",
    "devengado":   "#2ca02c",
}

# ── Patrones de detección de columnas SIAF ────────────────────────────────────
PATRONES_DEVENGADO = [
    r"mto_devenga_\d{2}",
    r"devengado",
    r"monto_devengado",
    r"mes_\d{2}",
]

PATRONES_EXCLUIR = [
    "mto_pim", "pim", "mto_certificado", "certificado",
    "mto_compro_anual", "compromiso", "total", "año", "ano",
]

# ── CSS responsivo ────────────────────────────────────────────────────────────
CSS_EXTRA = """
<style>
[data-testid="stSidebar"] { min-width: 260px !important; }
.block-container { padding-top: 1rem !important; }

div[data-testid="metric-container"] {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px 16px;
}

.header-title { font-size: clamp(16px, 2.5vw, 24px); font-weight: 700; color: #1e3a5f; }
.header-sub   { font-size: clamp(11px, 1.5vw, 14px); color: #64748b; }

@media (max-width: 768px) {
    .block-container { padding: 0.5rem !important; }
    div[data-testid="metric-container"] { padding: 8px 10px; }
}
</style>
"""

# ── Programación mensual precargada (Fuente: tabla oficial IPEN 2026) ─────────
PROGRAMACION_PRECARGADA = {
    "1.PERSONAL Y OBLIGACIONES SOCIALES": {
        "Enero": 1_580_315, "Febrero": 1_513_999, "Marzo":  1_758_827,
        "Abril": 2_511_367, "Mayo":    1_777_661, "Junio":  1_769_061,
        "Julio": 3_283_142, "Agosto":  1_752_061, "Setiembre": 1_752_061,
        "Octubre": 2_511_367, "Noviembre": 1_752_061, "Diciembre": 4_433_250,
    },
    "2.PENSIONES Y OTRAS PRESTACIONES SOCIALES": {
        "Enero": 120_258, "Febrero": 103_476, "Marzo":  102_467,
        "Abril": 104_058, "Mayo":    104_058, "Junio":  104_058,
        "Julio": 122_591, "Agosto":  104_058, "Setiembre": 104_058,
        "Octubre": 104_058, "Noviembre": 104_058, "Diciembre": 168_358,
    },
    "3.BIENES Y SERVICIOS": {
        "Enero": 254_138,   "Febrero":   944_140, "Marzo":   1_405_023,
        "Abril": 2_563_008, "Mayo":    2_640_117, "Junio":   2_631_808,
        "Julio": 2_760_267, "Agosto":  2_803_458, "Setiembre": 2_804_461,
        "Octubre": 2_792_513, "Noviembre": 2_892_769, "Diciembre": 3_637_567,
    },
    "4.DONACIONES Y TRANSFERENCIAS": {
        "Enero": 0, "Febrero": 400_000, "Marzo": 0,
        "Abril": 0, "Mayo": 0,          "Junio": 0,
        "Julio": 0, "Agosto": 0,        "Setiembre": 86_914,
        "Octubre": 0, "Noviembre": 0,   "Diciembre": 0,
    },
    "5.OTROS GASTOS": {
        "Enero": 0, "Febrero": 67_398, "Marzo": 1_432,
        "Abril": 0, "Mayo": 0,         "Junio": 0,
        "Julio": 93_295, "Agosto": 0,  "Setiembre": 0,
        "Octubre": 0, "Noviembre": 0,  "Diciembre": 0,
    },
    "6.ADQUISICION DE ACTIVOS NO FINANCIEROS": {
        "Enero": 0,         "Febrero":   279_909, "Marzo":     165_463,
        "Abril": 482_713,   "Mayo":    5_982_148, "Junio":   1_542_038,
        "Julio": 1_381_225, "Agosto":  1_600_025, "Setiembre": 2_162_400,
        "Octubre": 1_994_755, "Noviembre": 1_634_224, "Diciembre": 4_741_390,
    },
}

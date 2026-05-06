# src/config.py
# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN GLOBAL - Tablero Presupuestal SIAF v2.0
# Integración sin breaking changes con config existente
# ═══════════════════════════════════════════════════════════════════════════

import streamlit as st
from datetime import datetime

# ─ CONSTANTES EXISTENTES (mantener compatibilidad) ─────────────────────
# Si tu config.py actual tiene otras constantes, NO las reemplaces
# Solo agrega las nuevas que faltan

# Meses en español (probablemente ya lo tenías)
MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Setiembre", "Octubre", "Noviembre", "Diciembre"
]

MESES_ABREV = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
               "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]

# ═══════════════════════════════════════════════════════════════════════════
# NUEVA SECCIÓN: PALETA TREASURY VAULT (v2.0)
# ═══════════════════════════════════════════════════════════════════════════

PALETA = {
    # Neutrales tintados zinc (no gris puro)
    "bg_primary":      "#FAFAFA",  # fondo principal modo claro
    "bg_secondary":    "#F4F4F5",  # superficies (cards, panels)
    "bg_tertiary":     "#E4E4E7",  # bordes suaves
    "bg_dark_primary": "#09090B",  # fondo principal modo oscuro
    "bg_dark_secondary": "#18181B",
    "bg_dark_tertiary":  "#27272A",

    "text_primary":   "#18181B",   # texto principal claro
    "text_secondary": "#52525B",   # texto secundario
    "text_muted":     "#71717A",   # texto terciario
    "text_dark_primary":   "#FAFAFA",
    "text_dark_secondary": "#A1A1AA",

    # Colores semánticos
    "brand":      "#1D9E75",  # Verde Treasury
    "brand_dark": "#0F6E56",
    "brand_light": "#5DCAA5",
    "brand_50":   "#E1F5EE",

    "info":       "#185FA5",  # Azul confianza
    "info_dark":  "#0C447C",
    "info_light": "#85B7EB",
    "info_50":    "#E6F1FB",

    "warning":      "#BA7517",  # Ámbar precaución
    "warning_dark": "#854F0B",
    "warning_50":   "#FAEEDA",

    "danger":      "#A32D2D",  # Rojo crítico
    "danger_dark": "#791F1F",
    "danger_50":   "#FCEBEB",

    "accent":     "#D85A30",  # Coral para comparativos
    "accent_dark": "#993C1D",
}

# ═══════════════════════════════════════════════════════════════════════════
# COLORES POR GENÉRICA (rampa única teal)
# ═══════════════════════════════════════════════════════════════════════════

COLORES_GENERICAS = [
    "#04342C",  # 1. Personal
    "#085041",  # 2. Pensiones
    "#0F6E56",  # 3. Bienes y servicios
    "#1D9E75",  # 4. Donaciones
    "#5DCAA5",  # 5. Otros gastos
    "#9FE1CB",  # 6. Adquisición activos
]

COLOR_POR_GENERICA = {
    "1.PERSONAL Y OBLIGACIONES SOCIALES": "#04342C",
    "2.PENSIONES Y OTRAS PRESTACIONES SOCIALES": "#085041",
    "3.BIENES Y SERVICIOS": "#0F6E56",
    "4.DONACIONES Y TRANSFERENCIAS": "#1D9E75",
    "5.OTROS GASTOS": "#5DCAA5",
    "6.ADQUISICION DE ACTIVOS NO FINANCIEROS": "#9FE1CB",
}

# ═══════════════════════════════════════════════════════════════════════════
# UMBRALES DE EJECUCIÓN (DGPP-MEF)
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
# PATRONES PARA DETECTAR COLUMNAS (v2.0)
# ═══════════════════════════════════════════════════════════════════════════
# Estos patrones se usan en data_processor.py para detectar automáticamente
# las columnas del Excel, aunque tengan nombres ligeramente diferentes

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
# PROGRAMACIÓN PRECARGADA (si la tienes)
# ═══════════════════════════════════════════════════════════════════════════
# Reemplaza esto con tus datos reales de IPEN 2026

PROGRAMACION_PRECARGADA = {
    "1.PERSONAL Y OBLIGACIONES SOCIALES": {
        "Enero": 8_500_000,
        "Febrero": 8_500_000,
        "Marzo": 8_500_000,
        "Abril": 8_500_000,
        "Mayo": 8_500_000,
        "Junio": 8_500_000,
        "Julio": 8_500_000,
        "Agosto": 8_500_000,
        "Setiembre": 8_500_000,
        "Octubre": 8_500_000,
        "Noviembre": 8_500_000,
        "Diciembre": 8_500_000,
    },
    "2.PENSIONES Y OTRAS PRESTACIONES SOCIALES": {
        "Enero": 2_000_000,
        "Febrero": 2_000_000,
        "Marzo": 2_000_000,
        "Abril": 2_000_000,
        "Mayo": 2_000_000,
        "Junio": 2_000_000,
        "Julio": 2_000_000,
        "Agosto": 2_000_000,
        "Setiembre": 2_000_000,
        "Octubre": 2_000_000,
        "Noviembre": 2_000_000,
        "Diciembre": 2_000_000,
    },
    "3.BIENES Y SERVICIOS": {
        "Enero": 4_500_000,
        "Febrero": 4_500_000,
        "Marzo": 4_500_000,
        "Abril": 4_500_000,
        "Mayo": 4_500_000,
        "Junio": 4_500_000,
        "Julio": 4_500_000,
        "Agosto": 4_500_000,
        "Setiembre": 4_500_000,
        "Octubre": 4_500_000,
        "Noviembre": 4_500_000,
        "Diciembre": 4_500_000,
    },
    "4.DONACIONES Y TRANSFERENCIAS": {
        "Enero": 1_500_000,
        "Febrero": 1_500_000,
        "Marzo": 1_500_000,
        "Abril": 1_500_000,
        "Mayo": 1_500_000,
        "Junio": 1_500_000,
        "Julio": 1_500_000,
        "Agosto": 1_500_000,
        "Setiembre": 1_500_000,
        "Octubre": 1_500_000,
        "Noviembre": 1_500_000,
        "Diciembre": 1_500_000,
    },
    "5.OTROS GASTOS": {
        "Enero": 3_000_000,
        "Febrero": 3_000_000,
        "Marzo": 3_000_000,
        "Abril": 3_000_000,
        "Mayo": 3_000_000,
        "Junio": 3_000_000,
        "Julio": 3_000_000,
        "Agosto": 3_000_000,
        "Setiembre": 3_000_000,
        "Octubre": 3_000_000,
        "Noviembre": 3_000_000,
        "Diciembre": 3_000_000,
    },
    "6.ADQUISICION DE ACTIVOS NO FINANCIEROS": {
        "Enero": 500_000,
        "Febrero": 500_000,
        "Marzo": 500_000,
        "Abril": 500_000,
        "Mayo": 500_000,
        "Junio": 500_000,
        "Julio": 500_000,
        "Agosto": 500_000,
        "Setiembre": 500_000,
        "Octubre": 500_000,
        "Noviembre": 500_000,
        "Diciembre": 500_000,
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE STREAMLIT
# ═══════════════════════════════════════════════════════════════════════════

INSTITUCION = {
    "nombre": "IPEN",
    "nombre_completo": "Instituto Peruano de Energía Nuclear",
    "logo_url": "https://www.ipen.gob.pe/templates/ipen/images/logo-ipen.png",
    "ejercicio_fiscal": 2026,
}

# ═══════════════════════════════════════════════════════════════════════════
# RUTAS DE CARPETAS
# ═══════════════════════════════════════════════════════════════════════════

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESPALDO_DATA_DIR = os.path.join(PROJECT_ROOT, "Respaldo_Data")
REPORTES_DIR = os.path.join(RESPALDO_DATA_DIR, "reportes")
PROG_JSON_PATH = os.path.join(RESPALDO_DATA_DIR, "programacion.json")

# Crear carpetas si no existen
os.makedirs(REPORTES_DIR, exist_ok=True)

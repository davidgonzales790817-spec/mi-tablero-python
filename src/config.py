# config.py
import plotly.express as px

# Configuración de la página
PAGE_CONFIG = {
    "page_title": "Tablero Presupuestal",
    "layout": "wide"
}

# Constantes
MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

CARPETA_RESPALDO = "Respaldo_Data"
LOGO_URL = "https://www.ipen.gob.pe/templates/ipen/images/logo-ipen.png"

# Colores para gráficos
COLORES_GAUGE = {
    "certificado": "#1f77b4",
    "compromiso": "#ff7f0e",
    "devengado": "#2ca02c"
}

COLORES_GENERICAS = px.colors.qualitative.Set2

# Patrones de búsqueda para columnas
PATRONES_DEVENGADO = [
    r'mto_devenga_\d{2}',
    r'devengado',
    r'monto_devengado',
    r'mes_\d{2}'
]

PATRONES_EXCLUIR = ['mto_pim', 'pim', 'mto_certificado', 'certificado', 
                    'mto_compro_anual', 'compromiso', 'total', 'año', 'ano']

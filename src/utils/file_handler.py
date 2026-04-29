# src/utils/file_handler.py
# ─────────────────────────────────────────────────────────────────────────────
# Gestión de archivos Excel SIAF — Versión optimizada para Streamlit Cloud
# ─────────────────────────────────────────────────────────────────────────────
#
# CAMBIOS PARA STREAMLIT CLOUD:
# - Los archivos se leen directamente en memoria (sin guardar en disco)
# - No hay persistencia entre sesiones (normal para Fase 0)
# - Session_state almacena los DataFrames durante la sesión actual
#
# ─────────────────────────────────────────────────────────────────────────────

import os
import pandas as pd
import streamlit as st
from config import CARPETA_DATA


# ── Funciones auxiliares (mantener para compatibilidad con versión local) ─────

def listar_archivos_repo() -> list[str]:
    """Devuelve los archivos Excel disponibles en la carpeta de datos."""
    os.makedirs(CARPETA_DATA, exist_ok=True)
    return sorted([
        f for f in os.listdir(CARPETA_DATA)
        if f.lower().endswith((".xls", ".xlsx"))
    ])


def guardar_archivo_repo(archivo_up) -> str:
    """Guarda un archivo subido por el usuario en el repositorio local."""
    os.makedirs(CARPETA_DATA, exist_ok=True)
    ruta = os.path.join(CARPETA_DATA, archivo_up.name)
    with open(ruta, "wb") as f:
        f.write(archivo_up.getbuffer())
    return ruta


def eliminar_archivo_repo(nombre: str) -> bool:
    """Elimina un archivo del repositorio local."""
    ruta = os.path.join(CARPETA_DATA, nombre)
    if os.path.exists(ruta):
        os.remove(ruta)
        return True
    return False


def cargar_excel(ruta: str) -> pd.DataFrame | None:
    """
    Carga un archivo Excel detectando automáticamente el motor correcto.
    - .xls  → xlrd
    - .xlsx → openpyxl
    """
    try:
        engine = "xlrd" if ruta.lower().endswith(".xls") else "openpyxl"
        return pd.read_excel(ruta, engine=engine)
    except Exception as e:
        st.error(f"❌ Error al leer el archivo: {e}")
        return None


# ── Widget sidebar — OPTIMIZADO PARA STREAMLIT CLOUD ────────────────────────

def widget_carga_archivo() -> str | None:
    """
    Muestra los controles de carga de archivo en la barra lateral.
    
    IMPORTANTE: En Streamlit Cloud, los archivos NO se guardan en disco.
    Se procesan directamente en memoria usando session_state.
    
    FLUJO:
    1. Usuario sube Excel
    2. Se lee inmediatamente a DataFrame
    3. Se almacena en session_state (memoria RAM)
    4. Se procesa y se muestran gráficos
    5. Al recargar la página, se pierden datos (normal para Fase 0)
    """
    st.sidebar.header("📁 Archivo de Datos")

    # En Streamlit Cloud, no listamos archivos del repo (no persisten)
    # Solo mostramos la opción de subir un nuevo archivo
    
    archivo = st.sidebar.file_uploader(
        "Seleccionar Excel (.xls / .xlsx)",
        type=["xls", "xlsx"],
        help="El archivo se procesa en memoria durante tu sesión",
        key="file_uploader_main",
    )
    
    if archivo is not None:
        # Leer el archivo directamente sin guardar en disco
        try:
            # Detectar el motor correcto según la extensión
            engine = "xlrd" if archivo.name.lower().endswith(".xls") else "openpyxl"
            
            # Leer el Excel a un DataFrame (en memoria)
            df = pd.read_excel(archivo, engine=engine)
            
            # Guardar en session_state (persiste durante esta sesión)
            st.session_state.df_raw = df
            st.session_state.archivo_activo = archivo.name
            st.session_state.df_procesado = None
            st.session_state.cols_devengado = []
            
            # Mostrar mensaje de éxito
            st.sidebar.success(f"✅ Cargado: `{archivo.name}`")
            st.rerun()
            
        except Exception as e:
            st.sidebar.error(f"❌ Error al leer el archivo:\n{str(e)}")
            return None

    return st.session_state.get("archivo_activo", None)

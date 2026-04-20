# src/utils/file_handler.py
# ─────────────────────────────────────────────────────────────────────────────
# Gestión del repositorio local de archivos Excel SIAF
# ─────────────────────────────────────────────────────────────────────────────

import os
import pandas as pd
import streamlit as st
from config import CARPETA_DATA


# ── Repositorio local ─────────────────────────────────────────────────────────

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


# ── Carga de Excel ────────────────────────────────────────────────────────────

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


# ── Widget sidebar ────────────────────────────────────────────────────────────

def widget_carga_archivo() -> str | None:
    """
    Muestra los controles de carga de archivo en la barra lateral
    y devuelve la ruta del archivo activo, o None si no hay ninguno.
    """
    st.sidebar.header("📁 Archivo de Datos")
    archivos_repo = listar_archivos_repo()

    tab_upload, tab_repo = st.sidebar.tabs(["⬆️ Subir nuevo", "📂 Repositorio"])

    with tab_upload:
        archivo = st.file_uploader(
            "Seleccionar Excel (.xls / .xlsx)",
            type=["xls", "xlsx"],
            help="El archivo se guarda automáticamente en Respaldo_Data/",
            key="file_uploader_main",
        )
        if archivo:
            ruta = guardar_archivo_repo(archivo)
            st.success(f"Guardado: `{archivo.name}`")
            # Forzar recarga del procesamiento
            st.session_state.archivo_activo = ruta
            st.session_state.df_raw = None
            st.rerun()

    with tab_repo:
        if archivos_repo:
            sel = st.selectbox("Archivos disponibles:", archivos_repo, key="sel_repo")
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("📂 Cargar", use_container_width=True):
                    st.session_state.archivo_activo = os.path.join(CARPETA_DATA, sel)
                    st.session_state.df_raw = None
                    st.rerun()
            with col2:
                if st.button("🗑️", help="Eliminar archivo", use_container_width=True):
                    if eliminar_archivo_repo(sel):
                        st.success("Eliminado.")
                        st.rerun()
        else:
            st.info("No hay archivos en el repositorio aún.")

    return st.session_state.get("archivo_activo", None)

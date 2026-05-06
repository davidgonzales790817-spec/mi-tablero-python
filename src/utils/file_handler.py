# src/utils/file_handler.py
# ─────────────────────────────────────────────────────────────────────────────
# Gestión de archivos - Versión COMPATIBLE CON APP.PY
# ─────────────────────────────────────────────────────────────────────────────

import os
import pandas as pd
import streamlit as st
from config import CARPETA_DATA


class FileHandler:
    """Maneja la carga de archivos Excel SIAF."""
    
    def __init__(self):
        """Inicializa el manejador de archivos."""
        os.makedirs(CARPETA_DATA, exist_ok=True)
    
    def cargar_excel(self, archivo_subido) -> pd.DataFrame:
        """
        Carga un archivo Excel subido por el usuario.
        
        Args:
            archivo_subido: Objeto de archivo de Streamlit (file_uploader)
        
        Returns:
            DataFrame con los datos del Excel
        """
        try:
            # Detectar el motor según la extensión
            engine = "xlrd" if archivo_subido.name.lower().endswith(".xls") else "openpyxl"
            
            # Leer Excel directamente en memoria
            df = pd.read_excel(archivo_subido, engine=engine)
            
            return df
        
        except Exception as e:
            st.error(f"Error al leer archivo: {e}")
            return None
    
    def listar_archivos(self) -> list[str]:
        """Devuelve lista de archivos Excel en CARPETA_DATA."""
        try:
            return sorted([
                f for f in os.listdir(CARPETA_DATA)
                if f.lower().endswith((".xls", ".xlsx"))
            ])
        except:
            return []
    
    def guardar_archivo(self, archivo_subido) -> str:
        """Guarda un archivo subido en disco."""
        try:
            ruta = os.path.join(CARPETA_DATA, archivo_subido.name)
            with open(ruta, "wb") as f:
                f.write(archivo_subido.getbuffer())
            return ruta
        except Exception as e:
            st.error(f"Error guardando archivo: {e}")
            return None
    
    def eliminar_archivo(self, nombre: str) -> bool:
        """Elimina un archivo de CARPETA_DATA."""
        try:
            ruta = os.path.join(CARPETA_DATA, nombre)
            if os.path.exists(ruta):
                os.remove(ruta)
                return True
            return False
        except:
            return False


# ─ Funciones auxiliares (para compatibilidad con código existente) ─

def widget_carga_archivo() -> str | None:
    """
    Muestra los controles de carga de archivo en la barra lateral.
    Para compatibilidad con código existente.
    """
    st.sidebar.header("📁 Archivo de Datos")

    archivo = st.sidebar.file_uploader(
        "Seleccionar Excel (.xls / .xlsx)",
        type=["xls", "xlsx"],
        help="El archivo se procesa en memoria durante tu sesión",
        key="file_uploader_main",
    )
    
    if archivo is not None:
        try:
            engine = "xlrd" if archivo.name.lower().endswith(".xls") else "openpyxl"
            df = pd.read_excel(archivo, engine=engine)
            
            st.session_state.df_raw = df
            st.session_state.archivo_activo = archivo.name
            
            st.sidebar.success(f"✅ Cargado: `{archivo.name}`")
            
        except Exception as e:
            st.sidebar.error(f"❌ Error: {str(e)}")
            return None

    return st.session_state.get("archivo_activo", None)


def cargar_excel(ruta: str) -> pd.DataFrame | None:
    """Para compatibilidad: carga un Excel desde una ruta."""
    try:
        engine = "xlrd" if ruta.lower().endswith(".xls") else "openpyxl"
        return pd.read_excel(ruta, engine=engine)
    except Exception as e:
        st.error(f"Error al leer: {e}")
        return None


def listar_archivos_repo() -> list[str]:
    """Para compatibilidad: lista archivos en CARPETA_DATA."""
    os.makedirs(CARPETA_DATA, exist_ok=True)
    return sorted([
        f for f in os.listdir(CARPETA_DATA)
        if f.lower().endswith((".xls", ".xlsx"))
    ])


def guardar_archivo_repo(archivo_up) -> str:
    """Para compatibilidad: guarda un archivo."""
    os.makedirs(CARPETA_DATA, exist_ok=True)
    ruta = os.path.join(CARPETA_DATA, archivo_up.name)
    with open(ruta, "wb") as f:
        f.write(archivo_up.getbuffer())
    return ruta


def eliminar_archivo_repo(nombre: str) -> bool:
    """Para compatibilidad: elimina un archivo."""
    ruta = os.path.join(CARPETA_DATA, nombre)
    if os.path.exists(ruta):
        os.remove(ruta)
        return True
    return False

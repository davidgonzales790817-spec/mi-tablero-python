# utils/file_handler.py
import os
import streamlit as st
from ..config import CARPETA_RESPALDO

def guardar_archivo_respaldo(archivo):
    """Guarda el archivo cargado en la carpeta de respaldo"""
    os.makedirs(CARPETA_RESPALDO, exist_ok=True)
    ruta_archivo = os.path.join(CARPETA_RESPALDO, archivo.name)
    with open(ruta_archivo, "wb") as f:
        f.write(archivo.getbuffer())
    return ruta_archivo

def cargar_archivo_excel():
    """Componente de carga de archivo en la barra lateral"""
    st.sidebar.header("Cargar archivo Excel")
    archivo = st.sidebar.file_uploader("Seleccionar archivo Excel", type=["xls", "xlsx"])
    return archivo

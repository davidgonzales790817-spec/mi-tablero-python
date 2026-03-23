# components/sidebar.py
import streamlit as st
from ..config import LOGO_URL

def mostrar_logo():
    st.sidebar.image(LOGO_URL, width=250)

def crear_filtros(df):
    """Crea los filtros en la barra lateral y devuelve el dataframe filtrado"""
    st.sidebar.header("Filtros")

    # Filtro de genérica
    genericas = ["Todas"] + sorted(df["generica"].unique().tolist())
    filtro_generica = st.sidebar.selectbox("Filtrar por Genérica", genericas)

    df_filtrado = df.copy()
    if filtro_generica != "Todas":
        df_filtrado = df_filtrado[df_filtrado["generica"] == filtro_generica]

    # Filtro de unidad ejecutora (si existe)
    if "unidad_ejecutora" in df.columns:
        ues = ["Todas"] + sorted(df["unidad_ejecutora"].dropna().unique())
        filtro_ue = st.sidebar.selectbox("Filtrar por Unidad Ejecutora", ues)
        if filtro_ue != "Todas":
            df_filtrado = df_filtrado[df_filtrado["unidad_ejecutora"] == filtro_ue]

    return df_filtrado, filtro_generica

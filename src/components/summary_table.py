# components/summary_table.py
import streamlit as st
from components.drilldown_detail import crear_tabla_con_drilldown

def crear_tabla_resumen(df_filtrado):
    """
    Crea y muestra la tabla resumen por genérica con funcionalidad de drilldown
    """
    return crear_tabla_con_drilldown(df_filtrado)

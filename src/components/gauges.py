# components/gauges.py
import streamlit as st
import plotly.graph_objects as go
from config import COLORES_GAUGE

def crear_gauge(valor, total, titulo, color):
    porcentaje = round(valor / total * 100 if total > 0 else 0, 2)
    return go.Indicator(
        mode="gauge+number",
        value=porcentaje,
        number={"suffix": "%", "font": {"size": 24}},
        title={"text": f"<b>{titulo}</b><br><span style='font-size:0.8em'>S/ {valor:,.0f}</span>",
               "font": {"size": 16}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "darkgray"},
            "bar": {"color": color},
            "bgcolor": "white",
            "borderwidth": 1,
            "bordercolor": "gray",
            "steps": [
                {"range": [0, 50], "color": "#f2f2f2"},
                {"range": [50, 80], "color": "#d9ead3"},
                {"range": [80, 100], "color": "#b6d7a8"},
            ]
        }
    )

def mostrar_indicadores(pim_total, certificado_total, compromiso_total, devengado_total):
    st.subheader("Indicadores de Ejecución Presupuestal")

    col1, col2, col3 = st.columns(3)

    with col1:
        fig_cert = go.Figure(crear_gauge(certificado_total, pim_total, "% Certificado", COLORES_GAUGE["certificado"]))
        fig_cert.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30))
        st.plotly_chart(fig_cert, use_container_width=True)

    with col2:
        fig_comp = go.Figure(crear_gauge(compromiso_total, pim_total, "% Compromiso", COLORES_GAUGE["compromiso"]))
        fig_comp.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30))
        st.plotly_chart(fig_comp, use_container_width=True)

    with col3:
        fig_dev = go.Figure(crear_gauge(devengado_total, pim_total, "% Devengado", COLORES_GAUGE["devengado"]))
        fig_dev.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30))
        st.plotly_chart(fig_dev, use_container_width=True)

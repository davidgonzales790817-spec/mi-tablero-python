import streamlit as st
import plotly.graph_objects as go

def obtener_color_semaforo(porcentaje):
    """Define la lógica del semáforo"""
    if porcentaje < 50:
        return "#FF4B4B"  # Rojo (Bajo)
    elif porcentaje < 80:
        return "#FFD700"  # Amarillo/Oro (Medio)
    else:
        return "#238636"  # Verde (Alto)

def crear_gauge(valor, total, titulo):
    # 1. Calculamos el porcentaje
    porcentaje = round(valor / total * 100 if total > 0 else 0, 2)
    
    # 2. Obtenemos el color dinámico basado en el valor
    color_dinamico = obtener_color_semaforo(porcentaje)
    
    return go.Indicator(
        mode="gauge+number",
        value=porcentaje,
        number={"suffix": "%", "font": {"size": 26}, "valueformat": ".1f"},
        title={
            "text": f"<b>{titulo}</b><br><span style='font-size:0.8em; color:gray'>S/ {valor:,.0f}</span>",
            "font": {"size": 18}
        },
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "gray"},
            "bar": {"color": color_dinamico}, # <--- AQUÍ SE APLICA EL SEMÁFORO
            "bgcolor": "white",
            "borderwidth": 1,
            "bordercolor": "silver",
            "steps": [
                {"range": [0, 100], "color": "#f0f2f6"} # Fondo neutro para que resalte la barra
            ]
        }
    )

def mostrar_indicadores(pim_total, certificado_total, compromiso_total, devengado_total):
    st.subheader("Indicadores de Ejecución Presupuestal")

    col1, col2, col3 = st.columns(3)

    # IMPORTANTE: Eliminamos 'color' de los argumentos porque ahora es dinámico
    with col1:
        fig_cert = go.Figure(crear_gauge(certificado_total, pim_total, "% Certificado"))
        fig_cert.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30))
        st.plotly_chart(fig_cert, use_container_width=True)

    with col2:
        fig_comp = go.Figure(crear_gauge(compromiso_total, pim_total, "% Compromiso"))
        fig_comp.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30))
        st.plotly_chart(fig_comp, use_container_width=True)

    with col3:
        fig_dev = go.Figure(crear_gauge(devengado_total, pim_total, "% Devengado"))
        fig_dev.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30))
        st.plotly_chart(fig_dev, use_container_width=True)

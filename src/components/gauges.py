import streamlit as st
import plotly.graph_objects as go

def obtener_color_semaforo(porcentaje):
    """Retorna el color según el nivel de ejecución."""
    if porcentaje < 50:
        return "#E74C3C"  # Rojo (Bajo)
    elif porcentaje < 80:
        return "#F1C40F"  # Amarillo/Ámbar (Medio)
    else:
        return "#27AE60"  # Verde (Alto)

def crear_gauge(valor, total, titulo):
    # Calcular porcentaje
    porcentaje = round(valor / total * 100 if total > 0 else 0, 2)
    
    # Obtener color dinámico
    color_barra = obtener_color_semaforo(porcentaje)
    
    return go.Indicator(
        mode="gauge+number",
        value=porcentaje,
        number={"suffix": "%", "font": {"size": 24}, "valueformat": ".2f"},
        title={
            "text": f"<b>{titulo}</b><br><span style='font-size:0.8em; color:gray'>S/ {valor:,.0f}</span>",
            "font": {"size": 16}
        },
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "gray"},
            "bar": {"color": color_barra}, # Aquí se aplica el color tipo semáforo
            "bgcolor": "white",
            "borderwidth": 1,
            "bordercolor": "silver",
            "steps": [
                {"range": [0, 50], "color": "#FDEDEC"},   # Fondo rojizo muy claro
                {"range": [50, 80], "color": "#FEF9E7"},  # Fondo amarillento muy claro
                {"range": [80, 100], "color": "#EAFAF1"}, # Fondo verdoso muy claro
            ]
        }
    )

def mostrar_indicadores(pim_total, certificado_total, compromiso_total, devengado_total):
    st.subheader("Indicadores de Ejecución Presupuestal")

    col1, col2, col3 = st.columns(3)

    # Nota: Eliminamos COLORES_GAUGE de los parámetros ya que el color ahora es dinámico
    with col1:
        fig_cert = go.Figure(crear_gauge(certificado_total, pim_total, "% Certificado"))
        fig_cert.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_cert, use_container_width=True)

    with col2:
        fig_comp = go.Figure(crear_gauge(compromiso_total, pim_total, "% Compromiso"))
        fig_comp.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_comp, use_container_width=True)

    with col3:
        fig_dev = go.Figure(crear_gauge(devengado_total, pim_total, "% Devengado"))
        fig_dev.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_dev, use_container_width=True)

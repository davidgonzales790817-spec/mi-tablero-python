import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

def obtener_config_meta():
    """Calcula la meta basada en el mes anterior al actual."""
    mes_actual = datetime.now().month
    # Si estamos en enero (1), la meta es 0 o se toma diciembre (12)
    mes_referencia = mes_actual - 1 if mes_actual > 1 else 0
    meta = (mes_referencia / 12) * 100
    return meta, mes_referencia

def crear_gauge(valor, total, titulo, es_devengado=False):
    porcentaje = round(valor / total * 100 if total > 0 else 0, 2)
    
    # --- LÓGICA DE COLOR ---
    if es_devengado:
        meta_teorica, _ = obtener_config_meta()
        margen_amarillo = meta_teorica - 5
        
        if porcentaje >= meta_teorica:
            color_barra = "#238636"  # Verde
        elif porcentaje >= margen_amarillo:
            color_barra = "#FFD700"  # Amarillo
        else:
            color_barra = "#FF4B4B"  # Rojo
    else:
        # Lógica estándar para Certificado y Compromiso
        if porcentaje < 50: color_barra = "#FF4B4B"
        elif porcentaje < 80: color_barra = "#FFD700"
        else: color_barra = "#238636"

    # --- CONSTRUCCIÓN DEL GRÁFICO ---
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=porcentaje,
        number={"suffix": "%", "font": {"size": 26}},
        title={
            "text": f"<b>{titulo}</b><br><span style='font-size:0.8em; color:gray'>S/ {valor:,.0f}</span>",
            "font": {"size": 18}
        },
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "gray"},
            "bar": {"color": color_barra},
            "bgcolor": "white",
            "borderwidth": 1,
            "bordercolor": "silver",
            # Añadimos el umbral (meta) solo si es devengado
            "threshold": {
                "line": {"color": "black", "width": 4}, # Línea negra gruesa
                "thickness": 0.8, # Grosor de la marca
                "value": obtener_config_meta()[0] if es_devengado else None
            } if es_devengado else None,
            "steps": [{"range": [0, 100], "color": "#f0f2f6"}]
        }
    ))

    fig.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30))
    return fig

def mostrar_indicadores(pim_total, certificado_total, compromiso_total, devengado_total):
    st.subheader("Indicadores de Ejecución Presupuestal")
    
    # Información de la meta para el usuario
    meta_val, mes_num = obtener_config_meta()
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    if mes_num > 0:
        st.info(f"📊 **Meta al mes de {meses[mes_num-1]}: {meta_val:.1f}%** (Línea negra en Devengado)")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.plotly_chart(crear_gauge(certificado_total, pim_total, "% Certificado"), use_container_width=True)

    with col2:
        st.plotly_chart(crear_gauge(compromiso_total, pim_total, "% Compromiso"), use_container_width=True)

    with col3:
        # Activamos el flag es_devengado=True
        st.plotly_chart(crear_gauge(devengado_total, pim_total, "% Devengado", es_devengado=True), use_container_width=True)

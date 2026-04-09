import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

def obtener_color_dinamico(porcentaje, tipo_indicador):
    """
    Lógica de semáforo dinámica.
    - Para 'devengado': Basado en el mes anterior / 12.
    - Para otros: Lógica estándar (o puedes adaptarla).
    """
    if tipo_indicador == "devengado":
        # 1. Calculamos la meta basada en el mes anterior
        mes_actual = datetime.now().month
        # Si es enero (1), el mes anterior es 12 (del año pasado) o 0 para inicio de año
        mes_referencia = mes_actual - 1 if mes_actual > 1 else 1 
        
        meta_teorica = (mes_referencia / 12) * 100
        margen_amarillo = meta_teorica - 5

        if porcentaje >= meta_teorica:
            return "#238636"  # Verde (Cumple meta mensual)
        elif porcentaje >= margen_amarillo:
            return "#FFD700"  # Amarillo (Cerca de la meta)
        else:
            return "#FF4B4B"  # Rojo (Retraso significativo)
    
    else:
        # Lógica estándar para Certificado y Compromiso (puedes ajustarla)
        if porcentaje < 50: return "#FF4B4B"
        elif porcentaje < 80: return "#FFD700"
        else: return "#238636"

def crear_gauge(valor, total, titulo, tipo_indicador="general"):
    porcentaje = round(valor / total * 100 if total > 0 else 0, 2)
    
    # Aplicamos la nueva lógica dinámica
    color_barra = obtener_color_dinamico(porcentaje, tipo_indicador)
    
    # Opcional: Calcular la meta para mostrarla en el gráfico
    mes_ref = datetime.now().month - 1
    meta_val = (mes_ref / 12) * 100 if tipo_indicador == "devengado" else None

    fig_dict = {
        "mode": "gauge+number",
        "value": porcentaje,
        "number": {"suffix": "%", "font": {"size": 24}},
        "title": {
            "text": f"<b>{titulo}</b><br><span style='font-size:0.8em; color:gray'>S/ {valor:,.0f}</span>",
            "font": {"size": 16}
        },
        "gauge": {
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": color_barra},
            "bgcolor": "white",
            "borderwidth": 1,
            "bordercolor": "silver",
            "steps": [
                {"range": [0, 100], "color": "#f0f2f6"}
            ]
        }
    }

    # Si es devengado, añadimos una línea (threshold) que marque la meta teórica
    if meta_val:
        fig_dict["gauge"]["threshold"] = {
            "line": {"color": "black", "width": 3},
            "thickness": 0.75,
            "value": meta_val
        }

    return go.Indicator(**fig_dict)

def mostrar_indicadores(pim_total, certificado_total, compromiso_total, devengado_total):
    st.subheader("Indicadores de Ejecución Presupuestal")
    
    # Texto explicativo de la meta actual
    mes_nombre = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    mes_ref = datetime.now().month - 1
    meta_actual = (mes_ref / 12) * 100
    
    st.caption(f"📅 Meta esperada al cierre de **{mes_nombre[mes_ref-1]}**: **{meta_actual:.1f}%**")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.plotly_chart(go.Figure(crear_gauge(certificado_total, pim_total, "% Certificado")), use_container_width=True)

    with col2:
        st.plotly_chart(go.Figure(crear_gauge(compromiso_total, pim_total, "% Compromiso")), use_container_width=True)

    with col3:
        # Aquí pasamos el tipo "devengado" para activar la fórmula especial
        fig_dev = go.Figure(crear_gauge(devengado_total, pim_total, "% Devengado", tipo_indicador="devengado"))
        fig_dev.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30))
        st.plotly_chart(fig_dev, use_container_width=True)

# src/components/monthly_chart.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from config import MESES, COLORES_GENERICAS

def _fmt_soles(valor):
    """Formatea un valor numérico como soles peruanos."""
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return "S/ 0"
    try:
        return f"S/ {valor:,.0f}".replace(",", ".")
    except:
        return f"S/ {valor}"

def _determinar_escala(max_val):
    """Determina la escala de visualización."""
    if max_val > 1e6:
        return 1e6, "Millones S/"
    if max_val > 1e3:
        return 1e3, "Miles S/"
    return 1, "Soles"

def obtener_programacion_desde_session():
    """Obtiene el DataFrame de programación desde session_state."""
    if "programacion_mensual" in st.session_state:
        df_prog = st.session_state.programacion_mensual
        if df_prog is not None and not df_prog.empty:
            return df_prog
    return None

def preparar_datos_grafico(df_filtrado, columnas_devengado):
    """Prepara datos para el gráfico."""
    genericas = sorted(df_filtrado["generica"].unique())
    
    datos = []
    for mes_col in columnas_devengado:
        nombre_mes = mes_col.replace("Devengado_", "").strip()
        if nombre_mes not in MESES:
            continue
        
        fila = {"mes": nombre_mes}
        for gen in genericas:
            valor = df_filtrado[df_filtrado["generica"] == gen][mes_col].sum()
            fila[gen] = valor if not np.isnan(valor) else 0
        datos.append(fila)
    
    # Completar meses faltantes
    meses_existentes = {d["mes"] for d in datos}
    for mes in MESES:
        if mes not in meses_existentes:
            fila = {"mes": mes}
            for gen in genericas:
                fila[gen] = 0
            datos.append(fila)
    
    df = pd.DataFrame(datos)
    df["mes"] = pd.Categorical(df["mes"], categories=MESES, ordered=True)
    df = df.sort_values("mes")
    
    return df.set_index("mes"), genericas

def preparar_programacion_para_grafico(programacion_df, meses):
    """Prepara datos de programación."""
    if programacion_df is None or programacion_df.empty:
        return {mes: 0 for mes in meses}
    
    resultado = {}
    for mes in meses:
        if mes in programacion_df.columns:
            total = programacion_df[mes].sum()
            resultado[mes] = total if not np.isnan(total) else 0
        else:
            resultado[mes] = 0
    return resultado

def crear_grafico_mensual(df_filtrado, columnas_devengado, programacion_df=None):
    """Crea el gráfico mensual."""
    
    # Intentar obtener programación de session_state si no se pasó
    if programacion_df is None or programacion_df.empty:
        programacion_df = obtener_programacion_desde_session()
    
    if df_filtrado.empty:
        st.warning("No hay datos para mostrar")
        return
    
    # Preparar datos
    pivot, genericas = preparar_datos_grafico(df_filtrado, columnas_devengado)
    programacion_por_mes = preparar_programacion_para_grafico(programacion_df, pivot.index.tolist())
    
    # Calcular totales
    totales_mensuales = pivot.sum(axis=1)
    total_devengado = totales_mensuales.sum()
    total_programado = sum(programacion_por_mes.values())
    
    # Determinar escala
    max_val = max(totales_mensuales.max(), total_programado, total_devengado / 6)
    escala, unidad = _determinar_escala(max_val)
    
    # Crear figura
    fig = go.Figure()
    
    # Agregar barras por genérica
    for i, gen in enumerate(genericas):
        color = COLORES_GENERICAS[i % len(COLORES_GENERICAS)]
        valores = pivot[gen] / escala
        
        fig.add_trace(go.Bar(
            x=pivot.index,
            y=valores,
            name=gen,
            marker_color=color,
            text=pivot[gen].apply(lambda x: _fmt_soles(x) if x > 0 else ""),
            textposition="inside",
            textfont_size=9,
            hovertemplate=f"<b>{gen}</b><br>%{{x}}<br>S/ %{{customdata:,.0f}}<extra></extra>",
            customdata=pivot[gen]
        ))
    
    # Agregar línea de programación
    if any(programacion_por_mes.values()):
        prog_vals = [programacion_por_mes.get(mes, 0) / escala for mes in pivot.index]
        
        fig.add_trace(go.Scatter(
            x=pivot.index,
            y=prog_vals,
            mode="lines+markers+text",
            name="🎯 Programación",
            line=dict(color="#E63946", width=3),
            marker=dict(size=10, color="#E63946", symbol="circle"),
            text=[_fmt_soles(programacion_por_mes.get(mes, 0)) for mes in pivot.index],
            textposition="top center",
            textfont=dict(size=10, color="#E63946"),
            hovertemplate="<b>Programación</b><br>%{x}<br>S/ %{customdata:,.0f}<extra></extra>",
            customdata=[programacion_por_mes.get(mes, 0) for mes in pivot.index]
        ))
    
    # Agregar anotaciones de totales mensuales
    for mes, total in totales_mensuales.items():
        if total > 0:
            y_pos = (total / escala) + (max_val / escala * 0.02)
            fig.add_annotation(
                x=mes,
                y=y_pos,
                text=f"<b>{_fmt_soles(total)}</b>",
                showarrow=False,
                font=dict(size=11, color="#2C3E50"),
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#2C3E50",
                borderwidth=1,
                borderpad=3
            )
    
    # Configurar layout
    cumplimiento = (total_devengado / total_programado * 100) if total_programado > 0 else 0
    
    fig.update_layout(
        title=dict(
            text=f"<b>Evolución Mensual del Devengado</b><br>"
                 f"<sub>Total Devengado: {_fmt_soles(total_devengado)} | "
                 f"Total Programado: {_fmt_soles(total_programado)} | "
                 f"Cumplimiento: {cumplimiento:.1f}%</sub>",
            x=0.5,
            font=dict(size=14)
        ),
        xaxis_title="Mes",
        yaxis_title=unidad,
        barmode="stack",
        hovermode="x unified",
        height=550,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.9)"
        ),
        plot_bgcolor="white",
        xaxis=dict(gridcolor="#ececec", tickangle=45),
        yaxis=dict(gridcolor="#ececec"),
        margin=dict(t=100, b=80)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar métricas
    st.markdown("### 📊 Resumen")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Devengado", _fmt_soles(total_devengado))
    with col2:
        st.metric("Total Programado", _fmt_soles(total_programado))
    with col3:
        st.metric("Cumplimiento", f"{cumplimiento:.1f}%")
    with col4:
        st.metric("Promedio Mensual", _fmt_soles(total_devengado / 12))
    
    # Tabla detallada
    with st.expander("📋 Ver tabla detallada", expanded=False):
        tabla = pd.DataFrame({
            "Mes": pivot.index,
            "Devengado Total": totales_mensuales.apply(_fmt_soles),
            "Programación": [programacion_por_mes.get(mes, 0) for mes in pivot.index],
        })
        tabla["Programación"] = tabla["Programación"].apply(_fmt_soles)
        tabla["Diferencia"] = (totales_mensuales - pd.Series(programacion_por_mes)).apply(_fmt_soles)
        
        st.dataframe(tabla, use_container_width=True, hide_index=True)
        
        # Descarga
        csv = pivot.copy()
        csv["TOTAL_MENSUAL"] = totales_mensuales
        csv["PROGRAMACION"] = [programacion_por_mes.get(mes, 0) for mes in pivot.index]
        st.download_button(
            "📥 Descargar CSV",
            csv.to_csv().encode("utf-8"),
            "evolucion_mensual.csv",
            "text/csv"
        )

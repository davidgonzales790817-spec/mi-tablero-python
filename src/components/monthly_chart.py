# components/monthly_chart.py
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from config import MESES, COLORES_GENERICAS

def preparar_datos_grafico(df_filtrado, columnas_devengado):
    """
    Prepara los datos para el gráfico de evolución mensual.
    Ahora incluye todos los meses, incluso si tienen valor cero.
    """
    datos_grafico = []
    genericas_ordenadas = sorted(df_filtrado["generica"].unique())
    
    # Crear un diccionario para acumular montos por genérica y mes
    acumulado = {gen: {mes: 0 for mes in MESES} for gen in genericas_ordenadas}
    
    # Acumular los montos reales
    for generica in genericas_ordenadas:
        df_gen = df_filtrado[df_filtrado["generica"] == generica]
        for mes_col in columnas_devengado:
            nombre_mes = mes_col.replace("Devengado_", "")
            if nombre_mes in MESES:
                monto = df_gen[mes_col].sum()
                acumulado[generica][nombre_mes] += monto
    
    # Convertir a lista de diccionarios para el DataFrame
    for generica in genericas_ordenadas:
        for mes in MESES:
            monto = acumulado[generica][mes]
            datos_grafico.append({
                "generica": generica,
                "mes": mes,
                "monto": monto
            })
    
    df_grafico = pd.DataFrame(datos_grafico)
    
    # Ordenar por mes cronológicamente
    df_grafico["mes"] = pd.Categorical(df_grafico["mes"], categories=MESES, ordered=True)
    df_grafico = df_grafico.sort_values(["mes", "generica"])
    
    return df_grafico, genericas_ordenadas

def determinar_escala(df_grafico):
    """
    Determina la escala adecuada para los montos
    """
    max_monto = df_grafico["monto"].max()
    
    if max_monto > 1e6:
        factor = 1e6
        unidad = "Millones S/"
        formato_total = lambda x: f"S/ {x/1e6:.2f}M"
    elif max_monto > 1e3:
        factor = 1e3
        unidad = "Miles S/"
        formato_total = lambda x: f"S/ {x/1e3:.1f}K"
    else:
        factor = 1
        unidad = "Soles"
        formato_total = lambda x: f"S/ {x:,.0f}"
    
    return factor, unidad, formato_total

def crear_grafico_mensual(df_filtrado, columnas_devengado):
    """
    Crea y muestra el gráfico de evolución mensual
    """
    st.subheader("📈 Evolución del Devengado Mensual por Genérica")
    
    # Preparar datos (ahora incluye todos los meses)
    df_grafico, genericas_ordenadas = preparar_datos_grafico(df_filtrado, columnas_devengado)
    
    if df_grafico.empty:
        st.warning("No hay datos para mostrar en el gráfico")
        return
    
    # Calcular totales por mes (para anotaciones)
    totales_mes = df_grafico.groupby("mes")["monto"].sum().reset_index()
    
    # Determinar escala
    factor, unidad, formato_total = determinar_escala(df_grafico)
    df_grafico["monto_mostrar"] = df_grafico["monto"] / factor
    
    # Crear gráfico
    fig = go.Figure()
    colores = COLORES_GENERICAS
    
    # Agregar barras para cada genérica
    for i, generica in enumerate(genericas_ordenadas):
        df_gen = df_grafico[df_grafico["generica"] == generica]
        if not df_gen.empty:
            fig.add_trace(go.Bar(
                name=generica,
                x=df_gen["mes"],
                y=df_gen["monto_mostrar"],
                text=df_gen["monto"].apply(lambda x: f"S/ {x:,.0f}" if x > 0 else ""),
                textposition='inside',
                textfont_size=10,
                marker_color=colores[i % len(colores)],
                hovertemplate="<b>%{x}</b><br>" +
                              f"Genérica: {generica}<br>" +
                              "Monto: S/ %{customdata:,.0f}<br>" +
                              "<extra></extra>",
                customdata=df_gen["monto"].values,
                legendrank=i
            ))
    
    # Configurar layout
    fig.update_layout(
        barmode='stack',
        title="Evolución Mensual del Gasto por Genérica",
        xaxis_title="Mes",
        yaxis_title=unidad,
        hovermode='x unified',
        legend_title="Genérica",
        showlegend=True,
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Agregar anotaciones de totales (solo si el total > 0)
    for _, row in totales_mes.iterrows():
        mes = row["mes"]
        total = row["monto"]
        
        if total > 0:  # Solo mostrar anotación si hay gasto
            if factor == 1e6:
                y_pos = total / 1e6
            elif factor == 1e3:
                y_pos = total / 1e3
            else:
                y_pos = total
            
            fig.add_annotation(
                x=mes,
                y=y_pos,
                text=f"<b>{formato_total(total)}</b>",
                showarrow=False,
                yshift=15,
                font=dict(size=11, color="black", family="Arial Black"),
                bgcolor="rgba(255, 255, 255, 0.9)",
                bordercolor="black",
                borderwidth=1,
                borderpad=4
            )
    
    # Configurar eje X para mostrar TODOS los meses
    fig.update_xaxes(
        tickangle=45, 
        gridcolor='lightgray',
        tickmode='array',
        tickvals=MESES,
        ticktext=MESES
    )
    fig.update_yaxes(gridcolor='lightgray')
    
    # Mostrar gráfico
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar datos detallados (opcional)
    with st.expander("Ver datos detallados"):
        # Tabla pivotada
        pivot_df = df_grafico.pivot_table(
            values='monto',
            index='generica',
            columns='mes',
            aggfunc='sum',
            fill_value=0
        )
        
        # Asegurar que todos los meses aparezcan en la tabla
        for mes in MESES:
            if mes not in pivot_df.columns:
                pivot_df[mes] = 0
        
        # Reordenar columnas
        pivot_df = pivot_df[MESES]
        
        # Ordenar filas
        pivot_df = pivot_df.reindex(genericas_ordenadas)
        
        # Formatear
        pivot_display = pivot_df.copy()
        for col in pivot_display.columns:
            pivot_display[col] = pivot_display[col].apply(lambda x: f"S/ {x:,.0f}")
        
        st.dataframe(pivot_display, use_container_width=True)
        
        # Botón de descarga
        csv = df_grafico[["generica", "mes", "monto"]].to_csv(index=False)
        st.download_button(
            "📥 Descargar datos CSV",
            csv,
            "evolucion_mensual.csv",
            "text/csv"
        )

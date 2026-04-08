# components/monthly_chart.py
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from config import MESES, COLORES_GENERICAS

def preparar_datos_grafico(df_filtrado, columnas_devengado):
    datos_grafico = []
    genericas_ordenadas = sorted(df_filtrado["generica"].unique())

    for generica in genericas_ordenadas:
        df_gen = df_filtrado[df_filtrado["generica"] == generica]
        for mes in columnas_devengado:
            monto = df_gen[mes].sum()
            if monto > 0:
                datos_grafico.append({
                    "generica": generica,
                    "mes": mes.replace("Devengado_", ""),
                    "monto": monto
                })

    df_grafico = pd.DataFrame(datos_grafico)

    if not df_grafico.empty:
        df_grafico["mes"] = pd.Categorical(df_grafico["mes"], categories=MESES, ordered=True)
        df_grafico = df_grafico.sort_values(["mes", "generica"])

    return df_grafico, genericas_ordenadas

def determinar_escala(df_grafico):
    max_monto = df_grafico["monto"].max()
    if max_monto > 1e6:
        factor = 1e6
        unidad = "Millones S/"
        formato = lambda x: f"S/ {x/1e6:.2f}M"
    elif max_monto > 1e3:
        factor = 1e3
        unidad = "Miles S/"
        formato = lambda x: f"S/ {x/1e3:.1f}K"
    else:
        factor = 1
        unidad = "Soles"
        formato = lambda x: f"S/ {x:,.0f}"
    return factor, unidad, formato

def crear_grafico_mensual(df_filtrado, columnas_devengado):
    st.subheader("📈 Evolución del Devengado Mensual por Genérica")

    df_grafico, genericas_ordenadas = preparar_datos_grafico(df_filtrado, columnas_devengado)

    if df_grafico.empty:
        st.warning("No hay datos para mostrar en el gráfico")
        return

    totales_mes = df_grafico.groupby("mes")["monto"].sum().reset_index()
    factor, unidad, formato_total = determinar_escala(df_grafico)
    df_grafico["monto_mostrar"] = df_grafico["monto"] / factor

    fig = go.Figure()
    colores = COLORES_GENERICAS

    for i, generica in enumerate(genericas_ordenadas):
        df_gen = df_grafico[df_grafico["generica"] == generica]
        if not df_gen.empty:
            fig.add_trace(go.Bar(
                name=generica,
                x=df_gen["mes"],
                y=df_gen["monto_mostrar"],
                text=df_gen["monto"].apply(lambda x: f"S/ {x:,.0f}"),
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

    # Anotaciones de totales
    for _, row in totales_mes.iterrows():
        mes = row["mes"]
        total = row["monto"]
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

    fig.update_xaxes(tickangle=45, gridcolor='lightgray')
    fig.update_yaxes(gridcolor='lightgray')

    st.plotly_chart(fig, use_container_width=True)

    # Expandir con datos detallados
    with st.expander("Ver datos detallados"):
        pivot_df = df_grafico.pivot_table(
            values='monto',
            index='generica',
            columns='mes',
            aggfunc='sum',
            fill_value=0
        )
        pivot_df = pivot_df.reindex(genericas_ordenadas)

        pivot_display = pivot_df.copy()
        for col in pivot_display.columns:
            pivot_display[col] = pivot_display[col].apply(lambda x: f"S/ {x:,.0f}")

        st.dataframe(pivot_display, use_container_width=True)

        csv = df_grafico[["generica", "mes", "monto"]].to_csv(index=False)
        st.download_button(
            "📥 Descargar datos CSV",
            csv,
            "evolucion_mensual.csv",
            "text/csv"
        )

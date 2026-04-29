# src/components/monthly_chart.py
# ─────────────────────────────────────────────────────────────────────────────
# Gráfico de evolución mensual del devengado por genérica
# con línea de comparación contra la programación
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from config import MESES, COLORES_GENERICAS


def _determinar_escala(max_val: float) -> tuple[float, str]:
    if max_val > 1e6:
        return 1e6, "Millones S/"
    if max_val > 1e3:
        return 1e3, "Miles S/"
    return 1, "Soles"


def _fmt_soles(valor) -> str:
    """
    Formatea un valor numérico como soles peruanos.
    Maneja NaN, None, y valores inválidos.
    """
    # Manejar valores nulos o inválidos
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return "—"
    
    try:
        # Convertir a número si es string
        if isinstance(valor, str):
            valor = float(valor.replace(",", "."))
        
        # Formatear
        return f"S/ {round(valor):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "—"


def preparar_datos_grafico(
    df_filtrado: pd.DataFrame,
    columnas_devengado: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    """
    Construye un DataFrame pivotado con el devengado mensual por genérica,
    garantizando que todos los meses del año aparezcan (incluidos los ceros).
    """
    genericas = sorted(df_filtrado["generica"].unique())

    filas = []
    for mes_col in columnas_devengado:
        nombre_mes = mes_col.replace("Devengado_", "")
        if nombre_mes not in MESES:
            continue
        fila = {"mes": nombre_mes}
        for gen in genericas:
            fila[gen] = df_filtrado[df_filtrado["generica"] == gen][mes_col].sum()
        filas.append(fila)

    # Completar meses sin datos
    meses_en_datos = {f["mes"] for f in filas}
    for mes in MESES:
        if mes not in meses_en_datos:
            fila = {"mes": mes}
            for gen in genericas:
                fila[gen] = 0
            filas.append(fila)

    df = pd.DataFrame(filas)
    df["mes"] = pd.Categorical(df["mes"], categories=MESES, ordered=True)
    df = df.sort_values("mes")
    return df.set_index("mes"), genericas


def crear_grafico_mensual(
    df_filtrado: pd.DataFrame,
    columnas_devengado: list[str],
    programacion_df: pd.DataFrame,
):
    """
    Renderiza:
    1. Gráfico de barras apiladas (devengado mensual por genérica)
    2. Línea superpuesta (programación mensual total)
    3. Tabla con valores formateados
    4. Botón de descarga CSV
    """
    st.markdown('<div class="section-title">Evolución Mensual del Devengado</div>', 
                unsafe_allow_html=True)

    if df_filtrado.empty:
        st.warning("Sin datos para mostrar.")
        return

    # Preparar datos
    pivot, genericas = preparar_datos_grafico(df_filtrado, columnas_devengado)

    # Total programado por mes (si existe)
    prog_mensual = {}
    if programacion_df is not None and not programacion_df.empty:
        for mes in MESES:
            prog_row = programacion_df[programacion_df.index == mes]
            prog_mensual[mes] = (
                prog_row.sum(axis=1).values[0]
                if not prog_row.empty else 0
            )

    # Crear figura
    fig = go.Figure()

    # Barras apiladas por genérica
    for i, gen in enumerate(genericas):
        color = COLORES_GENERICAS[i % len(COLORES_GENERICAS)]
        fig.add_trace(go.Bar(
            x=pivot.index,
            y=pivot[gen],
            name=gen,
            marker=dict(color=color),
            hovertemplate=f"<b>{gen}</b><br>%{{x}}<br>S/ %{{y:,.0f}}<extra></extra>",
        ))

    # Línea de programación (si existe)
    if prog_mensual:
        prog_vals = [prog_mensual.get(mes, 0) for mes in pivot.index]
        fig.add_trace(go.Scatter(
            x=pivot.index,
            y=prog_vals,
            mode="lines+markers",
            name="Programación",
            line=dict(color="#E74C3C", width=3, dash="dash"),
            marker=dict(size=8),
            hovertemplate="<b>Programación</b><br>%{x}<br>S/ %{y:,.0f}<extra></extra>",
        ))

    # Actualizar layout
    fig.update_layout(
        title="Devengado Mensual por Genérica",
        xaxis_title="Mes",
        yaxis_title="Monto (S/.)",
        barmode="stack",
        hovermode="x unified",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#ececec"),
        yaxis=dict(gridcolor="#ececec"),
        margin=dict(t=80, b=30, l=10, r=10),
    )

    st.plotly_chart(fig, use_container_width=True, key="bar_mensual")

    # Tabla con valores formateados
    st.markdown('<div class="section-title">Tabla de Valores</div>', 
                unsafe_allow_html=True)

    with st.expander("Ver tabla detallada", expanded=False):
        pivot_fmt = pivot.copy()
        for col in pivot_fmt.columns:
            pivot_fmt[col] = pivot_fmt[col].apply(_fmt_soles)

        st.dataframe(pivot_fmt, use_container_width=True)

        csv = pivot.to_csv().encode("utf-8")
        st.download_button("📥 Descargar CSV", csv, "evolucion_mensual.csv", "text/csv")

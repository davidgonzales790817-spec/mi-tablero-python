# src/components/monthly_chart.py
# ─────────────────────────────────────────────────────────────────────────────
# Gráfico de evolución mensual del devengado por genérica
# con línea de comparación contra la programación
# ─────────────────────────────────────────────────────────────────────────────

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from config import MESES, COLORES_GENERICAS


def _determinar_escala(max_val: float) -> tuple[float, str]:
    if max_val > 1e6:
        return 1e6, "Millones S/"
    if max_val > 1e3:
        return 1e3, "Miles S/"
    return 1, "Soles"


def _fmt_soles(valor: float) -> str:
    return f"S/ {round(valor):,}".replace(",", ".")


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

    df_graf = pd.DataFrame(filas)
    df_graf["mes"] = pd.Categorical(df_graf["mes"], categories=MESES, ordered=True)
    df_graf = df_graf.sort_values("mes").reset_index(drop=True)

    return df_graf, genericas


def crear_grafico_mensual(
    df_filtrado: pd.DataFrame,
    columnas_devengado: list[str],
    df_programacion: pd.DataFrame | None = None,
):
    """
    Renderiza el gráfico de barras apiladas (devengado mensual por genérica)
    con una línea discontinua que muestra el monto programado total del mes.
    """
    st.subheader("📈 Evolución del Devengado Mensual por Genérica")

    df_graf, genericas = preparar_datos_grafico(df_filtrado, columnas_devengado)

    if df_graf.empty:
        st.warning("Sin datos para el gráfico mensual.")
        return

    # Escala
    max_val = df_graf[genericas].sum(axis=1).max() if genericas else 0
    factor, unidad = _determinar_escala(max_val)

    fig = go.Figure()
    colores = COLORES_GENERICAS

    # Barras por genérica
    for i, gen in enumerate(genericas):
        vals = df_graf[gen]
        fig.add_trace(go.Bar(
            name=gen,
            x=df_graf["mes"],
            y=vals / factor,
            customdata=vals,
            text=vals.apply(lambda x: _fmt_soles(x) if x > 0 else ""),
            textposition="inside",
            textfont=dict(size=9, color="white"),
            marker_color=colores[i % len(colores)],
            hovertemplate=(
                "<b>%{x}</b><br>"
                f"{gen}<br>"
                "S/ %{customdata:,.0f}<extra></extra>"
            ),
        ))

    # Línea de programación total
    # Filtramos el df_programacion a las mismas genéricas del df_filtrado
    # para que la línea respete los filtros laterales
    if df_programacion is not None:
        gens_activas = [g for g in genericas if g in df_programacion.index]
        df_prog_filtrado = df_programacion.loc[gens_activas] if gens_activas else df_programacion
        prog_vals = []
        for mes in MESES:
            if mes in df_prog_filtrado.columns:
                prog_vals.append(df_prog_filtrado[mes].sum())
            else:
                prog_vals.append(0)

        fig.add_trace(go.Scatter(
            name="Programado",
            x=MESES,
            y=[v / factor for v in prog_vals],
            customdata=prog_vals,
            mode="lines+markers",
            line=dict(color="#1e3a5f", width=2.5, dash="dash"),
            marker=dict(size=6, color="#1e3a5f"),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Programado: S/ %{customdata:,.0f}<extra></extra>"
            ),
        ))

    # Anotaciones de totales ejecutados
    totales = df_graf[genericas].sum(axis=1) if genericas else pd.Series([0] * len(df_graf))
    for mes, total in zip(df_graf["mes"], totales):
        if total > 0:
            fig.add_annotation(
                x=mes, y=total / factor,
                text=f"<b>{_fmt_soles(total)}</b>",
                showarrow=False, yshift=14,
                font=dict(size=10, color="#1e293b"),
                bgcolor="rgba(255,255,255,0.88)",
                bordercolor="#94a3b8", borderwidth=1, borderpad=3,
            )

    fig.update_layout(
        barmode="stack",
        xaxis=dict(
            tickangle=30,
            tickmode="array",
            tickvals=MESES,
            ticktext=MESES,
            tickfont=dict(size=11),
            gridcolor="#e5e7eb",
        ),
        yaxis=dict(title=unidad, gridcolor="#e5e7eb", tickfont=dict(size=11)),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1, font=dict(size=11),
        ),
        hovermode="x unified",
        height=440,
        margin=dict(l=10, r=10, t=65, b=55),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tabla pivotada expandible
    with st.expander("📋 Ver datos mensuales detallados"):
        pivot = df_graf.set_index("mes")[genericas].copy()
        pivot.index = pd.CategoricalIndex(pivot.index, categories=MESES, ordered=True)
        pivot = pivot.sort_index()

        # Fila TOTAL EJECUTADO
        pivot.loc["TOTAL EJECUTADO"] = pivot.sum()

        # Fila PROGRAMADO
        if df_programacion is not None:
            prog_row = {mes: (df_programacion[mes].sum() if mes in df_programacion.columns else 0)
                        for mes in MESES}
            prog_df  = pd.DataFrame([prog_row], index=["PROGRAMADO"])
            prog_df.columns = pd.CategoricalIndex(prog_df.columns, categories=MESES, ordered=True)
            pivot = pd.concat([pivot, prog_df])

        pivot_fmt = pivot.copy()
        for col in pivot_fmt.columns:
            pivot_fmt[col] = pivot_fmt[col].apply(_fmt_soles)

        st.dataframe(pivot_fmt, use_container_width=True)

        csv = pivot.to_csv().encode("utf-8")
        st.download_button("📥 Descargar CSV", csv, "evolucion_mensual.csv", "text/csv")

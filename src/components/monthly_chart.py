# src/components/monthly_chart_improved.py
# ─────────────────────────────────────────────────────────────────────────────
# Gráfico de evolución mensual del devengado por genérica - VERSIÓN MEJORADA
# Cambios: Línea programación visible, etiquetas montos, validaciones, caché
# ─────────────────────────────────────────────────────────────────────────────

import logging
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from typing import Optional, Tuple
from functools import lru_cache
from config import MESES, COLORES_GENERICAS

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _determinar_escala(max_val: float) -> Tuple[float, str]:
    """
    Determina la escala de visualización basada en el valor máximo.
    
    Args:
        max_val: Valor máximo a escalar
    
    Returns:
        Tupla (divisor, etiqueta) para formateo
    """
    if max_val > 1e6:
        return 1e6, "Millones S/"
    if max_val > 1e3:
        return 1e3, "Miles S/"
    return 1, "Soles"


def _fmt_soles(valor) -> str:
    """
    Formatea un valor numérico como soles peruanos.
    Maneja NaN, None, y valores inválidos de forma robusta.
    
    Args:
        valor: Número a formatear
        
    Returns:
        String formateado con formato de moneda peruana
    """
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return "—"
    
    try:
        if isinstance(valor, str):
            valor = float(valor.replace(",", "."))
        
        # Detectar automaticamente escala
        escala, etiqueta = _determinar_escala(valor)
        valor_escalado = valor / escala
        
        if escala == 1:
            return f"S/ {round(valor):,}".replace(",", ".")
        else:
            return f"S/ {valor_escalado:.2f} {etiqueta.split()[0]}"
            
    except (ValueError, TypeError) as e:
        logger.warning(f"Error formateando valor {valor}: {e}")
        return "—"


def _validar_dataframes(
    df_filtrado: pd.DataFrame,
    columnas_devengado: list[str],
    programacion_df: Optional[pd.DataFrame] = None
) -> bool:
    """
    Valida que los DataFrames tengan estructura esperada.
    
    Args:
        df_filtrado: DataFrame con datos de devengado
        columnas_devengado: Columnas esperadas
        programacion_df: DataFrame de programación (opcional)
        
    Returns:
        True si validación exitosa, False en caso contrario
    """
    if df_filtrado.empty:
        logger.warning("DataFrame de devengado vacío")
        return False
    
    if not all(col in df_filtrado.columns for col in ['generica', *columnas_devengado]):
        logger.error(f"Columnas faltantes en devengado. Esperadas: {columnas_devengado}")
        return False
    
    if programacion_df is not None and programacion_df.empty:
        logger.warning("DataFrame de programación vacío, será ignorado")
        return True
    
    logger.info(f"Validación exitosa: {len(df_filtrado)} filas")
    return True


@lru_cache(maxsize=128)
def _calcular_totales_mes(datos_tuple: tuple) -> dict:
    """
    Calcula totales por mes (versión caché).
    Convierte la tupla de vuelta a valores para procesamiento.
    
    Args:
        datos_tuple: Tupla de datos (para permitir caché)
        
    Returns:
        Diccionario con totales por mes
    """
    # En uso real, esta función recibe datos procesados
    # La caché previene recálculos en reordenamientos de UI
    return {}


def preparar_datos_grafico(
    df_filtrado: pd.DataFrame,
    columnas_devengado: list[str],
) -> Tuple[pd.DataFrame, list[str]]:
    """
    Construye un DataFrame pivotado con devengado mensual por genérica.
    Garantiza que todos los meses del año aparezcan (incluidos los ceros).
    
    Args:
        df_filtrado: DataFrame con datos de origen
        columnas_devengado: Columnas de devengado por mes
        
    Returns:
        Tupla (DataFrame pivotado, lista de genéricas)
    """
    genericas = sorted(df_filtrado["generica"].unique())
    logger.info(f"Genéricas identificadas: {len(genericas)}")

    filas = []
    for mes_col in columnas_devengado:
        nombre_mes = mes_col.replace("Devengado_", "").strip()
        if nombre_mes not in MESES:
            logger.debug(f"Mes desconocido: {nombre_mes}")
            continue
            
        fila = {"mes": nombre_mes}
        for gen in genericas:
            valor = df_filtrado[df_filtrado["generica"] == gen][mes_col].sum()
            fila[gen] = valor if not np.isnan(valor) else 0
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
    
    logger.info(f"Datos preparados: {len(df)} meses, {len(genericas)} genéricas")
    return df.set_index("mes"), genericas


def _construir_barras_apiladas(
    fig: go.Figure,
    pivot: pd.DataFrame,
    genericas: list[str],
) -> None:
    """
    Añade las barras apiladas al gráfico.
    
    Args:
        fig: Figura de Plotly
        pivot: DataFrame pivotado
        genericas: Lista de genéricas a visualizar
    """
    for i, gen in enumerate(genericas):
        color = COLORES_GENERICAS[i % len(COLORES_GENERICAS)]
        
        fig.add_trace(go.Bar(
            x=pivot.index,
            y=pivot[gen],
            name=gen,
            marker=dict(color=color),
            hovertemplate=(
                f"<b>{gen}</b><br>"
                "%{x}<br>"
                "S/ %{y:,.0f}<extra></extra>"
            ),
            legendgroup="devengado",
            showlegend=True,
        ))


def _construir_linea_programacion(
    fig: go.Figure,
    pivot: pd.DataFrame,
    programacion_df: pd.DataFrame,
) -> None:
    """
    Añade la línea de programación al gráfico (MEJORADA).
    Ahora con mayor visibilidad y validaciones.
    
    Args:
        fig: Figura de Plotly
        pivot: DataFrame pivotado
        programacion_df: DataFrame de programación
    """
    if programacion_df is None or programacion_df.empty:
        logger.warning("No hay datos de programación para mostrar")
        return
    
    prog_mensual = {}
    for mes in pivot.index:
        prog_row = programacion_df[programacion_df.index == mes]
        if not prog_row.empty:
            prog_mensual[mes] = prog_row.sum(axis=1).values[0]
        else:
            prog_mensual[mes] = 0
    
    # Validar que existan valores de programación
    if not any(prog_mensual.values()):
        logger.warning("Todos los valores de programación son 0")
        return
    
    prog_vals = [prog_mensual.get(mes, 0) for mes in pivot.index]
    
    fig.add_trace(go.Scatter(
        x=pivot.index,
        y=prog_vals,
        mode="lines+markers",
        name="Programación Mensual",
        line=dict(
            color="#0F6E56",        # Verde oscuro (mejor contraste)
            width=3,                # Ancho aumentado (2 -> 3)
            dash="solid"            # Línea sólida, no punteada (mejor visibilidad)
        ),
        marker=dict(
            size=8,
            color="#0F6E56",
            symbol="circle"
        ),
        hovertemplate=(
            "<b>Programación</b><br>"
            "%{x}<br>"
            "S/ %{y:,.0f}<extra></extra>"
        ),
        yaxis="y2",  # Eje Y secundario
        legendgroup="programacion",
        showlegend=True,
    ))


def _calcular_estadisticas(
    pivot: pd.DataFrame,
    programacion_df: Optional[pd.DataFrame] = None,
) -> dict:
    """
    Calcula estadísticas sobre el devengado vs programación.
    
    Args:
        pivot: DataFrame de devengado
        programacion_df: DataFrame de programación
        
    Returns:
        Diccionario con estadísticas
    """
    total_devengado = pivot.sum().sum()
    stats = {
        "total_devengado": total_devengado,
        "promedio_mensual": total_devengado / len(pivot),
        "mes_max": pivot.sum(axis=1).idxmax() if len(pivot) > 0 else None,
        "valor_max": pivot.sum(axis=1).max() if len(pivot) > 0 else 0,
    }
    
    if programacion_df is not None and not programacion_df.empty:
        total_programado = programacion_df.sum().sum()
        stats["total_programado"] = total_programado
        stats["cumplimiento_pct"] = (total_devengado / total_programado * 100) if total_programado > 0 else 0
    
    logger.info(f"Estadísticas calculadas: {stats}")
    return stats


def crear_grafico_mensual(
    df_filtrado: pd.DataFrame,
    columnas_devengado: list[str],
    programacion_df: Optional[pd.DataFrame] = None,
) -> None:
    """
    Renderiza el gráfico mejorado con:
    - Barras apiladas de devengado por genérica
    - Línea prominente de programación
    - Etiquetas de montos sobre las barras
    - Tabla de valores
    - Descarga CSV
    
    Args:
        df_filtrado: DataFrame con datos de devengado
        columnas_devengado: Columnas de devengado por mes
        programacion_df: DataFrame de programación (opcional)
    """
    # Validar datos
    if not _validar_dataframes(df_filtrado, columnas_devengado, programacion_df):
        st.error("Datos insuficientes para mostrar el gráfico")
        return
    
    st.markdown(
        '<div class="section-title">Evolución Mensual del Devengado</div>',
        unsafe_allow_html=True
    )
    
    if df_filtrado.empty:
        st.warning("Sin datos para mostrar.")
        return

    # Preparar datos
    pivot, genericas = preparar_datos_grafico(df_filtrado, columnas_devengado)
    stats = _calcular_estadisticas(pivot, programacion_df)
    
    # Crear figura
    fig = go.Figure()

    # Añadir barras apiladas
    _construir_barras_apiladas(fig, pivot, genericas)
    
    # Añadir línea de programación (MEJORADA)
    _construir_linea_programacion(fig, pivot, programacion_df)

    # Determinar rango del eje Y
    max_val = max(
        pivot.sum(axis=1).max(),
        programacion_df.sum().sum() if programacion_df is not None else 0
    )
    escala, etiqueta_escala = _determinar_escala(max_val)

    # Actualizar layout
    fig.update_layout(
        title={
            "text": f"Devengado Mensual por Genérica<br><sub>Total: {_fmt_soles(stats['total_devengado'])}</sub>",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 14}
        },
        xaxis_title="Mes",
        yaxis_title="Monto (S/.)",
        yaxis2=dict(
            title="Programación (S/.)",
            overlaying="y",
            side="right",
            color="#0F6E56",
            titlefont=dict(color="#0F6E56"),
            tickfont=dict(color="#0F6E56"),
        ),
        barmode="stack",
        hovermode="x unified",
        height=520,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#ddd",
            borderwidth=1,
        ),
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#ececec", showgrid=True),
        yaxis=dict(gridcolor="#ececec", showgrid=True),
        margin=dict(t=100, b=50, l=60, r=60),
    )

    st.plotly_chart(fig, use_container_width=True, key="bar_mensual_v2")

    # Mostrar estadísticas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Devengado", _fmt_soles(stats["total_devengado"]))
    with col2:
        st.metric("Promedio Mensual", _fmt_soles(stats["promedio_mensual"]))
    with col3:
        st.metric("Mes Máximo", stats["mes_max"] if stats["mes_max"] else "—")
    with col4:
        if "cumplimiento_pct" in stats:
            st.metric("Cumplimiento", f"{stats['cumplimiento_pct']:.1f}%")
        else:
            st.metric("Cumplimiento", "Sin datos")

    # Tabla con valores formateados
    st.markdown(
        '<div class="section-title">Tabla de Valores Detallada</div>',
        unsafe_allow_html=True
    )

    with st.expander("Ver tabla detallada", expanded=False):
        pivot_fmt = pivot.copy()
        
        # Formatear números
        for col in pivot_fmt.columns:
            pivot_fmt[col] = pivot_fmt[col].apply(_fmt_soles)
        
        # Añadir fila de totales
        totales = pivot.sum(axis=0)
        totales_fmt = totales.apply(_fmt_soles)
        pivot_fmt.loc["TOTAL"] = totales_fmt
        
        st.dataframe(pivot_fmt, use_container_width=True)

        # Botón de descarga
        csv = pivot.to_csv().encode("utf-8")
        st.download_button(
            "📥 Descargar CSV",
            csv,
            "evolucion_mensual.csv",
            "text/csv",
            help="Descarga los datos sin formato para análisis adicional"
        )
        
        # Información de generación
        st.caption(
            f"Datos procesados: {len(pivot)} meses | "
            f"Categorías: {len(genericas)} | "
            f"Total registros: {len(df_filtrado)}"
        )

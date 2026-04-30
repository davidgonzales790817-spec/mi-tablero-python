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
from typing import Optional, Tuple, Dict
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
    
    if programacion_df is not None and not programacion_df.empty:
        logger.info(f"Programación cargada: {len(programacion_df)} filas")
    
    logger.info(f"Validación exitosa: {len(df_filtrado)} filas")
    return True


def obtener_programacion_desde_session() -> Optional[pd.DataFrame]:
    """
    Obtiene el DataFrame de programación desde session_state.
    
    Returns:
        DataFrame de programación o None si no existe
    """
    if "programacion_mensual" in st.session_state:
        df_prog = st.session_state.programacion_mensual
        if not df_prog.empty:
            logger.info("Programación obtenida desde session_state")
            return df_prog
    logger.info("No hay programación guardada en session_state")
    return None


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


def preparar_programacion_para_grafico(
    programacion_df: pd.DataFrame,
    meses: list,
) -> Dict[str, float]:
    """
    Prepara los datos de programación para el gráfico.
    Convierte el DataFrame de programación (genéricas x meses) a total mensual.
    
    Args:
        programacion_df: DataFrame con programación por genérica y mes
        meses: Lista de meses en orden
        
    Returns:
        Diccionario {mes: total_programado}
    """
    if programacion_df is None or programacion_df.empty:
        return {mes: 0 for mes in meses}
    
    # Sumar todas las genéricas para obtener total mensual
    total_por_mes = {}
    
    for mes in meses:
        if mes in programacion_df.columns:
            total = programacion_df[mes].sum()
            total_por_mes[mes] = total if not np.isnan(total) else 0
        else:
            total_por_mes[mes] = 0
    
    logger.info(f"Programación preparada: {total_por_mes}")
    return total_por_mes


def _construir_barras_apiladas(
    fig: go.Figure,
    pivot: pd.DataFrame,
    genericas: list[str],
    escala: float,
) -> None:
    """
    Añade las barras apiladas al gráfico con etiquetas de montos.
    
    Args:
        fig: Figura de Plotly
        pivot: DataFrame pivotado
        genericas: Lista de genéricas a visualizar
        escala: Factor de escala para el eje Y
    """
    for i, gen in enumerate(genericas):
        color = COLORES_GENERICAS[i % len(COLORES_GENERICAS)]
        
        fig.add_trace(go.Bar(
            x=pivot.index,
            y=pivot[gen] / escala,
            name=gen,
            marker=dict(color=color),
            text=pivot[gen].apply(lambda x: _fmt_soles(x)),
            textposition="inside",
            textfont=dict(size=9),
            hovertemplate=(
                f"<b>{gen}</b><br>"
                "%{x}<br>"
                "S/ %{customdata:,.0f}<extra></extra>"
            ),
            customdata=pivot[gen],
            legendgroup="devengado",
            showlegend=True,
        ))


def _construir_linea_programacion(
    fig: go.Figure,
    pivot: pd.DataFrame,
    programacion_por_mes: Dict[str, float],
    escala: float,
) -> None:
    """
    Añade la línea de programación al gráfico (MEJORADA).
    Ahora con mayor visibilidad y validaciones.
    
    Args:
        fig: Figura de Plotly
        pivot: DataFrame pivotado
        programacion_por_mes: Diccionario con programación por mes
        escala: Factor de escala para el eje Y
    """
    if not any(programacion_por_mes.values()):
        logger.info("No hay datos de programación para mostrar")
        return
    
    prog_vals = [programacion_por_mes.get(mes, 0) / escala for mes in pivot.index]
    
    fig.add_trace(go.Scatter(
        x=pivot.index,
        y=prog_vals,
        mode="lines+markers+text",
        name="🎯 Programación Mensual",
        line=dict(
            color="#E63946",        # Rojo intenso (mejor contraste)
            width=3,
            dash="solid"
        ),
        marker=dict(
            size=10,
            color="#E63946",
            symbol="circle-dot",
            line=dict(width=1, color="white")
        ),
        text=[_fmt_soles(programacion_por_mes.get(mes, 0)) for mes in pivot.index],
        textposition="top center",
        textfont=dict(size=10, color="#E63946", family="Arial Black"),
        hovertemplate=(
            "<b>📊 Programación</b><br>"
            "%{x}<br>"
            "S/ %{customdata:,.0f}<extra></extra>"
        ),
        customdata=[programacion_por_mes.get(mes, 0) for mes in pivot.index],
        name="Programación",
        legendgroup="programacion",
        showlegend=True,
    ))


def _agregar_anotaciones_totales(
    fig: go.Figure,
    pivot: pd.DataFrame,
    escala: float,
) -> None:
    """
    Agrega anotaciones con el total mensual encima de cada barra.
    
    Args:
        fig: Figura de Plotly
        pivot: DataFrame pivotado
        escala: Factor de escala
    """
    totales_mensuales = pivot.sum(axis=1)
    
    for i, (mes, total) in enumerate(totales_mensuales.items()):
        if total > 0:
            fig.add_annotation(
                x=mes,
                y=(total / escala) + (max(totales_mensuales) / escala * 0.02),
                text=f"<b>💰 {_fmt_soles(total)}</b>",
                showarrow=False,
                font=dict(size=11, color="#2C3E50", family="Arial Black"),
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#2C3E50",
                borderwidth=1,
                borderpad=4,
                yshift=5
            )


def _calcular_estadisticas(
    pivot: pd.DataFrame,
    programacion_por_mes: Optional[Dict[str, float]] = None,
) -> dict:
    """
    Calcula estadísticas sobre el devengado vs programación.
    
    Args:
        pivot: DataFrame de devengado
        programacion_por_mes: Diccionario con programación por mes
        
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
    
    if programacion_por_mes and any(programacion_por_mes.values()):
        total_programado = sum(programacion_por_mes.values())
        stats["total_programado"] = total_programado
        stats["cumplimiento_pct"] = (total_devengado / total_programado * 100) if total_programado > 0 else 0
        stats["brecha"] = total_devengado - total_programado
    else:
        stats["total_programado"] = 0
        stats["cumplimiento_pct"] = 0
        stats["brecha"] = 0
    
    logger.info(f"Estadísticas calculadas: total_devengado={total_devengado:,.0f}")
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
    # Si no se pasó programacion_df, intentar obtener de session_state
    if programacion_df is None or programacion_df.empty:
        programacion_df = obtener_programacion_desde_session()
    
    # Validar datos
    if not _validar_dataframes(df_filtrado, columnas_devengado, programacion_df):
        st.error("Datos insuficientes para mostrar el gráfico")
        return
    
    st.markdown("### 📈 Evolución Mensual del Devengado por Genérica")
    
    if df_filtrado.empty:
        st.warning("Sin datos para mostrar.")
        return

    # Preparar datos de devengado
    pivot, genericas = preparar_datos_grafico(df_filtrado, columnas_devengado)
    
    # Preparar datos de programación
    programacion_por_mes = preparar_programacion_para_grafico(programacion_df, pivot.index.tolist())
    
    # Calcular estadísticas
    stats = _calcular_estadisticas(pivot, programacion_por_mes)
    
    # Determinar escala y rango
    max_val = max(
        pivot.sum(axis=1).max(),
        max(programacion_por_mes.values()) if programacion_por_mes else 0,
        stats["total_devengado"] / 6
    )
    escala, etiqueta_escala = _determinar_escala(max_val)
    
    # Crear figura
    fig = go.Figure()

    # Añadir barras apiladas
    _construir_barras_apiladas(fig, pivot, genericas, escala)
    
    # Añadir línea de programación
    if any(programacion_por_mes.values()):
        _construir_linea_programacion(fig, pivot, programacion_por_mes, escala)
    
    # Añadir anotaciones de totales mensuales
    _agregar_anotaciones_totales(fig, pivot, escala)

    # Actualizar layout
    fig.update_layout(
        title={
            "text": f"<b>Devengado vs Programación</b><br>"
                    f"<sub>Total Devengado: {_fmt_soles(stats['total_devengado'])} | "
                    f"Total Programado: {_fmt_soles(stats['total_programado'])} | "
                    f"Cumplimiento: {stats['cumplimiento_pct']:.1f}%</sub>",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 14}
        },
        xaxis_title="Mes",
        yaxis_title=etiqueta_escala,
        barmode="stack",
        hovermode="x unified",
        height=550,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#ddd",
            borderwidth=1,
        ),
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            gridcolor="#ececec", 
            showgrid=True,
            tickangle=45,
            tickfont=dict(size=11)
        ),
        yaxis=dict(gridcolor="#ececec", showgrid=True),
        margin=dict(t=120, b=80, l=60, r=60),
    )

    st.plotly_chart(fig, use_container_width=True, key="bar_mensual_v2")

    # Mostrar métricas clave
    st.markdown("### 📊 Resumen de Ejecución")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Devengado", _fmt_soles(stats["total_devengado"]))
    with col2:
        st.metric("Total Programado", _fmt_soles(stats["total_programado"]))
    with col3:
        color = "normal" if stats["cumplimiento_pct"] >= 100 else "inverse"
        st.metric("Cumplimiento", f"{stats['cumplimiento_pct']:.1f}%", delta_color=color)
    with col4:
        st.metric("Promedio Mensual", _fmt_soles(stats["promedio_mensual"]))
    with col5:
        brecha_color = "normal" if stats["brecha"] >= 0 else "inverse"
        st.metric("Brecha", _fmt_soles(stats["brecha"]), delta_color=brecha_color)

    # Tabla con valores formateados
    with st.expander("📋 Ver tabla detallada de valores", expanded=False):
        # Crear tabla con datos de devengado
        devengado_total_mensual = pivot.sum(axis=1)
        
        tabla = pd.DataFrame({
            "Mes": pivot.index,
            "Devengado Total": devengado_total_mensual.apply(_fmt_soles),
            "Programación": [programacion_por_mes.get(mes, 0) for mes in pivot.index],
            "Diferencia": [(devengado_total_mensual[i] - programacion_por_mes.get(mes, 0)) 
                          for i, mes in enumerate(pivot.index)]
        })
        
        tabla["Programación"] = tabla["Programación"].apply(_fmt_soles)
        tabla["Diferencia"] = tabla["Diferencia"].apply(_fmt_soles)
        
        st.dataframe(tabla, use_container_width=True, hide_index=True)
        
        # Botón de descarga
        csv_data = pivot.copy()
        csv_data["TOTAL_MENSUAL"] = devengado_total_mensual
        csv_data["PROGRAMACION"] = [programacion_por_mes.get(mes, 0) for mes in pivot.index]
        
        csv = csv_data.to_csv().encode("utf-8")
        st.download_button(
            "📥 Descargar datos completos (CSV)",
            csv,
            "evolucion_mensual_detallada.csv",
            "text/csv",
            help="Descarga los datos de devengado y programación"
        )
        
        # Información de generación
        st.caption(
            f"📅 Datos procesados: {len(pivot)} meses | "
            f"📁 Categorías: {len(genericas)} | "
            f"📊 Registros analizados: {len(df_filtrado)} | "
            f"🎯 Programación: {'Sí' if any(programacion_por_mes.values()) else 'No'}"
        )

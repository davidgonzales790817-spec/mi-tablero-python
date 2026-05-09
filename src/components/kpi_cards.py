# src/components/kpi_cards.py
# ─────────────────────────────────────────────────────────────────[...]
# KPI cards modernos con componentes nativos de Streamlit
# ─────────────────────────────────────────────────────────────────[...]

import streamlit as st
from typing import Optional
from config import PALETA, color_por_avance


def _format_soles(valor: float, decimals: int = 1) -> str:
    """Formatea un valor en soles con escala automática (M/K)."""
    if abs(valor) >= 1e6:
        return f"S/ {valor/1e6:.{decimals}f}M"
    if abs(valor) >= 1e3:
        return f"S/ {valor/1e3:.{decimals}f}K"
    return f"S/ {valor:,.0f}".replace(",", ".")


def kpi_card(
    titulo: str,
    valor: float,
    *,
    valor_es_porcentaje: bool = False,
    sparkline: Optional[list] = None,
    delta: Optional[float] = None,
    delta_label: str = "vs anterior",
    subtitulo: Optional[str] = None,
    progreso: Optional[float] = None,
    estado: str = "neutral",
    target: Optional[float] = None,
    formato: str = "soles",
):
    """
    Renderiza una KPI card moderna usando componentes nativos de Streamlit.

    Args:
        titulo: Etiqueta de la métrica
        valor: Valor numérico principal
        sparkline: Lista de valores para mini-gráfico de tendencia (ignorado en versión nativa)
        delta: Variación vs período anterior
        progreso: Si se especifica, muestra barra de progreso 0-100
        estado: Color del indicador (success, warning, danger, neutral)
        target: Umbral de referencia
        formato: 'soles', 'porcentaje', 'numero'
    """
    # Formateo del valor
    if formato == "porcentaje":
        valor_str = f"{valor:.1f}%"
    elif formato == "soles":
        valor_str = _format_soles(valor)
    else:
        valor_str = f"{valor:,.0f}".replace(",", ".")

    # Mostrar título
    st.markdown(f"**{titulo}**", help=delta_label if delta else None)
    
    # Mostrar valor principal
    st.metric(
        label=titulo,
        value=valor_str,
        delta=f"{delta:.1f}%" if delta is not None else None,
        label_visibility="collapsed"
    )
    
    # Mostrar subtítulo si existe
    if subtitulo:
        st.caption(subtitulo)
    
    # Mostrar barra de progreso si existe
    if progreso is not None:
        st.progress(min(progreso / 100, 1.0))


def grid_kpis(kpis: list, columnas: int = 4):
    """
    Renderiza una grilla de KPI cards usando st.columns.

    Args:
        kpis: Lista de dicts con argumentos para kpi_card()
        columnas: Número de columnas (default 4)
    """
    # Crear columnas una sola vez
    cols = st.columns(columnas)
    
    # Distribuir KPIs en las columnas
    for i, kpi in enumerate(kpis):
        col_index = i % columnas
        with cols[col_index]:
            kpi_card(**kpi)


def panel_alertas(alertas: list):
    """
    Renderiza el panel de alertas activas usando componentes nativos.

    Args:
        alertas: Lista de dicts con keys: severidad, categoria, titulo, descripcion
    """
    if not alertas:
        st.success("Sin alertas activas. Ejecución dentro de parámetros.")
        return

    st.markdown(f"**Alertas activas · {len(alertas)}**")
    
    for alerta in alertas:
        # Usar el ícono y color según severidad
        severidad = alerta.get("severidad", "media").lower()
        
        if "critica" in severidad:
            icon = "🔴"
        elif "alta" in severidad:
            icon = "🟠"
        else:
            icon = "🟡"
        
        # Mostrar alerta con st.warning, st.error o st.info según severidad
        mensaje = f"**{alerta['titulo']}**\n\n{alerta.get('descripcion', '')}"
        
        if "critica" in severidad:
            st.error(mensaje)
        elif "alta" in severidad:
            st.warning(mensaje)
        else:
            st.info(mensaje)

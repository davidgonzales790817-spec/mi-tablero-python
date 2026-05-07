# src/components/kpi_cards.py
# ─────────────────────────────────────────────────────────────────[...]
# KPI cards modernos con sparklines, status colors y tendencias
# Reemplaza/complementa los st.metric tradicionales con cards más informativas
# ─────────────────────────────────────────────────────────────────[...]

import streamlit as st
import plotly.graph_objects as go
from typing import Optional
from config import PALETA, color_por_avance


def _format_soles(valor: float, decimals: int = 1) -> str:
    """Formatea un valor en soles con escala automática (M/K)."""
    if abs(valor) >= 1e6:
        return f"S/ {valor/1e6:.{decimals}f}M"
    if abs(valor) >= 1e3:
        return f"S/ {valor/1e3:.{decimals}f}K"
    return f"S/ {valor:,.0f}".replace(",", ".")


def _sparkline_html(valores: list, color: str, height: int = 24) -> str:
    """Genera un sparkline SVG inline minimal."""
    if not valores or len(valores) < 2:
        return ""

    # Normalizar a 0-100 para el viewBox
    min_v, max_v = min(valores), max(valores)
    rango = max(max_v - min_v, 1)
    n = len(valores)

    puntos = " ".join([
        f"{i * (100 / (n - 1)):.1f},{(1 - (v - min_v) / rango) * 90 + 5:.1f}"
        for i, v in enumerate(valores)
    ])

    return f"""
    <svg viewBox="0 0 100 100" preserveAspectRatio="none"
         style="width: 100%; height: {height}px; display: block;">
        <polyline points="{puntos}" fill="none" stroke="{color}" stroke-width="2"
                  vector-effect="non-scaling-stroke"/>
    </svg>
    """


def kpi_card(
    titulo: str,
    valor: float,
    *,
    valor_es_porcentaje: bool = False,
    sparkline: Optional[list] = None,
    delta: Optional[float] = None,
    delta_label: str = "vs anterior",
    subtitulo: Optional[str] = None,
    progreso: Optional[float] = None,  # 0-100, muestra barra de progreso
    estado: str = "neutral",  # 'success', 'warning', 'danger', 'neutral'
    target: Optional[float] = None,  # umbral teórico para indicar logro
    formato: str = "soles",  # 'soles', 'porcentaje', 'numero'
):
    """
    Renderiza una KPI card moderna en Streamlit usando HTML.

    Args:
        titulo: Etiqueta de la métrica
        valor: Valor numérico principal
        sparkline: Lista de valores para mini-gráfico de tendencia
        delta: Variación vs período anterior (en pp o S/)
        progreso: Si se especifica, muestra barra de progreso 0-100
        estado: Color del border-left para indicar status
        target: Umbral de referencia (línea vertical en barra de progreso)

    Uso:
        kpi_card("Devengado", 13_800_000, progreso=9.7, estado="danger",
                 sparkline=[2.4, 5.7, 9.1, 13.8], target=33)
    """
    # Mapeo de estados a colores
    colores_borde = {
        "success":  PALETA["brand"],
        "info":     PALETA["info"],
        "warning":  PALETA["warning"],
        "danger":   PALETA["danger"],
        "neutral":  PALETA["text_muted"],
    }
    color_borde = colores_borde.get(estado, PALETA["text_muted"])

    # Auto-detectar estado por progreso si no se especificó
    if estado == "neutral" and progreso is not None:
        color_borde = color_por_avance(progreso)

    # Formateo del valor
    if formato == "porcentaje":
        valor_str = f"{valor:.1f}%"
    elif formato == "soles":
        valor_str = _format_soles(valor)
    else:
        valor_str = f"{valor:,.0f}".replace(",", ".")

    # Delta badge
    delta_html = ""
    if delta is not None:
        flecha = "↑" if delta > 0 else "↓" if delta < 0 else "→"
        color_delta = (
            PALETA["brand"] if delta > 0
            else PALETA["danger"] if delta < 0
            else PALETA["text_muted"]
        )
        delta_str = f"{flecha} {abs(delta):.1f}%" if abs(delta) < 1000 else f"{flecha} {_format_soles(abs(delta))}"
        delta_html = f"""
        <span style="font-size: 11px; color: {color_delta}; font-weight: 500;
                     background: {color_delta}20; padding: 2px 6px; border-radius: 4px;">
            {delta_str}
        </span>
        """

    # Sparkline
    sparkline_html = _sparkline_html(sparkline, color_borde) if sparkline else ""

    # Barra de progreso con target opcional
    progreso_html = ""
    if progreso is not None:
        target_marker = ""
        if target is not None:
            target_marker = f"""
            <div style="position: absolute; height: 100%; width: 1px;
                        left: {min(target, 100)}%; background: {PALETA['text_muted']};
                        top: 0;"></div>
            """
        progreso_html = f"""
        <div style="height: 6px; background: {color_borde}20;
                    border-radius: 3px; margin-top: 10px; position: relative;">
            <div style="position: absolute; top: 0; left: 0; height: 100%;
                        width: {min(progreso, 100):.1f}%; background: {color_borde};
                        border-radius: 3px;"></div>
            {target_marker}
        </div>
        """

    color_muted = PALETA["text_muted"]
    subtitulo_html = (
        f"<div style='font-size: 11px; color: {color_muted}; margin-top: 4px;'>{subtitulo}</div>"
        if subtitulo else ""
    )

    html = f"""
    <div style="background: {PALETA['bg_secondary']};
                border-radius: 8px;
                padding: 14px;
                border-left: 3px solid {color_borde};
                height: 100%;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
            <span style="font-size: 11px; color: {PALETA['text_muted']};
                         text-transform: uppercase; letter-spacing: 0.3px; font-weight: 500;">
                {titulo}
            </span>
            {delta_html}
        </div>
        <div style="font-size: 22px; font-weight: 500; line-height: 1.1;
                    color: {PALETA['text_primary']}; margin-bottom: 4px;">
            {valor_str}
        </div>
        {subtitulo_html}
        {progreso_html}
        {sparkline_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def grid_kpis(kpis: list, columnas: int = 4):
    """
    Renderiza una grilla de KPI cards.

    Args:
        kpis: Lista de dicts con argumentos para kpi_card()
        columnas: Número de columnas (default 4)

    Uso:
        grid_kpis([
            {"titulo": "PIM", "valor": 142_500_000},
            {"titulo": "Devengado", "valor": 13_800_000, "progreso": 9.7,
             "estado": "danger", "target": 33,
             "sparkline": [2.4, 5.7, 9.1, 13.8]},
            ...
        ])
    """
    cols = st.columns(columnas)
    for i, kpi in enumerate(kpis):
        with cols[i % columnas]:
            kpi_card(**kpi)


def panel_alertas(alertas: list):
    """
    Renderiza el panel de alertas activas.

    Args:
        alertas: Lista de dicts con keys: severidad, categoria, titulo, descripcion
    """
    if not alertas:
        st.success("Sin alertas activas. Ejecución dentro de parámetros.")
        return

    color_por_severidad = {
        "critica": PALETA["danger"],
        "alta":    PALETA["warning"],
        "media":   PALETA["info"],
    }

    st.markdown(
        f"<div style='font-size: 13px; font-weight: 500; margin-bottom: 12px;'>"
        f"Alertas activas · {len(alertas)}</div>",
        unsafe_allow_html=True,
    )

    for alerta in alertas:
        color = color_por_severidad.get(alerta["severidad"], PALETA["text_muted"])
        st.markdown(f"""
        <div style="background: {color}15;
                    border-left: 3px solid {color};
                    padding: 10px 12px;
                    border-radius: 4px;
                    margin-bottom: 8px;">
            <div style="font-size: 12px; font-weight: 500; color: {color}; margin-bottom: 2px;">
                {alerta['titulo']}
            </div>
            <div style="font-size: 11px; color: {PALETA['text_secondary']}; line-height: 1.5;">
                {alerta['descripcion']}
            </div>
        </div>
        """, unsafe_allow_html=True)

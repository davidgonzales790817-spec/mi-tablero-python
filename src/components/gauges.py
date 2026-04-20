# src/components/gauges.py
# ─────────────────────────────────────────────────────────────────────────────
# Indicadores de ejecución presupuestal (gauges tipo velocímetro)
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime


# ── Helpers ───────────────────────────────────────────────────────────────────

def meta_teorica() -> tuple[float, int]:
    """
    Calcula la meta teórica acumulada basada en el mes anterior al actual.
    Retorna (porcentaje_meta, numero_mes_referencia).
    """
    mes_actual  = datetime.now().month
    mes_ref     = mes_actual - 1 if mes_actual > 1 else 0
    meta        = round((mes_ref / 12) * 100, 1)
    return meta, mes_ref


def _color_gauge(pct: float, es_devengado: bool, meta: float) -> str:
    if es_devengado:
        if pct >= meta:        return "#16a34a"   # verde
        if pct >= meta - 5:    return "#d97706"   # ámbar
        return "#dc2626"                           # rojo
    # Para certificado y compromiso
    if pct >= 80:  return "#16a34a"
    if pct >= 50:  return "#d97706"
    return "#dc2626"


# ── Gauge individual ──────────────────────────────────────────────────────────

def crear_gauge(valor: float, total: float, titulo: str,
                es_devengado: bool = False) -> go.Figure:
    """
    Construye un indicador tipo gauge para el porcentaje valor/total.

    Args:
        valor:        Monto ejecutado (numerador).
        total:        PIM (denominador).
        titulo:       Texto que aparece debajo del gauge.
        es_devengado: Si True, aplica la lógica de meta teórica y
                      muestra la línea de umbral.
    """
    meta_val, _ = meta_teorica()
    pct         = round(valor / total * 100, 2) if total > 0 else 0
    color       = _color_gauge(pct, es_devengado, meta_val)

    fmt_monto = f"S/ {round(valor):,}".replace(",", ".")

    threshold = (
        {"line": {"color": "#000", "width": 3}, "thickness": 0.80, "value": meta_val}
        if es_devengado else None
    )

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number={"suffix": "%", "font": {"size": 28, "color": color}},
        title={
            "text": f"<b>{titulo}</b><br>"
                    f"<span style='font-size:12px;color:#64748b'>{fmt_monto}</span>",
            "font": {"size": 15},
        },
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": "#94a3b8",
                "tickfont": {"size": 10},
            },
            "bar":         {"color": color},
            "bgcolor":     "white",
            "borderwidth": 1,
            "bordercolor": "#cbd5e1",
            "threshold":   threshold,
            "steps":       [{"range": [0, 100], "color": "#f1f5f9"}],
        },
    ))

    fig.update_layout(
        height=230,
        margin=dict(l=20, r=20, t=60, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ── Sección completa de indicadores ──────────────────────────────────────────

def mostrar_indicadores(pim_total: float, certificado_total: float,
                        compromiso_total: float, devengado_total: float):
    """
    Renderiza los tres gauges (Certificado, Compromiso, Devengado)
    con su cabecera informativa sobre la meta teórica.
    """
    st.subheader("📊 Indicadores de Ejecución Presupuestal")

    meta_val, mes_num = meta_teorica()
    NOMBRES_MESES = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Setiembre", "Octubre", "Noviembre", "Diciembre",
    ]

    if mes_num > 0:
        st.info(
            f"📌 Meta teórica al cierre de **{NOMBRES_MESES[mes_num - 1]}**: "
            f"**{meta_val}%**  ·  La línea negra en el gauge de Devengado "
            f"indica este umbral."
        )

    g1, g2, g3 = st.columns(3)
    with g1:
        st.plotly_chart(
            crear_gauge(certificado_total, pim_total, "% Certificado"),
            use_container_width=True,
        )
    with g2:
        st.plotly_chart(
            crear_gauge(compromiso_total, pim_total, "% Compromiso Anual"),
            use_container_width=True,
        )
    with g3:
        st.plotly_chart(
            crear_gauge(devengado_total, pim_total, "% Devengado", es_devengado=True),
            use_container_width=True,
        )

    # Tabla comparativa resumida
    fmt = lambda v, t: f"{v / t * 100:.1f}%" if t > 0 else "—"
    estado = lambda p, m: ("🟢 OK" if p >= m else ("🟡 Cerca" if p >= m - 5 else "🔴 Bajo"))

    p_cert = certificado_total / pim_total * 100  if pim_total else 0
    p_comp = compromiso_total  / pim_total * 100  if pim_total else 0
    p_dev  = devengado_total   / pim_total * 100  if pim_total else 0

    import pandas as pd
    tabla = pd.DataFrame({
        "Indicador":    ["Certificado", "Compromiso Anual", "Devengado"],
        "% del PIM":    [fmt(certificado_total, pim_total),
                         fmt(compromiso_total,  pim_total),
                         fmt(devengado_total,   pim_total)],
        "Meta teórica": ["—", "—", f"{meta_val}%"],
        "Estado":       [
            "🟡 En proceso" if p_cert >= 50 else "🔴 Bajo",
            "🟡 En proceso" if p_comp >= 50 else "🔴 Bajo",
            estado(p_dev, meta_val),
        ],
    })
    st.dataframe(tabla, use_container_width=True, hide_index=True)

# src/components/drilldown_detail.py
# ─────────────────────────────────────────────────────────────────────────────
# Drill-down de clasificadores: muestra el Top 20% por PIM para una genérica
# ─────────────────────────────────────────────────────────────────────────────

import math
import numpy as np
import pandas as pd
import streamlit as st

# ── Jerarquía de clasificadores SIAF ─────────────────────────────────────────
JERARQUIA = [
    "tipo_transaccion",
    "generica",
    "subgenerica",
    "subgenerica_det",
    "especifica",
    "especifica_det",
]

METRICAS = ["PIM", "Certificado", "Compromiso_Anual", "Devengado_Total", "Saldo"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extraer_codigo(valor: str) -> str:
    """'2.CONTRATACION DE SERVICIOS' → '2'"""
    s = str(valor)
    return s.split(".", 1)[0].strip()


def _extraer_nombre(valor: str) -> str:
    """'2.CONTRATACION DE SERVICIOS' → 'CONTRATACION DE SERVICIOS'"""
    s     = str(valor)
    parts = s.split(".", 1)
    return parts[1].strip() if len(parts) > 1 else s.strip()


# ── Construcción de clasificadores ───────────────────────────────────────────

def construir_clasificadores(df: pd.DataFrame, generica: str) -> pd.DataFrame | None:
    """
    Para una genérica dada, construye el código completo del clasificador
    concatenando los códigos numéricos de todos los niveles de la jerarquía.

    Columnas generadas:
        clas_codigo  → '2.3.2.4.7.1'
        clas_nombre  → nombre del último nivel disponible
        clas_display → 'código — nombre'
    """
    dg = df[df["generica"] == generica].copy()
    if dg.empty:
        return None

    campos = [c for c in JERARQUIA if c in dg.columns]
    if not campos:
        return None

    # Código compuesto
    partes = [dg[c].astype(str).apply(_extraer_codigo) for c in campos]
    dg["clas_codigo"] = partes[0]
    for p in partes[1:]:
        dg["clas_codigo"] = dg["clas_codigo"] + "." + p

    # Nombre: último nivel disponible
    dg["clas_nombre"]  = dg[campos[-1]].astype(str).apply(_extraer_nombre)
    dg["clas_display"] = dg["clas_codigo"] + " — " + dg["clas_nombre"]
    return dg


# ── Renderizado del detalle ───────────────────────────────────────────────────

def mostrar_detalle_clasificadores(df_filtrado: pd.DataFrame, generica: str):
    """
    Muestra el desglose de clasificadores del Top 20% por PIM
    de manera desplegable dentro de la tabla resumen.
    """
    if not generica or generica == "TOTAL":
        return

    df_det = construir_clasificadores(df_filtrado, generica)
    if df_det is None or df_det.empty:
        st.warning(f"Sin datos de clasificadores para: **{generica}**")
        return

    mets_disp = [m for m in METRICAS if m in df_det.columns]

    # ── Agrupar por clasificador completo ─────────────────────────────────────
    resumen = (
        df_det
        .groupby(["clas_codigo", "clas_nombre", "clas_display"])[mets_disp]
        .sum()
        .reset_index()
        .sort_values("PIM", ascending=False)
        .reset_index(drop=True)
    )

    total_pim = resumen["PIM"].sum() if "PIM" in resumen.columns else 0
    n_total   = len(resumen)
    n_top     = max(1, math.ceil(n_total * 0.20))
    top       = resumen.head(n_top).copy()
    pim_top   = top["PIM"].sum() if "PIM" in top.columns else 0

    # ── Métricas derivadas ────────────────────────────────────────────────────
    if "PIM" in top.columns:
        top["%_PIM"]    = (top["PIM"] / total_pim * 100).round(2) if total_pim else 0.0
    if "Devengado_Total" in top.columns and "PIM" in top.columns:
        top["%_Ejec"]   = (
            top["Devengado_Total"] / top["PIM"].replace(0, np.nan) * 100
        ).fillna(0).round(1)
    if "PIM" in top.columns and "Certificado" in top.columns:
        top["PIM_vs_Cert"] = top["PIM"] - top["Certificado"]

    # ── KPIs del drill-down ───────────────────────────────────────────────────
    st.markdown(f"##### 🔍 Top 20% de Clasificadores — {generica}")
    k1, k2, k3 = st.columns(3)
    k1.metric("Total clasificadores", n_total)
    k2.metric("Mostrando Top 20%",    n_top)
    k3.metric("PIM concentrado",
              f"{round(pim_top / total_pim * 100, 1)}%" if total_pim else "—")

    st.caption(
        f"Los **{n_top}** clasificadores del Top 20% concentran "
        f"**S/ {round(pim_top):,}** "
        f"({round(pim_top / total_pim * 100, 1) if total_pim else 0}% "
        f"del PIM de esta genérica)."
    )

    # ── Tabla formateada ──────────────────────────────────────────────────────
    fmt_sol = lambda x: f"S/ {round(x):,}".replace(",", ".")

    disp = top.copy()
    for col in ["PIM", "Certificado", "PIM_vs_Cert", "Compromiso_Anual",
                "Devengado_Total", "Saldo"]:
        if col in disp.columns:
            disp[col] = disp[col].apply(fmt_sol)
    if "%_PIM"  in disp.columns:
        disp["%_PIM"]  = disp["%_PIM"].apply(lambda x: f"{x:.2f}%")
    if "%_Ejec" in disp.columns:
        disp["%_Ejec"] = disp["%_Ejec"].apply(lambda x: f"{x:.1f}%")

    cols_mostrar = [c for c in [
        "clas_codigo", "clas_nombre",
        "PIM", "Certificado", "PIM_vs_Cert",
        "Compromiso_Anual", "Devengado_Total", "Saldo",
        "%_PIM", "%_Ejec",
    ] if c in disp.columns]

    col_cfg = {
        "clas_codigo":      st.column_config.TextColumn("Código",      width="small"),
        "clas_nombre":      st.column_config.TextColumn("Nombre",      width="large"),
        "PIM":              st.column_config.TextColumn("PIM",         width="medium"),
        "Certificado":      st.column_config.TextColumn("Certificado", width="medium"),
        "PIM_vs_Cert":      st.column_config.TextColumn("PIM-Cert.",   width="medium"),
        "Compromiso_Anual": st.column_config.TextColumn("Compromiso",  width="medium"),
        "Devengado_Total":  st.column_config.TextColumn("Devengado",   width="medium"),
        "Saldo":            st.column_config.TextColumn("Saldo",       width="medium"),
        "%_PIM":            st.column_config.TextColumn("% PIM",       width="small"),
        "%_Ejec":           st.column_config.TextColumn("% Ejec.",     width="small"),
    }

    st.dataframe(
        disp[cols_mostrar],
        use_container_width=True,
        hide_index=True,
        column_config=col_cfg,
    )

    # ── Descarga ──────────────────────────────────────────────────────────────
    csv = top.to_csv(index=False).encode("utf-8")
    st.download_button(
        f"📥 Descargar Top 20% — {generica[:25]}…",
        csv,
        f"clas_top20_{generica[:20].replace(' ', '_')}.csv",
        "text/csv",
    )

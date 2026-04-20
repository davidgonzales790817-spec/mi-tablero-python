# src/components/summary_table.py
# ─────────────────────────────────────────────────────────────────────────────
# Tabla resumen por Genérica con drill-down integrado
# ─────────────────────────────────────────────────────────────────────────────

import numpy as np
import pandas as pd
import streamlit as st
from components.drilldown_detail import mostrar_detalle_clasificadores

METRICAS = ["PIM", "Certificado", "Compromiso_Anual", "Devengado_Total", "Saldo"]

_fmt = lambda x: f"S/ {round(x):,}".replace(",", ".")


def crear_tabla_resumen(df_filtrado: pd.DataFrame) -> pd.DataFrame:
    """
    Muestra la tabla resumen por Genérica con fila TOTAL
    y un selectbox para desplegar el drill-down de clasificadores
    (Top 20% por PIM) de la genérica elegida.

    Returns:
        DataFrame con el resumen (incluye fila TOTAL).
    """
    st.subheader("📊 Resumen por Genérica")
    st.caption("Selecciona una genérica en el selector inferior para ver el desglose de clasificadores (Top 20% PIM).")

    # ── 1. Construir resumen ──────────────────────────────────────────────────
    mets = [m for m in METRICAS if m in df_filtrado.columns]

    resumen = (
        df_filtrado
        .groupby("generica")[mets]
        .sum()
        .reset_index()
        .sort_values("generica")
        .reset_index(drop=True)
    )

    # Métricas derivadas
    if "PIM" in resumen.columns and "Devengado_Total" in resumen.columns:
        resumen["%_Ejec"] = (
            resumen["Devengado_Total"]
            / resumen["PIM"].replace(0, np.nan) * 100
        ).fillna(0).round(2)

    if "PIM" in resumen.columns and "Certificado" in resumen.columns:
        resumen["PIM_vs_Cert"] = resumen["PIM"] - resumen["Certificado"]

    # ── 2. Fila TOTAL ─────────────────────────────────────────────────────────
    total: dict = {"generica": "TOTAL"}
    for m in mets:
        total[m] = resumen[m].sum()
    if "PIM" in total and "Devengado_Total" in total and total["PIM"]:
        total["%_Ejec"]     = round(total["Devengado_Total"] / total["PIM"] * 100, 2)
    if "PIM" in total and "Certificado" in total:
        total["PIM_vs_Cert"] = total["PIM"] - total["Certificado"]

    full = pd.concat([resumen, pd.DataFrame([total])], ignore_index=True)

    # ── 3. Formatear para display ─────────────────────────────────────────────
    disp = full.copy()
    for col in ["PIM", "Certificado", "PIM_vs_Cert", "Compromiso_Anual",
                "Devengado_Total", "Saldo"]:
        if col in disp.columns:
            disp[col] = disp[col].apply(_fmt)
    if "%_Ejec" in disp.columns:
        disp["%_Ejec"] = disp["%_Ejec"].apply(lambda x: f"{x:.1f}%")

    RENAME = {
        "generica":        "Genérica",
        "PIM":             "PIM",
        "Certificado":     "Certif.",
        "PIM_vs_Cert":     "PIM-Cert.",
        "Compromiso_Anual":"Compromiso",
        "Devengado_Total": "Devengado",
        "Saldo":           "Saldo",
        "%_Ejec":          "% Ejec.",
    }
    COLS = [c for c in RENAME if c in disp.columns]

    st.dataframe(
        disp[COLS].rename(columns=RENAME),
        use_container_width=True,
        hide_index=True,
    )

    # ── 4. Drill-down selectbox ───────────────────────────────────────────────
    st.divider()
    genericas_lista = resumen["generica"].tolist()

    sel = st.selectbox(
        "▼ Ver clasificadores (Top 20% PIM) de:",
        ["— Seleccionar genérica —"] + genericas_lista,
        key="drill_generica_select",
    )

    if sel and not sel.startswith("—"):
        with st.container():
            mostrar_detalle_clasificadores(df_filtrado, sel)

    return full

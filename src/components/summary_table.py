# components/summary_table.py
import streamlit as st
import pandas as pd
import math


# ─────────────────────────────────────────────────────────────
# HELPERS DE CONSTRUCCIÓN DEL CLASIFICADOR
# ─────────────────────────────────────────────────────────────

def _extraer_nombre(valor_str: str) -> str:
    """
    Extrae solo la descripción de una cadena con formato 'N.NOMBRE'.
    Ej: '1.DE MAQUINARIAS Y EQUIPOS'  →  'DE MAQUINARIAS Y EQUIPOS'
    Si no tiene punto, devuelve el texto completo.
    """
    if not isinstance(valor_str, str):
        valor_str = str(valor_str)
    partes = valor_str.split(".", 1)
    return partes[1].strip() if len(partes) > 1 else valor_str.strip()


def _extraer_codigo(valor_str: str) -> str:
    """
    Extrae solo la parte numérica de una cadena con formato 'N.NOMBRE'.
    Ej: '1.DE MAQUINARIAS Y EQUIPOS'  →  '1'
    """
    if not isinstance(valor_str, str):
        valor_str = str(valor_str)
    return valor_str.split(".", 1)[0].strip()


CAMPOS_JERARQUIA = [
    "tipo_transaccion",
    "generica",
    "subgenerica",
    "subgenerica_det",
    "especifica",
    "especifica_det",
]


def construir_clasificador_completo(df: pd.DataFrame, generica_seleccionada: str) -> pd.DataFrame | None:
    """
    Para una genérica dada construye:
      - clasificador_codigo : '2.3.2.4.7.1'
      - clasificador_nombre : nombre del ÚLTIMO nivel disponible (especifica_det)
      - clasificador_display: '2.3.2.4.7.1 "DE MAQUINARIAS Y EQUIPOS"'
    Usa los campos: tipo_transaccion, generica, subgenerica, subgenerica_det, especifica, especifica_det
    """
    df_gen = df[df["generica"] == generica_seleccionada].copy()
    if df_gen.empty:
        return None

    campos = [c for c in CAMPOS_JERARQUIA if c in df_gen.columns]
    if not campos:
        return None

    # Código numérico: extraer solo la parte numérica de cada campo
    codigos = [df_gen[c].astype(str).apply(_extraer_codigo) for c in campos]
    df_gen["clasificador_codigo"] = codigos[0]
    for parte in codigos[1:]:
        df_gen["clasificador_codigo"] = df_gen["clasificador_codigo"] + "." + parte

    # Nombre: último campo disponible
    ultimo_campo = campos[-1]
    df_gen["clasificador_nombre"] = df_gen[ultimo_campo].astype(str).apply(_extraer_nombre)

    # Display completo
    df_gen["clasificador_display"] = (
        df_gen["clasificador_codigo"] + ' "' + df_gen["clasificador_nombre"] + '"'
    )

    return df_gen


# ─────────────────────────────────────────────────────────────
# DETALLE DE CLASIFICADORES (DRILL-DOWN)
# ─────────────────────────────────────────────────────────────

METRICAS = ["PIM", "Certificado", "Compromiso_Anual", "Devengado_Total", "Saldo"]


def mostrar_detalle_clasificadores(df_filtrado: pd.DataFrame, generica_seleccionada: str):
    """
    Muestra el desglose de clasificadores para una genérica específica.
    Aplica la regla de Pareto (Top 20%) y las mismas métricas del resumen por genérica.
    """
    if not generica_seleccionada or generica_seleccionada == "TOTAL":
        return

    st.markdown("---")
    st.markdown(f"## 📋 Desglose de: **{generica_seleccionada}**")

    # ── 1. Construir clasificadores ──────────────────────────
    df_detalle = construir_clasificador_completo(df_filtrado, generica_seleccionada)
    if df_detalle is None or df_detalle.empty:
        st.warning(f"No hay datos de clasificadores para {generica_seleccionada}")
        return

    metricas_disponibles = [m for m in METRICAS if m in df_detalle.columns]

    # ── 2. Agrupar por clasificador completo ─────────────────
    resumen = (
        df_detalle
        .groupby(["clasificador_codigo", "clasificador_nombre", "clasificador_display"])[metricas_disponibles]
        .sum()
        .reset_index()
    )

    total_pim = resumen["PIM"].sum() if "PIM" in resumen.columns else 0

    # Métricas derivadas
    if "PIM" in resumen.columns:
        resumen["%_PIM"] = (resumen["PIM"] / total_pim * 100).round(2) if total_pim > 0 else 0.0
    if "Devengado_Total" in resumen.columns and "PIM" in resumen.columns:
        resumen["%_Ejecucion"] = (resumen["Devengado_Total"] / resumen["PIM"].replace(0, pd.NA) * 100).round(2).fillna(0)
    if "PIM" in resumen.columns and "Certificado" in resumen.columns:
        resumen["PIM_-_Certificado"] = resumen["PIM"] - resumen["Certificado"]

    # Ordenar de mayor a menor PIM
    resumen = resumen.sort_values("PIM", ascending=False).reset_index(drop=True)

    # ── 3. Regla de Pareto: Top 20% ──────────────────────────
    total_clasificadores = len(resumen)
    top_n_pareto = max(1, math.ceil(total_clasificadores * 0.20))

    # Mostrar indicadores de contexto (apilados — se ven bien en móvil)
    st.metric("Total clasificadores", total_clasificadores)
    st.metric("Mostrando Top 20%", top_n_pareto)
    st.metric("PIM Total", f"S/ {total_pim:,.0f}")

    resumen_pareto = resumen.head(top_n_pareto).copy()

    pim_pareto = resumen_pareto["PIM"].sum() if "PIM" in resumen_pareto.columns else 0
    pct_concentracion = (pim_pareto / total_pim * 100) if total_pim > 0 else 0
    st.info(
        f"📌 Los **{top_n_pareto} clasificadores** del Top 20% concentran el "
        f"**{pct_concentracion:.1f}%** del PIM total de {generica_seleccionada}."
    )

    # ── 4. Tabla de clasificadores (Top 20%) ─────────────────
    st.subheader(f"Top 20% de Clasificadores por PIM — {generica_seleccionada}")

    display_df = resumen_pareto.copy()
    for col in ["PIM", "Certificado", "PIM_-_Certificado", "Compromiso_Anual", "Devengado_Total", "Saldo"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"S/ {x:,.0f}")
    if "%_PIM" in display_df.columns:
        display_df["%_PIM"] = display_df["%_PIM"].apply(lambda x: f"{x:.2f}%")
    if "%_Ejecucion" in display_df.columns:
        display_df["%_Ejecucion"] = display_df["%_Ejecucion"].apply(lambda x: f"{x:.1f}%")

    column_config = {
        "clasificador_codigo":  st.column_config.TextColumn("Código",       width="small"),
        "clasificador_nombre":  st.column_config.TextColumn("Nombre",        width="large"),
        "clasificador_display": st.column_config.TextColumn("Clasificador",  width="large"),
        "PIM":                  st.column_config.TextColumn("PIM",           width="medium"),
        "Certificado":          st.column_config.TextColumn("Certificado",   width="medium"),
        "PIM_-_Certificado":    st.column_config.TextColumn("PIM-Cert.",     width="medium"),
        "Compromiso_Anual":     st.column_config.TextColumn("Compromiso",    width="medium"),
        "Devengado_Total":      st.column_config.TextColumn("Devengado",     width="medium"),
        "Saldo":                st.column_config.TextColumn("Saldo",         width="medium"),
        "%_PIM":                st.column_config.TextColumn("% PIM",         width="small"),
        "%_Ejecucion":          st.column_config.TextColumn("% Ejec.",       width="small"),
    }

    cols_mostrar = [c for c in [
        "clasificador_codigo", "clasificador_nombre",
        "PIM", "Certificado", "PIM_-_Certificado",
        "Compromiso_Anual", "Devengado_Total", "Saldo",
        "%_PIM", "%_Ejecucion"
    ] if c in display_df.columns]

    st.dataframe(
        display_df[cols_mostrar],
        use_container_width=True,
        column_config=column_config,
    )

    # ── 5. Descarga del Top 20% ───────────────────────────────
    csv = resumen_pareto.to_csv(index=False)
    st.download_button(
        "📥 Descargar Top 20% clasificadores (CSV)",
        csv,
        f"clasificadores_top20_{generica_seleccionada.replace(' ', '_')}.csv",
        "text/csv",
    )


# ─────────────────────────────────────────────────────────────
# TABLA RESUMEN POR GENÉRICA (con drill-down)
# ─────────────────────────────────────────────────────────────

def crear_tabla_resumen(df_filtrado: pd.DataFrame):
    """
    Tabla resumen por Genérica con botón drill-down por fila.
    Al hacer clic en una genérica se despliega el desglose de clasificadores
    (Top 20% por PIM) justo debajo de esa fila.
    """
    st.subheader("📊 Resumen por Genérica")
    st.caption("💡 **Haga clic en 🔍** para ver el desglose de clasificadores (Top 20% por PIM)")

    # ── 1. Construir resumen por genérica ────────────────────
    metricas_disponibles = [m for m in METRICAS if m in df_filtrado.columns]

    resumen = (
        df_filtrado
        .groupby("generica")[metricas_disponibles]
        .sum()
        .reset_index()
        .sort_values("generica")
        .reset_index(drop=True)
    )

    if "PIM" in resumen.columns and "Devengado_Total" in resumen.columns:
        resumen["%_Ejecucion"] = (
            resumen["Devengado_Total"] / resumen["PIM"].replace(0, pd.NA) * 100
        ).round(2).fillna(0)
    if "PIM" in resumen.columns and "Certificado" in resumen.columns:
        resumen["PIM_-_Certificado"] = resumen["PIM"] - resumen["Certificado"]

    # Fila TOTAL
    total_vals: dict = {"generica": "TOTAL"}
    for m in metricas_disponibles:
        total_vals[m] = resumen[m].sum()
    if "PIM" in total_vals and "Devengado_Total" in total_vals:
        total_vals["%_Ejecucion"] = round(
            total_vals["Devengado_Total"] / total_vals["PIM"] * 100, 2
        ) if total_vals["PIM"] else 0.0
    if "PIM" in total_vals and "Certificado" in total_vals:
        total_vals["PIM_-_Certificado"] = total_vals["PIM"] - total_vals["Certificado"]

    total_row = pd.DataFrame([total_vals])
    resumen = pd.concat([resumen, total_row], ignore_index=True)

    # Formatear para display
    resumen_display = resumen.copy()
    for col in ["PIM", "Certificado", "PIM_-_Certificado", "Compromiso_Anual", "Devengado_Total", "Saldo"]:
        if col in resumen_display.columns:
            resumen_display[col] = resumen_display[col].apply(lambda x: f"S/ {x:,.0f}")
    if "%_Ejecucion" in resumen_display.columns:
        resumen_display["%_Ejecucion"] = resumen_display["%_Ejecucion"].apply(lambda x: f"{x:.1f}%")

    # ── 2. Session state ──────────────────────────────────────
    if "generica_seleccionada_detalle" not in st.session_state:
        st.session_state.generica_seleccionada_detalle = None

    # ── 3. Tabla resumen (scroll horizontal nativo en móvil) ──
    COLS_TABLA = ["generica"] + [
        c for c in ["PIM", "Certificado", "PIM_-_Certificado",
                    "Compromiso_Anual", "Devengado_Total", "Saldo", "%_Ejecucion"]
        if c in resumen_display.columns
    ]
    RENAME = {
        "generica": "Genérica", "PIM": "PIM", "Certificado": "Cert.",
        "PIM_-_Certificado": "PIM-Cert.", "Compromiso_Anual": "Compromiso",
        "Devengado_Total": "Devengado", "Saldo": "Saldo", "%_Ejecucion": "% Ejec.",
    }

    st.dataframe(
        resumen_display[COLS_TABLA].rename(columns=RENAME),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # ── 4. Selectbox drill-down (funciona perfectamente en móvil) ──
    genericas_disponibles = [g for g in resumen["generica"].tolist() if g != "TOTAL"]

    seleccion = st.selectbox(
        "🔍 Ver desglose de clasificadores (Top 20% PIM)",
        options=["— Seleccione una genérica —"] + genericas_disponibles,
        index=0,
        key="selectbox_generica_drill",
    )

    generica_elegida = None if seleccion.startswith("—") else seleccion
    st.session_state.generica_seleccionada_detalle = generica_elegida

    # Drill-down debajo del selector
    if generica_elegida:
        mostrar_detalle_clasificadores(df_filtrado, generica_elegida)

    return resumen

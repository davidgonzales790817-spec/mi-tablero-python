# components/summary_table.py
import pandas as pd
import streamlit as st

def crear_tabla_resumen(df_filtrado):
    st.subheader("Resumen por Genérica")

    resumen = df_filtrado.groupby("generica").agg({
        "PIM": "sum",
        "Certificado": "sum",
        "Compromiso_Anual": "sum",
        "Devengado_Total": "sum",
        "Saldo": "sum"
    }).reset_index()

    resumen["%_Ejecucion"] = (resumen["Devengado_Total"] / resumen["PIM"] * 100).round(2)
    resumen["PIM_-_Certificado"] = resumen["PIM"] - resumen["Certificado"]

    resumen = resumen.sort_values("generica").reset_index(drop=True)

    # Formato para mostrar
    resumen_display = resumen.copy()
    for col in ["PIM", "Certificado", "PIM_-_Certificado", "Compromiso_Anual", "Devengado_Total", "Saldo"]:
        if col in resumen_display.columns:
            resumen_display[col] = resumen_display[col].apply(lambda x: f"S/ {x:,.0f}")
    resumen_display["%_Ejecucion"] = resumen_display["%_Ejecucion"].apply(lambda x: f"{x}%")

    # Agregar fila de total
    total_row = pd.DataFrame({
        "generica": ["TOTAL"],
        "PIM": [f"S/ {resumen['PIM'].sum():,.0f}"],
        "Certificado": [f"S/ {resumen['Certificado'].sum():,.0f}"],
        "PIM_-_Certificado": [f"S/ {resumen['PIM'].sum() - resumen['Certificado'].sum():,.0f}"],
        "Compromiso_Anual": [f"S/ {resumen['Compromiso_Anual'].sum():,.0f}"],
        "Devengado_Total": [f"S/ {resumen['Devengado_Total'].sum():,.0f}"],
        "Saldo": [f"S/ {resumen['Saldo'].sum():,.0f}"],
        "%_Ejecucion": [f"{(resumen['Devengado_Total'].sum() / resumen['PIM'].sum() * 100):.1f}%"]
    })

    resumen_display = pd.concat([resumen_display, total_row], ignore_index=True)
    st.dataframe(resumen_display, use_container_width=True)

    return resumen

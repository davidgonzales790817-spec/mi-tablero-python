# components/summary_table.py
import streamlit as st
import pandas as pd
import plotly.express as px

def construir_clasificador_completo(df, generica_seleccionada):
    """
    Construye el clasificador jerárquico completo para una genérica específica
    Formato: generica.subgenerica.subgenerica_det.especifica.especifica_det
    """
    # Filtrar por la genérica seleccionada
    df_gen = df[df["generica"] == generica_seleccionada].copy()
    
    if df_gen.empty:
        return None
    
    # Campos jerárquicos en orden
    campos_jerarquia = ["generica", "subgenerica", "subgenerica_det", "especifica", "especifica_det"]
    campos_existentes = [c for c in campos_jerarquia if c in df_gen.columns]
    
    if not campos_existentes:
        return None
    
    # Construir el código jerárquico (ej: 2.3.2.4.2.1)
    codigo = df_gen[campos_existentes[0]].astype(str)
    for campo in campos_existentes[1:]:
        codigo = codigo + "." + df_gen[campo].astype(str)
    
    # Construir la descripción jerárquica (ej: 2 > 3 > 2 > 4 > 2 > 1)
    descripcion = df_gen[campos_existentes[0]].astype(str)
    for campo in campos_existentes[1:]:
        descripcion = descripcion + " > " + df_gen[campo].astype(str)
    
    df_gen["clasificador_codigo"] = codigo
    df_gen["clasificador_descripcion"] = descripcion
    
    return df_gen

def mostrar_detalle_clasificadores(df_filtrado, generica_seleccionada):
    """
    Muestra el detalle de clasificadores para una genérica específica
    """
    if not generica_seleccionada or generica_seleccionada == "TOTAL":
        return
    
    st.markdown("---")
    st.markdown(f"## 📋 Desglose de: **{generica_seleccionada}**")
    
    # Construir el clasificador jerárquico
    df_detalle = construir_clasificador_completo(df_filtrado, generica_seleccionada)
    
    if df_detalle is None or df_detalle.empty:
        st.warning(f"No hay datos de clasificadores para {generica_seleccionada}")
        return
    
    # ============================================
    # 1. AGRUPAR POR CLASIFICADOR COMPLETO
    # ============================================
    # Usar el código jerárquico como identificador único
    resumen = df_detalle.groupby(["clasificador_codigo", "clasificador_descripcion"]).agg({
        "PIM": "sum",
        "Certificado": "sum",
        "Compromiso_Anual": "sum",
        "Devengado_Total": "sum",
        "Saldo": "sum"
    }).reset_index()
    
    # Calcular porcentajes
    total_pim = resumen["PIM"].sum()
    resumen["%_PIM"] = (resumen["PIM"] / total_pim * 100).round(2) if total_pim > 0 else 0
    resumen["%_Ejecucion"] = (resumen["Devengado_Total"] / resumen["PIM"] * 100).round(2)
    resumen["PIM_-_Certificado"] = resumen["PIM"] - resumen["Certificado"]
    
    # Ordenar por PIM de mayor a menor
    resumen = resumen.sort_values("PIM", ascending=False)
    
    # ============================================
    # 2. MOSTRAR TABLA DE CLASIFICADORES
    # ============================================
    st.subheader(f"Clasificadores de {generica_seleccionada}")
    st.caption(f"Total de clasificadores: {len(resumen)} | PIM Total: S/ {total_pim:,.0f}")
    
    # Formatear para mostrar
    resumen_display = resumen.copy()
    resumen_display["PIM"] = resumen_display["PIM"].apply(lambda x: f"S/ {x:,.0f}")
    resumen_display["Certificado"] = resumen_display["Certificado"].apply(lambda x: f"S/ {x:,.0f}")
    resumen_display["PIM_-_Certificado"] = resumen_display["PIM_-_Certificado"].apply(lambda x: f"S/ {x:,.0f}")
    resumen_display["Compromiso_Anual"] = resumen_display["Compromiso_Anual"].apply(lambda x: f"S/ {x:,.0f}")
    resumen_display["Devengado_Total"] = resumen_display["Devengado_Total"].apply(lambda x: f"S/ {x:,.0f}")
    resumen_display["Saldo"] = resumen_display["Saldo"].apply(lambda x: f"S/ {x:,.0f}")
    resumen_display["%_PIM"] = resumen_display["%_PIM"].apply(lambda x: f"{x}%")
    resumen_display["%_Ejecucion"] = resumen_display["%_Ejecucion"].apply(lambda x: f"{x}%")
    
    # Mostrar tabla
    st.dataframe(
        resumen_display,
        use_container_width=True,
        column_config={
            "clasificador_codigo": st.column_config.TextColumn("Código", width="small"),
            "clasificador_descripcion": st.column_config.TextColumn("Descripción", width="large"),
            "PIM": st.column_config.TextColumn("PIM", width="medium"),
            "Certificado": st.column_config.TextColumn("Certificado", width="medium"),
            "PIM_-_Certificado": st.column_config.TextColumn("PIM - Certificado", width="medium"),
            "Compromiso_Anual": st.column_config.TextColumn("Compromiso", width="medium"),
            "Devengado_Total": st.column_config.TextColumn("Devengado", width="medium"),
            "Saldo": st.column_config.TextColumn("Saldo", width="medium"),
            "%_PIM": st.column_config.TextColumn("% PIM", width="small"),
            "%_Ejecucion": st.column_config.TextColumn("% Ejec.", width="small")
        }
    )
    
    # ============================================
    # 3. GRÁFICO DE BARRAS (Top 10)
    # ============================================
    top_n = min(10, len(resumen))
    if top_n > 1:
        st.subheader(f"Top {top_n} Clasificadores por PIM")
        
        resumen_top = resumen.head(top_n)
        # Crear etiqueta corta para el gráfico
        resumen_top["etiqueta"] = resumen_top["clasificador_codigo"] + " - " + resumen_top["clasificador_descripcion"].str[:40]
        
        fig = px.bar(
            resumen_top,
            x="etiqueta",
            y="PIM",
            title=f"Top {top_n} clasificadores - {generica_seleccionada}",
            labels={"PIM": "Monto (Soles)", "etiqueta": "Clasificador"},
            text_auto='.2s'
        )
        fig.update_layout(height=450, xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    # ============================================
    # 4. OPCIÓN DE DESCARGA
    # ============================================
    csv = resumen.to_csv(index=False)
    st.download_button(
        "📥 Descargar detalle de clasificadores (CSV)",
        csv,
        f"clasificadores_{generica_seleccionada.replace(' ', '_')}.csv",
        "text/csv"
    )

def crear_tabla_resumen(df_filtrado):
    """
    Crea una tabla resumen interactiva donde al hacer clic se muestra el detalle
    """
    st.subheader("📊 Resumen por Genérica")
    st.caption("💡 **Haga clic en cualquier genérica** para ver el desglose de sus clasificadores")
    
    # ============================================
    # 1. CREAR TABLA RESUMEN
    # ============================================
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
    
    # Agregar fila de total
    total_row = pd.DataFrame({
        "generica": ["TOTAL"],
        "PIM": [resumen["PIM"].sum()],
        "Certificado": [resumen["Certificado"].sum()],
        "Compromiso_Anual": [resumen["Compromiso_Anual"].sum()],
        "Devengado_Total": [resumen["Devengado_Total"].sum()],
        "Saldo": [resumen["Saldo"].sum()],
        "%_Ejecucion": [(resumen["Devengado_Total"].sum() / resumen["PIM"].sum() * 100)],
        "PIM_-_Certificado": [resumen["PIM"].sum() - resumen["Certificado"].sum()]
    })
    resumen = pd.concat([resumen, total_row], ignore_index=True)
    
    # Formatear para mostrar
    resumen_display = resumen.copy()
    for col in ["PIM", "Certificado", "PIM_-_Certificado", "Compromiso_Anual", "Devengado_Total", "Saldo"]:
        if col in resumen_display.columns:
            resumen_display[col] = resumen_display[col].apply(lambda x: f"S/ {x:,.0f}")
    resumen_display["%_Ejecucion"] = resumen_display["%_Ejecucion"].apply(lambda x: f"{x:.1f}%")
    
    # ============================================
    # 2. MOSTRAR TABLA CON BOTONES POR FILA
    # ============================================
    # Inicializar session_state para controlar qué genérica está seleccionada
    if "generica_seleccionada_detalle" not in st.session_state:
        st.session_state.generica_seleccionada_detalle = None
    
    # Mostrar cada fila con un botón "Ver detalle"
    for idx, row in resumen_display.iterrows():
        generica = row["generica"]
        
        # Crear columnas: [Botón, Datos de la fila]
        col1, col2 = st.columns([1, 8])
        
        with col1:
            # Botón para ver detalle
            if st.button(f"🔍", key=f"btn_{generica}", help=f"Ver detalle de {generica}"):
                if st.session_state.generica_seleccionada_detalle == generica:
                    st.session_state.generica_seleccionada_detalle = None  # Cerrar
                else:
                    st.session_state.generica_seleccionada_detalle = generica  # Abrir
                st.rerun()
        
        with col2:
            # Mostrar la fila como texto formateado
            cols_data = st.columns(len(row))
            for i, (col_name, col_value) in enumerate(row.items()):
                with cols_data[i]:
                    if col_name == "generica":
                        st.markdown(f"**{col_value}**")
                    else:
                        st.write(col_value)
        
        # Si esta genérica está seleccionada, mostrar el detalle debajo
        if st.session_state.generica_seleccionada_detalle == generica and generica != "TOTAL":
            mostrar_detalle_clasificadores(df_filtrado, generica)
    
    return resumen

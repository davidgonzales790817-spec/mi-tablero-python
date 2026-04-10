# components/drilldown_detail.py
import streamlit as st
import pandas as pd
import plotly.express as px

def mostrar_detalle_clasificadores(df_filtrado, generica_seleccionada, columna_clasificador):
    """
    Muestra un detalle desglosado de los clasificadores de gasto para una genérica específica
    """
    if not generica_seleccionada or generica_seleccionada == "TOTAL":
        return None
    
    # Filtrar datos por la genérica seleccionada
    df_gen = df_filtrado[df_filtrado["generica"] == generica_seleccionada]
    
    if df_gen.empty:
        st.warning(f"No hay datos para la genérica: {generica_seleccionada}")
        return None
    
    # Verificar que la columna clasificador exista
    if columna_clasificador not in df_gen.columns:
        st.info(f"La columna '{columna_clasificador}' no está disponible en los datos")
        return None
    
    # Agrupar por el clasificador
    resumen = df_gen.groupby(columna_clasificador).agg({
        "PIM": "sum",
        "Devengado_Total": "sum",
        "Saldo": "sum"
    }).reset_index()
    
    # Calcular porcentajes
    total_pim = resumen["PIM"].sum()
    resumen["%_PIM"] = (resumen["PIM"] / total_pim * 100).round(2)
    resumen["%_Ejecucion"] = (resumen["Devengado_Total"] / resumen["PIM"] * 100).round(2)
    
    # Ordenar por PIM de mayor a menor
    resumen = resumen.sort_values("PIM", ascending=False)
    
    # Mostrar top 10 (o menos si hay pocos)
    top_n = min(10, len(resumen))
    resumen_top = resumen.head(top_n)
    
    # Formatear para mostrar
    resumen_display = resumen_top.copy()
    resumen_display["PIM"] = resumen_display["PIM"].apply(lambda x: f"S/ {x:,.0f}")
    resumen_display["Devengado_Total"] = resumen_display["Devengado_Total"].apply(lambda x: f"S/ {x:,.0f}")
    resumen_display["Saldo"] = resumen_display["Saldo"].apply(lambda x: f"S/ {x:,.0f}")
    resumen_display["%_PIM"] = resumen_display["%_PIM"].apply(lambda x: f"{x}%")
    resumen_display["%_Ejecucion"] = resumen_display["%_Ejecucion"].apply(lambda x: f"{x}%")
    
    # Mostrar título
    st.markdown(f"### 📋 Detalle de {columna_clasificador} para: **{generica_seleccionada}**")
    st.caption(f"Mostrando los {top_n} de {len(resumen)} clasificadores (ordenados por PIM de mayor a menor)")
    
    # Mostrar tabla
    st.dataframe(resumen_display, use_container_width=True)
    
    # Gráfico de barras
    fig = px.bar(
        resumen_top,
        x=columna_clasificador,
        y="PIM",
        title=f"Top {top_n} {columna_clasificador} por PIM - {generica_seleccionada}",
        labels={"PIM": "Monto (Soles)", columna_clasificador: "Clasificador"},
        text_auto='.2s'
    )
    fig.update_layout(height=450, xaxis_tickangle=45)
    st.plotly_chart(fig, use_container_width=True)
    
    return resumen

def crear_tabla_con_drilldown(df_filtrado):
    """
    Crea una tabla resumen con selector de genérica para ver detalle de clasificadores
    """
    st.subheader("📊 Resumen por Genérica")
    
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
    
    # Mostrar tabla
    st.dataframe(
        resumen_display,
        use_container_width=True,
        column_config={
            "generica": st.column_config.TextColumn("Genérica", width="medium"),
        }
    )
    
    # ============================================
    # 2. DRILLDOWN - Selección de genérica
    # ============================================
    st.markdown("---")
    st.markdown("### 🔍 Desglose por clasificador de gasto")
    st.markdown("Seleccione una genérica para ver sus clasificadores más relevantes (ordenados por PIM):")
    
    # Opciones de genérica (excluyendo TOTAL)
    opciones_genericas = resumen[resumen["generica"] != "TOTAL"]["generica"].tolist()
    
    col1, col2 = st.columns([2, 1])
    with col1:
        generica_seleccionada = st.selectbox(
            "📌 Seleccionar Genérica:",
            options=opciones_genericas,
            key="drilldown_generica"
        )
    
    # Detectar columnas de clasificadores disponibles
    with col2:
        # Buscar columnas que podrían ser clasificadores
        posibles_clasificadores = []
        for col in df_filtrado.columns:
            if any(p in col.lower() for p in ["proyecto", "actividad", "rubro", "clasificador", "sec_func", "secfunc", "secuencia", "funcional", "fuente", "cadena", "funcion", "division", "grupo"]):
                posibles_clasificadores.append(col)
        
        # Si no se encontraron clasificadores específicos, buscar columnas de texto
        if not posibles_clasificadores:
            for col in df_filtrado.columns:
                if df_filtrado[col].dtype == 'object' and col not in ["generica", "pliego", "unidad_ejecutora", "ano_eje"]:
                    posibles_clasificadores.append(col)
        
        if posibles_clasificadores:
            clasificador_seleccionado = st.selectbox(
                "📂 Tipo de clasificador:",
                options=posibles_clasificadores,
                key="tipo_clasificador"
            )
        else:
            st.warning("No se encontraron columnas de clasificadores en los datos")
            clasificador_seleccionado = None
    
    # ============================================
    # 3. MOSTRAR DETALLE
    # ============================================
    if generica_seleccionada and clasificador_seleccionado:
        with st.expander(f"📋 Ver detalle de {clasificador_seleccionado} para {generica_seleccionada}", expanded=True):
            mostrar_detalle_clasificadores(
                df_filtrado, 
                generica_seleccionada, 
                clasificador_seleccionado
            )
    
    return resumen

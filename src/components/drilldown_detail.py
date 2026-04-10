# components/drilldown_detail.py
import streamlit as st
import pandas as pd
import plotly.express as px

def obtener_posibles_clasificadores(df_filtrado):
    """
    Detecta y retorna las columnas de clasificadores disponibles en los datos
    """
    posibles_clasificadores = []
    
    # Buscar columnas que podrían ser clasificadores
    for col in df_filtrado.columns:
        if any(p in col.lower() for p in ["proyecto", "actividad", "rubro", "clasificador", 
                                            "sec_func", "secfunc", "secuencia", "funcional", 
                                            "fuente", "cadena", "funcion", "division", "grupo"]):
            posibles_clasificadores.append(col)
    
    # Si no se encontraron clasificadores específicos, buscar columnas de texto
    if not posibles_clasificadores:
        for col in df_filtrado.columns:
            if df_filtrado[col].dtype == 'object' and col not in ["generica", "pliego", "unidad_ejecutora", "ano_eje"]:
                posibles_clasificadores.append(col)
    
    return posibles_clasificadores

def mostrar_detalle_clasificadores(df_filtrado, generica_seleccionada, columna_clasificador, mostrar_grafico=True):
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
    
    # Mostrar tabla sin título ni caption (se muestra en el expander)
    st.dataframe(resumen_display, use_container_width=True, hide_index=True)
    
    # Gráfico de barras (opcional)
    if mostrar_grafico and len(resumen_top) > 0:
        fig = px.bar(
            resumen_top,
            x=columna_clasificador,
            y="PIM",
            title=f"Top {top_n} {columna_clasificador} por PIM",
            labels={"PIM": "Monto (Soles)", columna_clasificador: "Clasificador"},
            text_auto='.2s'
        )
        fig.update_layout(height=350, xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    return resumen

def crear_tabla_con_drilldown(df_filtrado):
    """
    Crea una tabla resumen con expanders por cada genérica para ver detalles de clasificadores
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
    
    # Guardar resumen sin total para iteración
    resumen_sin_total = resumen.copy()
    
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
    resumen_display = pd.concat([resumen, total_row], ignore_index=True)
    
    # Formatear para mostrar
    resumen_display_fmt = resumen_display.copy()
    for col in ["PIM", "Certificado", "PIM_-_Certificado", "Compromiso_Anual", "Devengado_Total", "Saldo"]:
        if col in resumen_display_fmt.columns:
            resumen_display_fmt[col] = resumen_display_fmt[col].apply(lambda x: f"S/ {x:,.0f}")
    resumen_display_fmt["%_Ejecucion"] = resumen_display_fmt["%_Ejecucion"].apply(lambda x: f"{x:.1f}%")
    
    # Mostrar tabla
    st.dataframe(
        resumen_display_fmt,
        use_container_width=True,
        column_config={
            "generica": st.column_config.TextColumn("Genérica", width="medium"),
        },
        hide_index=True
    )
    
    # ============================================
    # 2. DETECTAR CLASIFICADORES DISPONIBLES
    # ============================================
    posibles_clasificadores = obtener_posibles_clasificadores(df_filtrado)
    
    if not posibles_clasificadores:
        st.warning("⚠️ No se encontraron columnas de clasificadores en los datos")
        return resumen
    
    # ============================================
    # 3. SELECTOR GLOBAL DE TIPO DE CLASIFICADOR
    # ============================================
    st.markdown("---")
    st.markdown("### 🔍 Desglose por clasificador de gasto")
    
    clasificador_seleccionado = st.selectbox(
        "📂 Seleccione el tipo de clasificador a visualizar:",
        options=posibles_clasificadores,
        key="tipo_clasificador_global"
    )
    
    # ============================================
    # 4. EXPANDERS POR CADA GENÉRICA
    # ============================================
    st.markdown("**Haga clic en cada genérica para ver su desglose:**")
    
    for idx, row in resumen_sin_total.iterrows():
        generica = row["generica"]
        pim = row["PIM"]
        ejecucion = row["%_Ejecucion"]
        
        # Crear header para el expander con información resumida
        header_text = f"📦 {generica} | PIM: S/ {pim:,.0f} | Ejecución: {ejecucion:.1f}%"
        
        with st.expander(header_text, expanded=False):
            st.markdown(f"**Detalle de {clasificador_seleccionado}**")
            mostrar_detalle_clasificadores(
                df_filtrado,
                generica,
                clasificador_seleccionado,
                mostrar_grafico=True
            )
    
    # ============================================
    # 5. VISTA ALTERNATIVA: TABLA COMBINADA (OPCIONAL)
    # ============================================
    if st.checkbox("📊 Mostrar vista de tabla combinada", value=False):
        st.markdown("### Vista combinada: Todas las genéricas")
        
        # Crear tabla con todas las genéricas y sus clasificadores
        datos_combinados = []
        
        for _, row in resumen_sin_total.iterrows():
            generica = row["generica"]
            df_gen = df_filtrado[df_filtrado["generica"] == generica]
            
            if clasificador_seleccionado in df_gen.columns:
                resumen_gen = df_gen.groupby(clasificador_seleccionado).agg({
                    "PIM": "sum",
                    "Devengado_Total": "sum"
                }).reset_index()
                
                resumen_gen["generica"] = generica
                resumen_gen["%_Ejecucion"] = (resumen_gen["Devengado_Total"] / resumen_gen["PIM"] * 100).round(2)
                datos_combinados.append(resumen_gen)
        
        if datos_combinados:
            tabla_combinada = pd.concat(datos_combinados, ignore_index=True)
            tabla_combinada = tabla_combinada.sort_values(["generica", "PIM"], ascending=[True, False])
            
            # Formatear
            tabla_combinada_fmt = tabla_combinada.copy()
            tabla_combinada_fmt["PIM"] = tabla_combinada_fmt["PIM"].apply(lambda x: f"S/ {x:,.0f}")
            tabla_combinada_fmt["Devengado_Total"] = tabla_combinada_fmt["Devengado_Total"].apply(lambda x: f"S/ {x:,.0f}")
            tabla_combinada_fmt["%_Ejecucion"] = tabla_combinada_fmt["%_Ejecucion"].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(tabla_combinada_fmt, use_container_width=True, hide_index=True)
    
    return resumen

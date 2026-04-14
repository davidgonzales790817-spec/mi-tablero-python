# components/summary_table.py
import streamlit as st
import pandas as pd
import plotly.express as px

def construir_clasificador(df):
    """
    Construye un clasificador jerárquico a partir de múltiples campos
    Formato: generica.subgenerica.subgenerica_det.especifica.especifica_det
    """
    # Lista de posibles campos en orden jerárquico
    campos_jerarquia = ["generica", "subgenerica", "subgenerica_det", "especifica", "especifica_det"]
    
    # Verificar qué campos existen en el DataFrame
    campos_existentes = [campo for campo in campos_jerarquia if campo in df.columns]
    
    if not campos_existentes:
        return None
    
    # Crear el clasificador concatenando los campos
    df = df.copy()
    df["clasificador_completo"] = ""
    df["clasificador_codigo"] = ""
    df["clasificador_descripcion"] = ""
    
    for i, campo in enumerate(campos_existentes):
        # Separador
        separador = " > " if i > 0 else ""
        df["clasificador_completo"] = df["clasificador_completo"] + separador + df[campo].astype(str)
        
        # Para el código (solo los valores numéricos/códigos)
        if campo == "generica":
            df["clasificador_codigo"] = df["clasificador_codigo"] + df[campo].astype(str)
            df["clasificador_descripcion"] = df["clasificador_descripcion"] + df[campo].astype(str)
        else:
            df["clasificador_codigo"] = df["clasificador_codigo"] + "." + df[campo].astype(str)
            df["clasificador_descripcion"] = df["clasificador_descripcion"] + " - " + df[campo].astype(str)
    
    return df["clasificador_completo"]

def detectar_columnas_clasificador(df):
    """
    Detecta las columnas que pueden usarse como clasificador
    """
    clasificadores = []
    
    # 1. Clasificador jerárquico construido
    if "generica" in df.columns:
        clasificadores.append("📊 Clasificador Jerárquico (Completo)")
    
    # 2. Campos individuales
    campos_clasificador = {
        "generica": "📁 Genérica",
        "subgenerica": "📂 Subgenérica",
        "subgenerica_det": "📄 Subgenérica Detallada",
        "especifica": "🔖 Específica",
        "especifica_det": "🏷️ Específica Detallada"
    }
    
    for campo, nombre in campos_clasificador.items():
        if campo in df.columns:
            clasificadores.append(nombre)
    
    # 3. Otros campos comunes
    otros_campos = ["proyecto", "actividad", "rubro", "fuente_financiamiento", "sec_func", "sec_funcional"]
    for campo in otros_campos:
        if campo in df.columns:
            clasificadores.append(f"📌 {campo.replace('_', ' ').title()}")
    
    return clasificadores

def obtener_datos_clasificador(df, tipo_clasificador):
    """
    Obtiene los datos del clasificador según el tipo seleccionado
    """
    if tipo_clasificador == "📊 Clasificador Jerárquico (Completo)":
        # Construir el clasificador jerárquico
        campos_jerarquia = ["generica", "subgenerica", "subgenerica_det", "especifica", "especifica_det"]
        campos_existentes = [c for c in campos_jerarquia if c in df.columns]
        
        if campos_existentes:
            # Crear el clasificador completo
            df_temp = df.copy()
            clasificador = df_temp[campos_existentes[0]].astype(str)
            for campo in campos_existentes[1:]:
                clasificador = clasificador + "." + df_temp[campo].astype(str)
            return clasificador
        return None
    
    elif "Genérica" in tipo_clasificador:
        return df["generica"] if "generica" in df.columns else None
    elif "Subgenérica" in tipo_clasificador:
        return df["subgenerica"] if "subgenerica" in df.columns else None
    elif "Subgenérica Detallada" in tipo_clasificador:
        return df["subgenerica_det"] if "subgenerica_det" in df.columns else None
    elif "Específica" in tipo_clasificador:
        return df["especifica"] if "especifica" in df.columns else None
    elif "Específica Detallada" in tipo_clasificador:
        return df["especifica_det"] if "especifica_det" in df.columns else None
    else:
        # Buscar por nombre
        for col in df.columns:
            if col.lower().replace("_", " ") in tipo_clasificador.lower():
                return df[col]
        return None

def mostrar_detalle_clasificadores(df_filtrado, generica_seleccionada, tipo_clasificador):
    """
    Muestra un detalle desglosado de los clasificadores para una genérica específica
    """
    if not generica_seleccionada or generica_seleccionada == "TOTAL":
        return None
    
    # Filtrar datos por la genérica seleccionada
    df_gen = df_filtrado[df_filtrado["generica"] == generica_seleccionada]
    
    if df_gen.empty:
        st.warning(f"No hay datos para la genérica: {generica_seleccionada}")
        return None
    
    # Obtener la columna del clasificador
    columna_clasificador = obtener_datos_clasificador(df_gen, tipo_clasificador)
    
    if columna_clasificador is None:
        st.info(f"No se pudo obtener el clasificador: {tipo_clasificador}")
        return None
    
    # Agrupar por el clasificador
    resumen = df_gen.groupby(columna_clasificador).agg({
        "PIM": "sum",
        "Devengado_Total": "sum",
        "Saldo": "sum"
    }).reset_index()
    
    # Renombrar la columna del clasificador
    resumen.rename(columns={columna_clasificador.name: "clasificador"}, inplace=True)
    
    # Limpiar valores nulos
    resumen = resumen.dropna(subset=["clasificador"])
    resumen = resumen[resumen["clasificador"] != "nan"]
    
    # Calcular porcentajes
    total_pim = resumen["PIM"].sum()
    resumen["%_PIM"] = (resumen["PIM"] / total_pim * 100).round(2)
    resumen["%_Ejecucion"] = (resumen["Devengado_Total"] / resumen["PIM"] * 100).round(2)
    
    # Ordenar por PIM de mayor a menor
    resumen = resumen.sort_values("PIM", ascending=False)
    
    # Mostrar top 15 (o menos si hay pocos)
    top_n = min(15, len(resumen))
    resumen_top = resumen.head(top_n)
    
    # Formatear para mostrar
    resumen_display = resumen_top.copy()
    resumen_display["PIM"] = resumen_display["PIM"].apply(lambda x: f"S/ {x:,.0f}")
    resumen_display["Devengado_Total"] = resumen_display["Devengado_Total"].apply(lambda x: f"S/ {x:,.0f}")
    resumen_display["Saldo"] = resumen_display["Saldo"].apply(lambda x: f"S/ {x:,.0f}")
    resumen_display["%_PIM"] = resumen_display["%_PIM"].apply(lambda x: f"{x}%")
    resumen_display["%_Ejecucion"] = resumen_display["%_Ejecucion"].apply(lambda x: f"{x}%")
    
    # Mostrar título
    st.markdown(f"### 📋 Detalle para: **{generica_seleccionada}**")
    st.markdown(f"**Tipo de clasificador:** {tipo_clasificador}")
    st.caption(f"Mostrando los {top_n} de {len(resumen)} clasificadores (ordenados por PIM de mayor a menor)")
    
    # Mostrar tabla
    st.dataframe(resumen_display, use_container_width=True)
    
    # Gráfico de barras (solo si hay suficientes datos)
    if len(resumen_top) > 1:
        # Acortar textos largos para el gráfico
        resumen_top["clasificador_corto"] = resumen_top["clasificador"].apply(
            lambda x: x[:50] + "..." if len(str(x)) > 50 else str(x)
        )
        
        fig = px.bar(
            resumen_top,
            x="clasificador_corto",
            y="PIM",
            title=f"Top {top_n} {tipo_clasificador} por PIM - {generica_seleccionada}",
            labels={"PIM": "Monto (Soles)", "clasificador_corto": "Clasificador"},
            text_auto='.2s'
        )
        fig.update_layout(height=450, xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    return resumen

def crear_tabla_resumen(df_filtrado):
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
    
    # Detectar tipos de clasificador disponibles
    with col2:
        posibles_clasificadores = detectar_columnas_clasificador(df_filtrado)
        
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
        with st.expander(f"📋 Ver detalle para {generica_seleccionada}", expanded=True):
            mostrar_detalle_clasificadores(
                df_filtrado, 
                generica_seleccionada, 
                clasificador_seleccionado
            )
    
    return resumen

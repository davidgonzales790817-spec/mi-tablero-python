import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from datetime import datetime
import re
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Tablero Presupuestal", layout="wide")

# Logo institucional
st.sidebar.image("https://www.ipen.gob.pe/templates/ipen/images/logo-ipen.png", width=250)

# Cargar archivo
st.sidebar.header("Cargar archivo Excel")
archivo = st.sidebar.file_uploader("Seleccionar archivo Excel", type=["xls", "xlsx"])

# Crear carpeta de respaldo
carpeta_respaldo = "Respaldo_Data"
os.makedirs(carpeta_respaldo, exist_ok=True)

if archivo:
    # Guardar archivo
    ruta_archivo = os.path.join(carpeta_respaldo, archivo.name)
    with open(ruta_archivo, "wb") as f:
        f.write(archivo.getbuffer())

    try:
        # Leer archivo Excel
        df = pd.read_excel(ruta_archivo)
        
        # Normalizar nombres de columnas
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # --- DETECCIÓN DE COLUMNAS OBLIGATORIAS ---
        
        # 1. Detectar columnas de devengado mensual
        columnas_devengado = []
        for col in df.columns:
            if re.search(r'mto_devenga_\d{2}|devengado|monto_devengado|mes_\d{2}', col, re.IGNORECASE):
                columnas_devengado.append(col)
        
        # Si no se encuentran, buscar columnas numéricas que podrían ser meses
        if len(columnas_devengado) < 12:
            cols_numericas = df.select_dtypes(include=[np.number]).columns.tolist()
            excluir = ['mto_pim', 'pim', 'mto_certificado', 'certificado', 
                      'mto_compro_anual', 'compromiso', 'total', 'año', 'ano']
            cols_candidatas = [c for c in cols_numericas if not any(e in c for e in excluir)]
            columnas_devengado = cols_candidatas[:12]
        
        if len(columnas_devengado) == 0:
            st.error("No se pudieron detectar columnas de devengado mensual")
            st.stop()
        
        # Renombrar columnas de devengado
        meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        
        for i, col in enumerate(columnas_devengado[:12]):
            df.rename(columns={col: f"Devengado_{meses[i]}"}, inplace=True)
        
        columnas_devengado = [f"Devengado_{mes}" for mes in meses[:len(columnas_devengado)]]
        
        # 2. Detectar columna PIM
        col_pim = None
        for col in df.columns:
            if 'pim' in col.lower() or ('presupuesto' in col.lower() and 'inicial' in col.lower()):
                col_pim = col
                break
        
        if col_pim is None:
            # Buscar por lógica de valores grandes
            cols_numericas = df.select_dtypes(include=[np.number]).columns
            for col in cols_numericas:
                if col not in columnas_devengado:
                    if df[col].mean() > df[columnas_devengado].mean().mean() * 1.5:
                        col_pim = col
                        break
        
        if col_pim is None:
            st.error("No se pudo detectar la columna PIM")
            st.stop()
        
        df.rename(columns={col_pim: "PIM"}, inplace=True)
        
        # 3. Detectar columna Certificado
        col_cert = None
        for col in df.columns:
            if 'certificado' in col.lower():
                col_cert = col
                break
        
        if col_cert:
            df.rename(columns={col_cert: "Certificado"}, inplace=True)
        else:
            df["Certificado"] = 0
        
        # 4. Detectar columna Compromiso Anual
        col_comp = None
        for col in df.columns:
            if 'compro_anual' in col.lower() or 'compromiso' in col.lower():
                col_comp = col
                break
        
        if col_comp:
            df.rename(columns={col_comp: "Compromiso_Anual"}, inplace=True)
        else:
            df["Compromiso_Anual"] = 0
        
        # 5. Detectar columna de genérica
        col_generica = None
        for col in df.columns:
            if re.search(r'generica?|gen[eé]rica?', col, re.IGNORECASE):
                col_generica = col
                break
        
        if col_generica:
            df.rename(columns={col_generica: "generica"}, inplace=True)
            st.sidebar.success(f"Columna de genérica detectada: '{col_generica}'")
        else:
            df["generica"] = "General"
            st.sidebar.info("No se encontró columna de genérica. Se usará 'General'.")
        
        # Calcular métricas
        df["Devengado_Total"] = df[columnas_devengado].sum(axis=1)
        df["Saldo"] = df["PIM"] - df["Devengado_Total"]
        df["%_Ejecucion"] = (df["Devengado_Total"] / df["PIM"] * 100).round(2)
        
        # Filtrar datos no válidos
        df = df[df["generica"].notna()]
        df = df[df["PIM"] > 0]  # Solo considerar registros con presupuesto
        
        # Información general
        fecha_formateada = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        pliego = df.get("pliego", pd.Series(["No especificado"])).iloc[0] if "pliego" in df.columns else "No especificado"
        ano_eje = df.get("ano_eje", pd.Series(["No disponible"])).iloc[0] if "ano_eje" in df.columns else "No disponible"
        
        st.title("📊 Tablero Presupuestal Interactivo")
        st.markdown(f"""
        **Entidad:** `{pliego}`  
        **Año Fiscal:** `{ano_eje}`  
        **Última actualización:** `{fecha_formateada}`  
        **Registros cargados:** `{len(df)}`
        """)
        
        # --- FILTROS ---
        st.sidebar.header("Filtros")
        
        # Filtro de genérica
        genericas = ["Todas"] + sorted(df["generica"].unique().tolist())
        filtro_generica = st.sidebar.selectbox("Filtrar por Genérica", genericas)
        
        df_filtrado = df.copy()
        if filtro_generica != "Todas":
            df_filtrado = df_filtrado[df_filtrado["generica"] == filtro_generica]
        
        if df_filtrado.empty:
            st.warning("No hay datos para los filtros seleccionados")
            st.stop()
        
        # Filtro de unidad ejecutora (si existe)
        if "unidad_ejecutora" in df.columns:
            ues = ["Todas"] + sorted(df["unidad_ejecutora"].dropna().unique())
            filtro_ue = st.sidebar.selectbox("Filtrar por Unidad Ejecutora", ues)
            if filtro_ue != "Todas":
                df_filtrado = df_filtrado[df_filtrado["unidad_ejecutora"] == filtro_ue]
        
        # --- CÁLCULO DE TOTALES PARA GAUGES ---
        pim_total = df_filtrado["PIM"].sum()
        certificado_total = df_filtrado["Certificado"].sum() if "Certificado" in df_filtrado.columns else 0
        compromiso_total = df_filtrado["Compromiso_Anual"].sum() if "Compromiso_Anual" in df_filtrado.columns else 0
        devengado_total = df_filtrado["Devengado_Total"].sum()
        
        # --- GRÁFICOS GAUGE (RELOJES) ---
        st.subheader("Indicadores de Ejecución Presupuestal")
        
        def crear_gauge(valor, total, titulo, color):
            porcentaje = round(valor / total * 100 if total > 0 else 0, 2)
            return go.Indicator(
                mode="gauge+number",
                value=porcentaje,
                number={"suffix": "%", "font": {"size": 24}},
                title={"text": f"<b>{titulo}</b><br><span style='font-size:0.8em'>S/ {valor:,.0f}</span>", 
                       "font": {"size": 16}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "darkgray"},
                    "bar": {"color": color},
                    "bgcolor": "white",
                    "borderwidth": 1,
                    "bordercolor": "gray",
                    "steps": [
                        {"range": [0, 50], "color": "#f2f2f2"},
                        {"range": [50, 80], "color": "#d9ead3"},
                        {"range": [80, 100], "color": "#b6d7a8"},
                    ]
                }
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            fig_cert = go.Figure(crear_gauge(certificado_total, pim_total, "% Certificado", "#1f77b4"))
            fig_cert.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30))
            st.plotly_chart(fig_cert, use_container_width=True)
        with col2:
            fig_comp = go.Figure(crear_gauge(compromiso_total, pim_total, "% Compromiso", "#ff7f0e"))
            fig_comp.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30))
            st.plotly_chart(fig_comp, use_container_width=True)
        with col3:
            fig_dev = go.Figure(crear_gauge(devengado_total, pim_total, "% Devengado", "#2ca02c"))
            fig_dev.update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30))
            st.plotly_chart(fig_dev, use_container_width=True)
        
        # --- TABLA RESUMEN POR GENÉRICA ---
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
        
        # Ordenar por nombre de genérica (para que aparezcan en orden)
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
        
        # --- GRÁFICO DE EVOLUCIÓN MENSUAL (CORREGIDO Y ORDENADO) ---
        st.subheader("📈 Evolución del Devengado Mensual por Genérica")
        
        # Preparar datos para el gráfico
        datos_grafico = []
        
        # Obtener lista ordenada de genéricas (Genérica 1, Genérica 2, ...)
        genericas_ordenadas = sorted(df_filtrado["generica"].unique())
        
        for generica in genericas_ordenadas:
            df_gen = df_filtrado[df_filtrado["generica"] == generica]
            for mes in columnas_devengado:
                monto = df_gen[mes].sum()
                if monto > 0:  # Solo incluir montos positivos
                    datos_grafico.append({
                        "generica": generica,
                        "mes": mes.replace("Devengado_", ""),
                        "monto": monto
                    })
        
        df_grafico = pd.DataFrame(datos_grafico)
        
        if df_grafico.empty:
            st.warning("No hay datos para mostrar en el gráfico")
        else:
            # Ordenar meses cronológicamente
            df_grafico["mes"] = pd.Categorical(
                df_grafico["mes"], 
                categories=meses, 
                ordered=True
            )
            df_grafico = df_grafico.sort_values(["mes", "generica"])
            
            # Calcular totales por mes
            totales_mes = df_grafico.groupby("mes")["monto"].sum().reset_index()
            
            # Determinar escala automática
            max_monto = df_grafico["monto"].max()
            if max_monto > 1e6:
                df_grafico["monto_mostrar"] = df_grafico["monto"] / 1e6
                unidad = "Millones S/"
                formato_total = lambda x: f"S/ {x/1e6:.2f}M"
            elif max_monto > 1e3:
                df_grafico["monto_mostrar"] = df_grafico["monto"] / 1e3
                unidad = "Miles S/"
                formato_total = lambda x: f"S/ {x/1e3:.1f}K"
            else:
                df_grafico["monto_mostrar"] = df_grafico["monto"]
                unidad = "Soles"
                formato_total = lambda x: f"S/ {x:,.0f}"
            
            # Crear gráfico con orden específico de genéricas
            fig = go.Figure()
            
            # Colores para cada genérica
            colores = px.colors.qualitative.Set2
            
            # Agregar barras en el orden de las genéricas (la primera aparecerá abajo)
            for i, generica in enumerate(genericas_ordenadas):
                df_gen = df_grafico[df_grafico["generica"] == generica]
                if not df_gen.empty:
                    fig.add_trace(go.Bar(
                        name=generica,
                        x=df_gen["mes"],
                        y=df_gen["monto_mostrar"],
                        text=df_gen["monto"].apply(lambda x: f"S/ {x:,.0f}"),
                        textposition='inside',
                        textfont_size=10,
                        marker_color=colores[i % len(colores)],
                        hovertemplate="<b>%{x}</b><br>" +
                                    f"Genérica: {generica}<br>" +
                                    "Monto: S/ %{customdata:,.0f}<br>" +
                                    "<extra></extra>",
                        customdata=df_gen["monto"].values,
                        legendrank=i  # Controla el orden en la leyenda
                    ))
            
            # Configurar layout
            fig.update_layout(
                barmode='stack',
                title="Evolución Mensual del Gasto por Genérica",
                xaxis_title="Mes",
                yaxis_title=unidad,
                hovermode='x unified',
                legend_title="Genérica",
                showlegend=True,
                height=500,
                legend=dict(
                    orientation="h",  # Leyenda horizontal
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Agregar anotaciones de totales
            for i, row in totales_mes.iterrows():
                mes = row["mes"]
                total = row["monto"]
                
                # Calcular posición Y para la anotación
                if max_monto > 1e6:
                    y_pos = total / 1e6
                elif max_monto > 1e3:
                    y_pos = total / 1e3
                else:
                    y_pos = total
                
                fig.add_annotation(
                    x=mes,
                    y=y_pos,
                    text=f"<b>{formato_total(total)}</b>",
                    showarrow=False,
                    yshift=15,
                    font=dict(size=11, color="black", family="Arial Black"),
                    bgcolor="rgba(255, 255, 255, 0.9)",
                    bordercolor="black",
                    borderwidth=1,
                    borderpad=4
                )
            
            # Mejorar ejes
            fig.update_xaxes(tickangle=45, gridcolor='lightgray')
            fig.update_yaxes(gridcolor='lightgray')
            
            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar datos detallados
            with st.expander("Ver datos detallados"):
                # Tabla pivotada
                pivot_df = df_grafico.pivot_table(
                    values='monto',
                    index='generica',
                    columns='mes',
                    aggfunc='sum',
                    fill_value=0
                )
                
                # Ordenar filas por nombre de genérica
                pivot_df = pivot_df.reindex(genericas_ordenadas)
                
                # Formatear
                pivot_display = pivot_df.copy()
                for col in pivot_display.columns:
                    pivot_display[col] = pivot_display[col].apply(lambda x: f"S/ {x:,.0f}")
                
                st.dataframe(pivot_display, use_container_width=True)
                
                # Botón de descarga
                csv = df_grafico[["generica", "mes", "monto"]].to_csv(index=False)
                st.download_button(
                    "📥 Descargar datos CSV",
                    csv,
                    "evolucion_mensual.csv",
                    "text/csv"
                )
    
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        st.exception(e)
else:
    st.info("👈 Por favor, cargue un archivo Excel válido para comenzar.")
